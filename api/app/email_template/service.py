"""The one way to send an email.

    queue_email('offer', user, event=event, context={'offer': offer})

renders the email type's template for the recipient's language against view
models built from `context`, wraps it in the layout, and adds an OutboxMessage
to the current session. Nothing is committed and nothing is sent here: the
caller's commit makes the email and the change that caused it land together,
and the outbox worker delivers it. `send_now=True` is for an email the person
is sitting waiting for; it commits and delivers in the request, falling back
to the worker if delivery fails.

Rendering happens now rather than in the worker because the worker has no
organisation in scope, because a template error should reach the caller (and
the admin who wrote the template) rather than fail silently later, and because
the stored message is then exactly what was sent - the per-user history.
"""
import html
from datetime import datetime

from flask import g, has_app_context

from app import LOGGER, db
from app.email_template import engine
from app.email_template.engine import EmailRenderError
from app.email_template.registry import get_email_type
from app.email_template.repository import (
    EmailLayoutRepository, EmailTemplateRepository, load_layout_source)
from app.email_template.views import BuildContext, EventView, OrganisationView, Recipient, RecipientView
from app.organisation.models import Organisation
from app.outbox.models import OutboxChannel, OutboxMessage, OutboxStatus
from app.outbox.repository import OutboxRepository
from app.utils.emailer import resolve_sender
from app.utils.language import user_language_for_event


class Attachment:
    """A file already in GCS. `bucket` None means the default bucket."""

    def __init__(self, blob_name, filename, content_type='application/pdf', bucket=None):
        self.blob_name = blob_name
        self.filename = filename
        self.content_type = content_type
        self.bucket = bucket

    def to_dict(self):
        spec = {'blob_name': self.blob_name, 'filename': self.filename,
                'content_type': self.content_type}
        if self.bucket:
            spec['bucket'] = self.bucket
        return spec


#: Prefix for files uploaded only so the outbox can attach them. The bucket
#: should have a lifecycle rule deleting objects under it after a few weeks;
#: by then the message has been delivered or abandoned.
OUTBOX_ATTACHMENT_PREFIX = 'outbox-attachments/'


def upload_attachment(content, filename, content_type='application/pdf'):
    """Upload bytes for a single email's attachment and return the Attachment."""
    import uuid
    from app.utils import storage
    blob_name = '{}{}-{}'.format(OUTBOX_ATTACHMENT_PREFIX, uuid.uuid4().hex, filename)
    storage.get_storage_bucket().blob(blob_name).upload_from_string(content, content_type=content_type)
    return Attachment(blob_name, filename, content_type)


class RenderedEmail:
    def __init__(self, subject, body_html, body_text, template, language):
        self.subject = subject
        self.body_html = body_html
        self.body_text = body_text
        self.template = template
        self.language = language


class MissingContextError(ValueError):
    pass


def _is_user(recipient):
    return not isinstance(recipient, Recipient)


def recipient_language(recipient, event):
    if _is_user(recipient):
        return user_language_for_event(recipient, event)
    language = recipient.language or 'en'
    return event.resolve_language(language) if event is not None else language


def _organisation_for(recipient, event, organisation):
    if organisation is not None:
        return organisation
    if event is not None:
        return event.organisation
    # g.organisation is a cached PlainOrganisation, not the model; only its id
    # is used.
    organisation_id = None
    if has_app_context() and getattr(g, 'organisation', None) is not None:
        organisation_id = g.organisation.id
    elif _is_user(recipient):
        organisation_id = getattr(recipient, 'organisation_id', None)
    organisation = db.session.query(Organisation).get(organisation_id) if organisation_id else None
    if organisation is None:
        raise ValueError('Cannot send an email without an organisation')
    return organisation


def build_context(email_type, recipient, organisation, event, language, context):
    """View-model dicts for everything the type's template can use."""
    context = context or {}
    declared = set(email_type.context)
    supplied = set(context)
    if declared != supplied:
        raise MissingContextError('{} needs context {} but was given {}'.format(
            email_type.key, sorted(declared), sorted(supplied)))

    ctx = BuildContext(language, organisation, event)
    full = email_type.full_context()
    values = {
        'recipient': RecipientView.build(recipient, ctx),
        'organisation': full['organisation'].build(organisation, ctx),
    }
    if email_type.is_event_scoped:
        values['event'] = full['event'].build(event, ctx)
    for name in email_type.context:
        source = context[name]
        if source is None and not email_type.nullable(name):
            raise MissingContextError('{} needs a value for "{}"'.format(email_type.key, name))
        values[name] = full[name].build(source, ctx)
    return values


