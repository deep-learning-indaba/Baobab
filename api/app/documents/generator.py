"""Single-document generation (design section 8.1) and the pipeline it shares
with bulk generation (section 8.2, app/documents/worker.py).

Self-service requests and admin one-offs run generate_document() in the
request: a handful of Google API calls, a few seconds. Bulk generation
pre-creates one `pending` GeneratedDocument row per recipient and has the
worker behind /api/v1/tasks/document-generation claim and run _process_row()
against each one - the exact same eligibility/blocker/variant/resolution/PDF
steps, just entered with a row that already exists instead of creating one.
"""
import uuid
from datetime import datetime

from app import db, LOGGER
from app.utils import storage
from app.utils.emailer import resolve_sender
from app.email_template.repository import EmailRepository
from app.outbox.models import OutboxChannel, OutboxStatus
from app.outbox.repository import OutboxRepository
from config import GCP_DOCS_WORKING_FOLDER_ID

from app.documents.models import GeneratedDocument, GeneratedDocumentStatus
from app.documents.resolver import PlaceholderResolver, evaluate_form_requirements, _AnswerIndex
from app.documents.variant_selection import select_variant, is_eligible, NoMatchingVariant
from app.documents.eligibility import build_eligibility_context
from app.documents.google_client import build_default_client, GoogleApiError

#: Outbox messages produced by this module are grouped under this source
#: type, e.g. source_id=generated_document.id - see app/outbox/models.py.
OUTBOX_SOURCE_TYPE = 'document'


class GenerationError(Exception):
    """Anything that stops a generation request short of producing a PDF.

    Callers (the API layer, and the bulk worker) turn `code` into an HTTP
    error response or a recorded failure respectively; `details` carries
    whatever structured data the frontend needs to explain the failure (which
    forms are unmet, which placeholders failed, etc). Never raised for a
    transport error (a Google API call itself failing) - that's recorded on
    the GeneratedDocument row instead, since a bulk run needs to continue past
    it rather than abort the whole request.
    """

    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def generate_document(document_template, user, requested_by_user, event,
                       language='en', client=None, override_eligibility=False):
    """Generate one document for `user` synchronously and return the
    GeneratedDocument row. Raises GenerationError - never a bare exception -
    for every expected failure mode short of a Google API error, which is
    recorded on the row and re-raised as GenerationError('GOOGLE_API_ERROR').
    """
    generated_document = GeneratedDocument(
        event_id=event.id, document_template_id=document_template.id, user_id=user.id,
        requested_by_user_id=requested_by_user.id, status=GeneratedDocumentStatus.GENERATING,
        language=language,
    )
    db.session.add(generated_document)
    db.session.flush()

    _process_row(generated_document, document_template, user, event, language,
                 client=client, override_eligibility=override_eligibility, retryable=False)
    return generated_document


def _process_row(generated_document, document_template, user, event, language,
                  client=None, override_eligibility=False, retryable=False):
    """Runs the full pipeline against an existing `pending`/`generating`
    GeneratedDocument row and always leaves it in a terminal state
    (`generated`, or `failed` - possibly bounced back to `pending` for a
    retryable transport failure with attempts left) before returning or
    raising GenerationError. The synchronous caller lets that propagate to
    the API layer; the bulk worker (worker.py) catches it, records the
    outcome on the job, and moves on to the next claimed row - either way,
    the row itself already carries the full error detail, which is what
    GeneratedDocumentListAPI shows admins.

    `retryable` controls whether a *transport* failure (a Google API error)
    goes back to `pending` for another attempt or straight to `failed` -
    see GeneratedDocument.mark_failed. A resolution/eligibility/blocker
    failure is never retried regardless of this flag: this person's data
    won't change before the next worker run, so retrying only delays
    reporting a real problem.
    """
    try:
        variant, pdf_bytes, filename, snapshot = _run_pipeline(
            generated_document, document_template, user, event, language,
            client, override_eligibility)
    except GenerationError as e:
        generated_document.mark_failed(e.code, e.message, retryable=(retryable and e.code == 'GOOGLE_API_ERROR'))
        db.session.commit()
        raise

    blob_name = f"documents/{event.id}/{document_template.id}/{uuid.uuid4().hex}.pdf"
    bucket = storage.get_storage_bucket()
    bucket.blob(blob_name).upload_from_string(pdf_bytes, content_type='application/pdf')

    generated_document.mark_generated(blob_name, filename, snapshot)
    db.session.commit()

    if document_template.delivery_mode != 'none':
        _enqueue_delivery_email(document_template, generated_document, user, event, filename, language)


