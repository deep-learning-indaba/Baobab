"""Editing email templates and layouts, at event level (event admins) and
organisation level (system admins).

Event routes:        /api/v1/events/<event_id>/email-types[...]
                     /api/v1/events/<event_id>/email-templates/<key>[...]
                     /api/v1/events/<event_id>/email-layout[...]
Organisation routes: the same under /api/v1/organisation/...

An event admin can only override event-scoped types for their own event.
Organisation-scoped types (password reset, email verification) go to every
user of the organisation and carry login links, so only system admins may
change them - otherwise an event admin could rewrite the whole user base's
password-reset email.
"""
from flask import g, request
import flask_restful as restful

from app import db
from app.documents.mixins import event_admin_required_from_path
from app.email_template import engine
from app.email_template.engine import EmailRenderError
from app.email_template.models import EmailLayout
from app.email_template.registry import (
    EMAIL_TYPES, UnknownEmailType, document_email_keys, get_email_type)
from app.email_template.repository import (
    BRAND_COLOUR_RE, EmailLayoutRepository, EmailTemplateRepository, Source, default_languages)
from app.email_template.service import queue_rendered, render_email, render_layout, sample_context
from app.email_template.translate import TranslationUnavailable, translate_template
from app.email_template.validation import check_template
from app.email_template.views import BuildContext, EventView, OrganisationView
from app.events.models import Event
from app.offer.models import Offer
from app.organisation.models import Organisation
from app.users.models import AppUser
from app.utils import errors
from app.utils.auth import admin_required


MAX_SUBJECT_LENGTH = 500
MAX_BODY_LENGTH = 100_000


def _error(message, status=400, **extra):
    body = {'message': message}
    body.update(extra)
    return body, status


def _render_error(e):
    return _error(e.message, 400, error=e.to_dict())


class _Scope:
    """Where an edit applies: one event, or the whole organisation."""

    def __init__(self, organisation, event=None):
        self.organisation = organisation
        self.event = event

    @property
    def event_id(self):
        return self.event.id if self.event is not None else None

    @property
    def level(self):
        return Source.EVENT if self.event is not None else Source.ORGANISATION

    def languages(self):
        if self.event is not None:
            return self.event.effective_languages
        return self.organisation.language_codes or ['en']

    def email_type(self, key):
        email_type = get_email_type(key, self.event_id)
        if self.event is not None and not email_type.is_event_scoped:
            raise UnknownEmailType(key)
        return email_type

    def keys(self):
        keys = [key for key, email_type in EMAIL_TYPES.items()
                if self.event is None or email_type.is_event_scoped]
        if self.event is not None:
            keys += sorted(document_email_keys(self.event.id))
        return keys


def _event_scope(event_id):
    event = db.session.query(Event).get(event_id)
    if event is None:
        return None
    return _Scope(event.organisation, event)


def _organisation_scope():
    # g.organisation is a cached PlainOrganisation; edits need the model.
    return _Scope(db.session.query(Organisation).get(g.organisation.id))


def _language(scope):
    language = (request.args.get('language') or (request.get_json(silent=True) or {}).get('language')
                or scope.languages()[0])
    return language[:2].lower()


def _ui_language():
    return (request.args.get('ui_language') or 'en')[:2]


# --------------------------------------------------------------------------- serialisers

def _type_summary(scope, email_type, ui_language):
    statuses = {}
    for language in scope.languages():
        resolved = EmailTemplateRepository.resolve(email_type, scope.organisation.id, scope.event, language)
        exact = resolved is not None and resolved.language == language
        statuses[language] = {
            'source': resolved.source if resolved else None,
            'language_fallback': not exact,
            'updated_at': resolved.updated_at.isoformat() + 'Z' if resolved and resolved.updated_at else None,
            'updated_by': resolved.updated_by if resolved else None,
        }
    return {
        'key': email_type.key,
        'name': email_type.name.get(ui_language) or email_type.name['en'],
        'description': email_type.description.get(ui_language) or email_type.description['en'],
        'group': email_type.group,
        'scope': email_type.scope,
        'sensitive': email_type.sensitive,
        'is_document_email': email_type.key not in EMAIL_TYPES,
        'languages': statuses,
    }


