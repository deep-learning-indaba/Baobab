"""Synchronous single-document generation (design section 8.1).

Self-service requests and admin one-offs run in the request: a handful of
Google API calls, a few seconds. Bulk generation (a job + worker draining a
queue of GeneratedDocument rows) is section 8.2 of the design and is not part
of this phase - everything here handles exactly one recipient.
"""
import os
import tempfile
import uuid

from app import db, LOGGER
from app.utils import storage, emailer
from config import GCP_DOCS_WORKING_FOLDER_ID

from app.documents.models import GeneratedDocument, GeneratedDocumentStatus
from app.documents.resolver import PlaceholderResolver, evaluate_form_requirements
from app.documents.variant_selection import select_variant, is_eligible, NoMatchingVariant
from app.documents.eligibility import build_eligibility_context
from app.documents.google_client import build_default_client, GoogleApiError


class GenerationError(Exception):
    """Anything that stops a generation request short of producing a PDF.

    Callers (the API layer) turn `code` into an HTTP error response; `details`
    carries whatever structured data the frontend needs to explain the
    failure (which forms are unmet, which placeholders failed, etc).
    """

    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def generate_document(document_template, user, requested_by_user, event,
                       language='en', client=None, override_eligibility=False):
    """Generate one document for `user` and return the GeneratedDocument row.

    Raises GenerationError - never a bare exception - for every expected
    failure mode: ineligible, no variant matches this person's tags, a
    required linked form hasn't been submitted, or a placeholder couldn't be
    resolved. `client` is injectable for tests; production callers leave it
    None and get the real Google client.
    """
    context = build_eligibility_context(user.id, event.id)

    if not override_eligibility and not is_eligible(document_template, context):
        raise GenerationError(
            'NOT_ELIGIBLE', 'This person is not eligible for this document.')

    blockers, _prompts = evaluate_form_requirements(document_template, user, language)
    if blockers:
        raise GenerationError(
            'REQUIRED_FORM_NOT_SUBMITTED',
            'A form required for this document has not been submitted.',
            {'blockers': blockers},
        )

    try:
        variant = select_variant(document_template, context, language)
    except NoMatchingVariant as e:
        raise GenerationError('NO_MATCHING_VARIANT', str(e))

    resolver = PlaceholderResolver(document_template, event, language)
    resolution = resolver.resolve(user, variant=variant)
    if not resolution.ok:
        raise GenerationError(
            'PLACEHOLDER_RESOLUTION_FAILED',
            'Some placeholders on this document could not be resolved for this person.',
            {'errors': [e.to_dict() for e in resolution.errors]},
        )

    client = client or build_default_client(working_folder_id=GCP_DOCS_WORKING_FOLDER_ID)

    generated_document = GeneratedDocument(
        event_id=event.id,
        document_template_id=document_template.id,
        user_id=user.id,
        requested_by_user_id=requested_by_user.id,
        variant_id=variant.id,
        status=GeneratedDocumentStatus.GENERATING,
    )
    db.session.add(generated_document)
    db.session.flush()

    try:
        pdf_bytes = client.generate_pdf(
            variant.google_file_id, variant.google_file_type, resolution.values)
    except GoogleApiError as e:
        generated_document.mark_failed('GOOGLE_API_ERROR', str(e))
        db.session.commit()
        raise GenerationError(
            'GOOGLE_API_ERROR', 'Could not generate the document. Please try again shortly.')

    filename = _render_filename(resolver, user, document_template)

    blob_name = f"documents/{event.id}/{document_template.id}/{uuid.uuid4().hex}.pdf"
    bucket = storage.get_storage_bucket()
    bucket.blob(blob_name).upload_from_string(pdf_bytes, content_type='application/pdf')

    generated_document.mark_generated(blob_name, filename, resolution.snapshot)
    db.session.commit()

    if document_template.delivery_mode in ('attachment', 'both'):
        _send_email(document_template, generated_document, user, pdf_bytes, filename)

    return generated_document


def _render_filename(resolver, user, document_template):
    default_name = f"{document_template.key}.pdf"
    if not document_template.filename_pattern:
        return default_name
    rendered = resolver.resolve_text(user, document_template.filename_pattern)
    if not rendered:
        return default_name
    return rendered if rendered.lower().endswith('.pdf') else f'{rendered}.pdf'


def _send_email(document_template, generated_document, user, pdf_bytes, filename):
    tmp_path = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4().hex}.pdf')
    with open(tmp_path, 'wb') as f:
        f.write(pdf_bytes)
    try:
        emailer.email_user(
            document_template.email_template_key or 'generated-document',
            event=generated_document.event,
            user=user,
            file_name=filename,
            file_path=tmp_path,
        )
    except ValueError:
        # No EmailTemplate row exists for this key/event/language. The document
        # is still generated and downloadable; only the email is skipped -
        # matching the legacy invitation letter generator's behaviour, and
        # deliberately not failing a request over a missing template.
        LOGGER.warning(
            'No email template "%s" found for generated document %s; not emailing.',
            document_template.email_template_key or 'generated-document',
            generated_document.id,
        )
    finally:
        os.remove(tmp_path)