def _run_pipeline(generated_document, document_template, user, event, language,
                   client, override_eligibility):
    """Eligibility -> blockers -> variant -> placeholder resolution -> PDF
    bytes. Raises GenerationError on the first failure; touches the row only
    to record which variant was selected, once that's known - _process_row
    (the only caller) owns marking failure/success on it."""
    resolver = PlaceholderResolver(document_template, event, language)
    answer_index = _AnswerIndex(user.id, resolver.form_links)
    eligibility_context = build_eligibility_context(
        user.id, event.id,
        answer_resolver=lambda key: resolver.answer_value(user, answer_index, key))

    if not override_eligibility and not is_eligible(document_template, eligibility_context):
        raise GenerationError('NOT_ELIGIBLE', 'This person is not eligible for this document.')

    blockers, _prompts = evaluate_form_requirements(document_template, user, language)
    if blockers:
        raise GenerationError(
            'REQUIRED_FORM_NOT_SUBMITTED',
            'A form required for this document has not been submitted.',
            {'blockers': blockers},
        )

    try:
        variant = select_variant(document_template, eligibility_context, language)
    except NoMatchingVariant as e:
        raise GenerationError('NO_MATCHING_VARIANT', str(e))

    generated_document.variant_id = variant.id

    resolution = resolver.resolve(user, variant=variant, answer_index=answer_index)
    if not resolution.ok:
        raise GenerationError(
            'PLACEHOLDER_RESOLUTION_FAILED',
            'Some placeholders on this document could not be resolved for this person.',
            {'errors': [e.to_dict() for e in resolution.errors]},
        )

    client = client or build_default_client(working_folder_id=GCP_DOCS_WORKING_FOLDER_ID)

    try:
        pdf_bytes = client.generate_pdf(
            variant.google_file_id, variant.google_file_type, resolution.values)
    except GoogleApiError as e:
        raise GenerationError(
            'GOOGLE_API_ERROR', 'Could not generate the document. Please try again shortly.')

    filename = _render_filename(resolver, user, document_template)
    return variant, pdf_bytes, filename, resolution.snapshot


def _render_filename(resolver, user, document_template):
    default_name = f"{document_template.key}.pdf"
    if not document_template.filename_pattern:
        return default_name
    rendered = resolver.resolve_text(user, document_template.filename_pattern)
    if not rendered:
        return default_name
    return rendered if rendered.lower().endswith('.pdf') else f'{rendered}.pdf'


def _enqueue_delivery_email(document_template, generated_document, user, event, filename, language):
    """Queue this document's delivery email through the outbox rather than
    sending it inline - the same worker that delivers announcement and push
    messages drains it, so a bulk run of hundreds never blocks on SMTP, and a
    single self-service request returns as soon as the PDF exists rather than
    waiting on a mail server round-trip too.

    A missing EmailTemplate is logged and skipped, not fatal: the document is
    still generated and downloadable, matching the legacy invitation letter
    generator's behaviour.
    """
    message = _build_delivery_message(document_template, generated_document, user, event, filename, language)
    if message is None:
        return
    OutboxRepository.enqueue_many([message], OUTBOX_SOURCE_TYPE, generated_document.id)
    db.session.commit()


def enqueue_resend(document_template, generated_document, user, event):
    """Admin-triggered resend of an already-generated document's delivery
    email (design section 9.7's results tab).

    Deliberately bypasses enqueue_many's per-source dedup: that dedup exists
    so the automatic delivery from generation never gets double-queued by an
    unrelated retry, but a resend is a deliberate repeat, not an accident -
    an admin who clicks it again after the first email bounced expects a new
    attempt, not silence.

    Returns False (nothing queued) only when there's no EmailTemplate to
    render from.
    """
    message = _build_delivery_message(
        document_template, generated_document, user, event,
        generated_document.filename, generated_document.language)
    if message is None:
        return False
    OutboxRepository.enqueue_many([message])
    db.session.commit()
    return True


def _build_delivery_message(document_template, generated_document, user, event, filename, language):
    """An OutboxMessage-shaped dict for this document's delivery email, or
    None when no EmailTemplate exists for this key/event/language."""
    email_template = EmailRepository.get(
        event.id, document_template.email_template_key or 'generated-document', language)
    if email_template is None:
        LOGGER.warning(
            'No email template "%s" found for generated document %s; not emailing.',
            document_template.email_template_key or 'generated-document', generated_document.id,
        )
        return None

    organisation = event.organisation
    sender_name, sender_email = resolve_sender(organisation.name, organisation.email_from)

    event_name = event.get_name(language) if event.has_specific_translation(language) else event.get_name('en')
    parameters = {
        'title': user.user_title or '', 'firstname': user.firstname, 'lastname': user.lastname,
        'event_name': event_name, 'document_name': _template_name(document_template, language),
    }
    subject = email_template.subject.format(**parameters)
    body_text = email_template.template.format(**parameters)

    payload = None
    if document_template.delivery_mode in ('attachment', 'both'):
        payload = {'attachment': {'blob_name': generated_document.storage_blob_name, 'filename': filename}}

    now = datetime.utcnow()
    return {
        'organisation_id': organisation.id,
        'event_id': event.id,
        'user_id': user.id,
        'channel': OutboxChannel.EMAIL,
        'recipient': user.email,
        'subject': subject,
        'body_text': body_text,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'payload': payload,
        'status': OutboxStatus.PENDING,
        'attempts': 0,
        'created_at': now,
        'scheduled_at': now,
        'source_type': OUTBOX_SOURCE_TYPE,
        'source_id': generated_document.id,
    }


def _template_name(document_template, language):
    translation = document_template.get_translation(language) or document_template.get_translation('en')
    return translation.name if translation else document_template.key