def _schema(email_type, ui_language):
    context = {}
    for context_name, view in email_type.full_context().items():
        entry = view.schema(ui_language)
        entry['nullable'] = email_type.nullable(context_name)
        entry['implicit'] = context_name in email_type.implicit_context()
        context[context_name] = entry
    name = email_type.name.get(ui_language) or email_type.name['en']
    description = email_type.description.get(ui_language) or email_type.description['en']
    return {'key': email_type.key, 'name': name, 'description': description, 'scope': email_type.scope,
            'sensitive': email_type.sensitive, 'context': context}


def _resolved_dict(resolved):
    if resolved is None:
        return None
    return {
        'subject': resolved.subject,
        'body': resolved.body,
        'source': resolved.source,
        'language': resolved.language,
        'updated_at': resolved.updated_at.isoformat() + 'Z' if resolved.updated_at else None,
        'updated_by': resolved.updated_by,
    }


# --------------------------------------------------------------------------- shared handlers

def _list_types(scope):
    ui_language = _ui_language()
    return [_type_summary(scope, get_email_type(key, scope.event_id), ui_language) for key in scope.keys()], 200


def _get_type(scope, key):
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    return _schema(email_type, _ui_language()), 200


def _get_template(scope, key):
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    language = _language(scope)
    own = EmailTemplateRepository.get_override(key, scope.organisation.id, scope.event_id, language)
    inherited = EmailTemplateRepository.resolve(email_type, scope.organisation.id, scope.event, language,
                                                below=scope.level)
    return {
        'key': key,
        'language': language,
        'languages': scope.languages(),
        'level': scope.level,
        'override': None if own is None else {
            'subject': own.subject,
            'body': own.body,
            'updated_at': own.updated_at.isoformat() + 'Z' if own.updated_at else None,
            'updated_by': own.updated_by.full_name if own.updated_by else None,
        },
        'inherited': _resolved_dict(inherited),
        'default_languages': default_languages(email_type.default_key),
        'language_sources': _language_sources(scope, email_type),
    }, 200


def _language_sources(scope, email_type):
    """{language: 'event' | 'organisation' | 'default'} - where each language's
    text comes from, so the editor can offer an already-customised one as the
    source for a translation. A language that only falls back to another is left out."""
    sources = {}
    for language in scope.languages():
        resolved = EmailTemplateRepository.resolve(email_type, scope.organisation.id, scope.event, language)
        if resolved is not None and resolved.language == language:
            sources[language] = resolved.source
    return sources


def _payload_text(body, field, limit):
    value = body.get(field)
    if not isinstance(value, str):
        return None
    return value[:limit + 1]


def _validate(email_type, scope, language, subject, body_source, overrides=None):
    """Raise EmailRenderError unless every path exists and the template renders
    against sample data."""
    views = email_type.full_context()
    check_template(subject, views, field='subject')
    check_template(body_source, views, field='body')
    values = sample_context(email_type, scope.organisation, scope.event, language, overrides)
    return render_email(email_type, values, scope.organisation, scope.event, language, template=None,
                        subject_source=subject, body_source=body_source, strict=True)


def _save_template(scope, key):
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    body = request.get_json(silent=True) or {}
    language = _language(scope)
    if language not in scope.languages():
        return _error('This event does not use the language "{}"'.format(language))
    subject = _payload_text(body, 'subject', MAX_SUBJECT_LENGTH)
    body_source = _payload_text(body, 'body', MAX_BODY_LENGTH)
    if not subject or not subject.strip() or body_source is None or not body_source.strip():
        return errors.MISSING_FIELDS
    if len(subject) > MAX_SUBJECT_LENGTH or len(body_source) > MAX_BODY_LENGTH:
        return _error('The template is too long')
    try:
        _validate(email_type, scope, language, subject, body_source)
    except EmailRenderError as e:
        return _render_error(e)
    EmailTemplateRepository.save(key, scope.organisation.id, scope.event_id, language, subject,
                                 body_source, g.current_user['id'])
    return _get_template(scope, key)