def sample_context(email_type, organisation, event, language, overrides=None):
    """Context built from each field's sample value - what the editor previews
    against when no real record is picked. `overrides` maps dotted paths to
    values, e.g. {'offer.payment_required': False, 'nominator': None}."""
    ctx = BuildContext(language, organisation, event)
    values = {}
    for name, view in email_type.full_context().items():
        if name == 'organisation' and organisation is not None:
            values[name] = view.build(organisation, ctx)
        elif name == 'event' and event is not None:
            values[name] = view.build(event, ctx)
        else:
            values[name] = view.sample(ctx)
    for path, value in (overrides or {}).items():
        _set_path(values, path, value)
    return values


def _set_path(values, path, value):
    parts = path.split('.')
    target = values
    for part in parts[:-1]:
        if not isinstance(target, dict) or not isinstance(target.get(part), dict):
            return
        target = target[part]
    if not isinstance(target, dict) or parts[-1] not in target:
        return
    current = target[parts[-1]]
    if isinstance(current, list) and isinstance(value, int) and not isinstance(value, bool):
        # A list length: keep that many sample items (0 shows the empty case).
        target[parts[-1]] = (current * (value // max(len(current), 1) + 1))[:value] if current else []
    else:
        target[parts[-1]] = value


def render_layout(organisation, event, language, subject, body_html, body_text, context,
                  layout=None, strict=False):
    layout = layout or EmailLayoutRepository.resolve(organisation.id, event, language)
    layout_context = {name: context[name] for name in ('organisation', 'event') if name in context}

    header_html = (engine.render_html_fragment(layout.header_markdown, layout_context, language,
                                               layout.brand_colour, strict, field='header')
                   if layout.header_markdown else '')
    footer_html = (engine.render_html_fragment(layout.footer_markdown, layout_context, language,
                                               layout.brand_colour, strict, field='footer')
                   if layout.footer_markdown else '')
    footer_text = (engine.render_text_fragment(layout.footer_markdown, layout_context, language, strict,
                                               field='footer')
                   if layout.footer_markdown else '')

    preheader = ' '.join(body_text.split())[:140]
    html_document = engine.render_liquid(
        load_layout_source(),
        {
            'language': language,
            'subject': subject,
            'preheader': preheader,
            'brand_colour': layout.brand_colour,
            'logo_url': layout.logo_url or '',
            'organisation_name': organisation.name,
            'header_html': engine.Markup(header_html),
            'body_html': engine.Markup(body_html),
            'footer_html': engine.Markup(footer_html),
        },
        engine.LAYOUT, language, field='layout')
    text = body_text if not footer_text else '{}\n\n--\n{}'.format(body_text, footer_text)
    return html_document, text


def render_email(email_type, values, organisation, event, language, template=None,
                 subject_source=None, body_source=None, strict=False, layout=None):
    """Render subject, HTML and text. `subject_source`/`body_source` replace
    the stored template (the editor's unsaved text)."""
    if template is None:
        template = EmailTemplateRepository.resolve(email_type, organisation.id, event, language)
        if template is None and (subject_source is None or body_source is None):
            raise EmailRenderError('No template exists for "{}"'.format(email_type.key))
    subject_source = template.subject if subject_source is None else subject_source
    body_source = template.body if body_source is None else body_source
    render_language = template.language if template is not None else language

    resolved_layout = layout or EmailLayoutRepository.resolve(organisation.id, event, language)
    subject = engine.render_subject(subject_source, values, render_language, strict)
    body_html = engine.render_html_fragment(body_source, values, render_language,
                                            resolved_layout.brand_colour, strict)
    body_text = engine.render_text_fragment(body_source, values, render_language, strict)
    html, text = render_layout(organisation, event, render_language, subject, body_html, body_text,
                               values, resolved_layout, strict)
    return RenderedEmail(subject, html, text, template, render_language)


def _message_dict(email_type, recipient, organisation, event, rendered, attachments, source,
                  idempotency_key, scheduled_at=None):
    sender_name, sender_email = resolve_sender(organisation.name, organisation.email_from)
    now = datetime.utcnow()
    source_type, source_id = source or (email_type.key, None)
    return {
        'organisation_id': organisation.id,
        'event_id': event.id if event is not None else None,
        'user_id': recipient.id if _is_user(recipient) else None,
        'channel': OutboxChannel.EMAIL,
        'recipient': recipient.email,
        'subject': rendered.subject,
        'body_text': rendered.body_text,
        'body_html': rendered.body_html,
        'payload': {'attachments': [a.to_dict() for a in attachments]} if attachments else None,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'reply_to': event.email_from if event is not None else None,
        'template_key': email_type.key,
        'template_revision_id': rendered.template.revision_id if rendered.template else None,
        'language': rendered.language,
        'sensitive': email_type.sensitive,
        'status': OutboxStatus.PENDING,
        'attempts': 0,
        'created_at': now,
        'scheduled_at': scheduled_at or now,
        'source_type': source_type,
        'source_id': source_id,
        'idempotency_key': idempotency_key,
    }


def queue_rendered(email_type, to, organisation, event, rendered, source=None, send_now=False):
    """Queue an already-rendered email (the editor's test send)."""
    row = OutboxMessage(**_message_dict(email_type, to, organisation, event, rendered, [], source, None))
    db.session.add(row)
    if send_now:
        db.session.commit()
        from app.outbox.sender import deliver_now
        deliver_now([row.id])
    return row


def prepare_email(key, to, event=None, context=None, attachments=(), source=None,
                  idempotency_key=None, organisation=None, language=None):
    """Render one email into an OutboxMessage column dict, without queueing it.
    `language` overrides the recipient's own (a document's delivery email is
    in the document's language)."""
    if to is None or not to.email:
        raise ValueError('Cannot email a recipient with no address')
    email_type = get_email_type(key, event.id if event is not None else None)
    if email_type.is_event_scoped and event is None:
        raise ValueError('"{}" is an event email and needs an event'.format(key))
    organisation = _organisation_for(to, event, organisation)
    language = language or recipient_language(to, event)
    values = build_context(email_type, to, organisation, event, language, context)
    rendered = render_email(email_type, values, organisation, event, language)
    return _message_dict(email_type, to, organisation, event, rendered, list(attachments), source,
                         idempotency_key)


def queue_email(key, to, event=None, context=None, attachments=(), source=None,
                idempotency_key=None, organisation=None, send_now=False):
    """Queue one email. Returns the OutboxMessage, or None if `idempotency_key`
    was already queued.

    `to` is an AppUser or a views.Recipient. Raises EmailRenderError when the
    template can't be rendered, and MissingContextError when `context` doesn't
    match what the type declares.

    send_now commits the session, then delivers in this request. Use it only
    where someone is waiting on the email (password reset, verification).
    """
    message = prepare_email(key, to, event, context, attachments, source, idempotency_key, organisation)
    if idempotency_key and OutboxRepository.existing_idempotency_keys([idempotency_key]):
        return None
    row = OutboxMessage(**message)
    db.session.add(row)
    if send_now:
        db.session.commit()
        from app.outbox.sender import deliver_now
        try:
            deliver_now([row.id])
        except Exception as e:  # noqa: BLE001 - the queued row is the fallback
            LOGGER.error('Immediate delivery of message %s failed; left for the worker: %s', row.id, e)
            db.session.rollback()
    return row


def queue_emails(key, items, event=None, source=None, organisation=None):
    """Queue the same email type for many recipients in one insert.

    `items` is an iterable of (recipient, context) or (recipient, context,
    idempotency_key). Recipients whose template fails to render are skipped and
    logged rather than failing the whole batch. Returns (queued, failed).
    """
    messages = []
    failed = []
    for item in items:
        recipient, context = item[0], item[1]
        idempotency_key = item[2] if len(item) > 2 else None
        try:
            messages.append(prepare_email(key, recipient, event, context, (), source, idempotency_key,
                                          organisation))
        except (EmailRenderError, ValueError) as e:
            LOGGER.error('Could not render "%s" for %s: %s', key, getattr(recipient, 'email', '?'), e)
            failed.append(recipient)
    queued = OutboxRepository.enqueue_many(messages)
    return queued, failed



def check_email_renders(key, event, language):
    """None if `key` renders for `event` in `language` against sample data, else
    the error message - a setup-time check, before any real recipient."""
    try:
        email_type = get_email_type(key, event.id if event is not None else None)
        organisation = (event.organisation if event is not None
                        else db.session.query(Organisation).get(g.organisation.id))
        values = sample_context(email_type, organisation, event, language)
        render_email(email_type, values, organisation, event, language)
    except (EmailRenderError, ValueError, KeyError) as e:
        return str(e)
    return None


def wrap_markdown(organisation, event, language, subject, heading, body_markdown):
    """(html, text) for admin-written Markdown that isn't a template - an
    announcement - in the same layout as every other email."""
    ctx = BuildContext(language, organisation, event)
    values = {'organisation': OrganisationView.build(organisation, ctx)}
    if event is not None:
        values['event'] = EventView.build(event, ctx)
    layout = EmailLayoutRepository.resolve(organisation.id, event, language)
    body_html = '<h2>{}</h2>{}'.format(html.escape(heading),
                                       engine.plain_markdown_to_html(body_markdown))
    body_text = '{}\n\n{}'.format(heading, engine.markdown_to_text(body_markdown))
    return render_layout(organisation, event, language, subject, body_html, body_text, values, layout)