def _reset_template(scope, key):
    try:
        scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    EmailTemplateRepository.delete(key, scope.organisation.id, scope.event_id, _language(scope))
    return _get_template(scope, key)


def _revisions(scope, key):
    try:
        scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    revisions = EmailTemplateRepository.revisions(key, scope.organisation.id, scope.event_id, _language(scope))
    return [{
        'id': r.id,
        'subject': r.subject,
        'body': r.body,
        'saved_at': r.saved_at.isoformat() + 'Z',
        'saved_by': r.saved_by.full_name if r.saved_by else None,
    } for r in revisions], 200


def _translate(scope, key):
    """A machine translation of another language's current text into this one,
    for the editor to load unsaved - the admin reviews it before saving."""
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    body = request.get_json(silent=True) or {}
    target = _language(scope)
    source = (body.get('source_language') or '')[:2].lower()
    if source == target or source not in scope.languages() or target not in scope.languages():
        return _error('Choose a different language of this event to translate from')
    resolved = EmailTemplateRepository.resolve(email_type, scope.organisation.id, scope.event, source)
    if resolved is None or resolved.language != source:
        return _error('There is no text in that language to translate from')
    try:
        subject, kept_subject = translate_template(resolved.subject, source, target)
        translated_body, kept_body = translate_template(resolved.body, source, target)
    except TranslationUnavailable as e:
        return _error(str(e), 503)
    return {
        'subject': subject,
        'body': translated_body,
        'source_language': source,
        'untranslated_lines': kept_subject + kept_body,
    }, 200


def _preview_values(email_type, scope, language, body):
    """Sample data, optionally replaced by a real recipient and/or offer from
    this event so the admin can see exactly what one person would get."""
    overrides = body.get('sample_overrides') if isinstance(body.get('sample_overrides'), dict) else None
    values = sample_context(email_type, scope.organisation, scope.event, language, overrides)
    user_id = body.get('user_id')
    offer_id = body.get('offer_id')
    if scope.event is None or (not user_id and not offer_id):
        return values, None

    ctx = BuildContext(language, scope.organisation, scope.event)
    if offer_id and 'offer' in email_type.context:
        offer = db.session.query(Offer).filter_by(id=offer_id, event_id=scope.event.id).first()
        if offer is None:
            return None, errors.OFFER_NOT_FOUND
        values['offer'] = email_type.full_context()['offer'].build(offer, ctx)
        user_id = user_id or offer.user_id
    if user_id:
        user = db.session.query(AppUser).filter_by(id=user_id, organisation_id=scope.organisation.id).first()
        if user is None:
            return None, errors.USER_NOT_FOUND
        values['recipient'] = email_type.full_context()['recipient'].build(user, ctx)
    return values, None


def _preview(scope, key):
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    body = request.get_json(silent=True) or {}
    language = _language(scope)
    subject = _payload_text(body, 'subject', MAX_SUBJECT_LENGTH)
    body_source = _payload_text(body, 'body', MAX_BODY_LENGTH)
    if subject is None or body_source is None:
        return errors.MISSING_FIELDS
    values, error = _preview_values(email_type, scope, language, body)
    if error:
        return error
    try:
        check_template(subject, email_type.full_context(), field='subject')
        check_template(body_source, email_type.full_context(), field='body')
        rendered = render_email(email_type, values, scope.organisation, scope.event, language,
                                subject_source=subject, body_source=body_source, strict=True)
    except EmailRenderError as e:
        return _render_error(e)
    return {'subject': rendered.subject, 'html': rendered.body_html, 'text': rendered.body_text}, 200


def _test_send(scope, key):
    """Sends the (possibly unsaved) template to the signed-in admin - never to
    anyone else, so this can't be used to mail arbitrary addresses."""
    try:
        email_type = scope.email_type(key)
    except UnknownEmailType:
        return errors.EMAIL_TYPE_NOT_FOUND
    body = request.get_json(silent=True) or {}
    language = _language(scope)
    subject = _payload_text(body, 'subject', MAX_SUBJECT_LENGTH)
    body_source = _payload_text(body, 'body', MAX_BODY_LENGTH)
    if subject is None or body_source is None:
        return errors.MISSING_FIELDS
    admin = db.session.query(AppUser).get(g.current_user['id'])
    values = sample_context(email_type, scope.organisation, scope.event, language,
                            body.get('sample_overrides') if isinstance(body.get('sample_overrides'), dict) else None)
    values['recipient'] = email_type.full_context()['recipient'].build(
        admin, BuildContext(language, scope.organisation, scope.event))
    try:
        check_template(subject, email_type.full_context(), field='subject')
        check_template(body_source, email_type.full_context(), field='body')
        rendered = render_email(email_type, values, scope.organisation, scope.event, language,
                                subject_source=subject, body_source=body_source, strict=True)
    except EmailRenderError as e:
        return _render_error(e)
    rendered.subject = '[TEST] ' + rendered.subject
    queue_rendered(email_type, admin, scope.organisation, scope.event, rendered,
                   source=('email-test', None), send_now=True)
    return {'sent_to': admin.email}, 201


# --------------------------------------------------------------------------- layouts

def _layout_dict(layout):
    if layout is None:
        return None
    return {field: getattr(layout, field) for field in EmailLayout.EDITABLE_FIELDS}


def _get_layout(scope):
    language = _language(scope)
    own = EmailLayoutRepository.get(scope.organisation.id, scope.event_id, language)
    inherited = EmailLayoutRepository.resolve(scope.organisation.id, scope.event, language, below=scope.level)
    return {
        'language': language,
        'languages': scope.languages(),
        'level': scope.level,
        'layout': _layout_dict(own),
        'inherited': _layout_dict(inherited),
    }, 200


def _layout_values(scope, body):
    values = {}
    for field in EmailLayout.EDITABLE_FIELDS:
        if field not in body:
            continue
        value = body[field]
        if value is not None and not isinstance(value, str):
            raise EmailRenderError('{} must be text'.format(field), field=field)
        value = (value or '').strip() or None
        if field == 'brand_colour' and value and not BRAND_COLOUR_RE.match(value):
            raise EmailRenderError('Brand colour must look like #1a2b3c', field=field)
        if field == 'logo_url' and value:
            engine.check_url(value)
            if len(value) > 500:
                raise EmailRenderError('The logo link is too long', field=field)
        if field in ('header_markdown', 'footer_markdown') and value:
            if len(value) > 20_000:
                raise EmailRenderError('The text is too long', field=field)
            views = {'organisation': OrganisationView}
            if scope.event is not None:
                views['event'] = EventView
            check_template(value, views, field=field)
        values[field] = value
    return values


def _merged_layout(scope, language, values):
    """What this level's layout looks like with `values` (unsaved edits) on top
    of what is saved; a field cleared in `values` falls back to the inherited one."""
    layout = EmailLayoutRepository.resolve(scope.organisation.id, scope.event, language, below=scope.level)
    own = EmailLayoutRepository.get(scope.organisation.id, scope.event_id, language)
    for field in EmailLayout.EDITABLE_FIELDS:
        value = values[field] if field in values else (getattr(own, field) if own else None)
        if value:
            setattr(layout, field, value)
    return layout


def _save_layout(scope):
    body = request.get_json(silent=True) or {}
    language = _language(scope)
    try:
        values = _layout_values(scope, body)
        _layout_preview(scope, language, values)
    except EmailRenderError as e:
        return _render_error(e)
    EmailLayoutRepository.save(scope.organisation.id, scope.event_id, language, values, g.current_user['id'])
    return _get_layout(scope)


def _layout_preview(scope, language, values):
    layout = _merged_layout(scope, language, values)
    ctx = BuildContext(language, scope.organisation, scope.event)
    context = {'organisation': OrganisationView.build(scope.organisation, ctx)}
    if scope.event is not None:
        context['event'] = EventView.build(scope.event, ctx)
    body_html = engine.render_html_fragment(
        'This is where the email\'s own text goes.\n\n{% button "Example button", "https://example.org" %}',
        context, language, layout.brand_colour, strict=True)
    return render_layout(scope.organisation, scope.event, language, 'Example email', body_html,
                         "This is where the email's own text goes.", context, layout, strict=True)


def _preview_layout(scope):
    body = request.get_json(silent=True) or {}
    language = _language(scope)
    try:
        html, text = _layout_preview(scope, language, _layout_values(scope, body))
    except EmailRenderError as e:
        return _render_error(e)
    return {'html': html, 'text': text}, 200


# --------------------------------------------------------------------------- resources

def _with_event_scope(handler):
    def method(self, event_id, **kwargs):
        scope = _event_scope(event_id)
        if scope is None:
            return errors.EVENT_NOT_FOUND
        return handler(scope, **kwargs)
    return event_admin_required_from_path(method)


def _with_organisation_scope(handler):
    def method(self, **kwargs):
        return handler(_organisation_scope(), **kwargs)
    return admin_required(method)


class EventEmailTypeListAPI(restful.Resource):
    get = _with_event_scope(_list_types)


class EventEmailTypeAPI(restful.Resource):
    get = _with_event_scope(_get_type)


class EventEmailTemplateAPI(restful.Resource):
    get = _with_event_scope(_get_template)
    put = _with_event_scope(_save_template)
    delete = _with_event_scope(_reset_template)


class EventEmailTemplateRevisionsAPI(restful.Resource):
    get = _with_event_scope(_revisions)


class EventEmailTemplatePreviewAPI(restful.Resource):
    post = _with_event_scope(_preview)


class EventEmailTemplateTestSendAPI(restful.Resource):
    post = _with_event_scope(_test_send)


class EventEmailTemplateTranslateAPI(restful.Resource):
    post = _with_event_scope(_translate)


class EventEmailLayoutAPI(restful.Resource):
    get = _with_event_scope(_get_layout)
    put = _with_event_scope(_save_layout)


class EventEmailLayoutPreviewAPI(restful.Resource):
    post = _with_event_scope(_preview_layout)


class OrganisationEmailTypeListAPI(restful.Resource):
    get = _with_organisation_scope(_list_types)


class OrganisationEmailTypeAPI(restful.Resource):
    get = _with_organisation_scope(_get_type)


class OrganisationEmailTemplateAPI(restful.Resource):
    get = _with_organisation_scope(_get_template)
    put = _with_organisation_scope(_save_template)
    delete = _with_organisation_scope(_reset_template)


class OrganisationEmailTemplateRevisionsAPI(restful.Resource):
    get = _with_organisation_scope(_revisions)


class OrganisationEmailTemplatePreviewAPI(restful.Resource):
    post = _with_organisation_scope(_preview)


class OrganisationEmailTemplateTestSendAPI(restful.Resource):
    post = _with_organisation_scope(_test_send)


class OrganisationEmailTemplateTranslateAPI(restful.Resource):
    post = _with_organisation_scope(_translate)


class OrganisationEmailLayoutAPI(restful.Resource):
    get = _with_organisation_scope(_get_layout)
    put = _with_organisation_scope(_save_layout)


class OrganisationEmailLayoutPreviewAPI(restful.Resource):
    post = _with_organisation_scope(_preview_layout)
