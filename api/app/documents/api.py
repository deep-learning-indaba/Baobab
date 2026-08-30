import csv
import io
import tempfile
from datetime import datetime

import flask_restful as restful
from flask_restful import reqparse
from flask import g, request, send_file
from sqlalchemy import func

from app import db, LOGGER
from app.utils import errors, storage
from app.utils.auth import auth_required, event_admin_required, get_user_from_request
from app.users.repository import UserRepository as user_repository
from app.users.models import AppUser
from app.forms.models import Form
from app.events.models import Event


from app.documents.models import (
    DocumentTemplate, DocumentTemplateTranslation, DocumentTemplateVariant,
    DocumentTemplateForm, DocumentTemplateFormTranslation, UserEventData,
    GeneratedDocument, GeneratedDocumentStatus,
    DerivedPlaceholder, DerivedPlaceholderRule, DerivedPlaceholderRuleTranslation,
    DocumentGenerationJob,
)
from app.documents.mixins import document_admin_required, event_admin_required_from_path
from app.documents.google_client import (
    build_default_client, describe_configured_identity, extract_file_id, AccessStatus, GoogleApiError,
)
from app.documents.resolver import PlaceholderResolver, evaluate_form_requirements, _AnswerIndex
from app.documents.variant_selection import select_variant, is_eligible, NoMatchingVariant
from app.documents.eligibility import build_eligibility_context
from app.documents.generator import generate_document, GenerationError, enqueue_resend
from app.documents.derived_placeholders import find_cycle
from app.documents.recipients import resolve_recipient_user_ids
from app.documents.worker import run_bulk_generation
from app.outbox.api import is_scheduler_request


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def serialize_template(document_template, language='en'):
    translation = document_template.get_translation(language) or document_template.get_translation('en')
    return {
        'id': document_template.id,
        'event_id': document_template.event_id,
        'key': document_template.key,
        'is_active': document_template.is_active,
        'self_service': document_template.self_service,
        'eligibility_expression': document_template.eligibility_expression,
        'delivery_mode': document_template.delivery_mode,
        'email_template_key': document_template.email_template_key,
        'filename_pattern': document_template.filename_pattern,
        'allow_blank_values': document_template.allow_blank_values,
        'name': translation.name if translation else document_template.key,
        'description': translation.description if translation else None,
        'instructions': translation.instructions if translation else None,
        'translations': {
            t.language: {'name': t.name, 'description': t.description, 'instructions': t.instructions}
            for t in document_template.translations
        },
        'variants': [serialize_variant(v) for v in document_template.variants],
        'form_links': [serialize_form_link(link, language) for link in document_template.ordered_form_links()],
        'created_at': document_template.created_at.isoformat(),
        'updated_at': document_template.updated_at.isoformat(),
    }


def serialize_variant(variant):
    if variant is None:
        return None
    return {
        'id': variant.id,
        'name': variant.name,
        'google_file_id': variant.google_file_id,
        'google_file_type': variant.google_file_type,
        'google_file_name': variant.google_file_name,
        'language': variant.language,
        'selection_expression': variant.selection_expression,
        'priority': variant.priority,
        'is_active': variant.is_active,
        'detected_placeholders': variant.detected_placeholders,
        'access_status': variant.access_status,
        'access_checked_at': variant.access_checked_at.isoformat() if variant.access_checked_at else None,
    }


def serialize_form_link(link, language='en'):
    translation = link.get_translation(language) or link.get_translation('en')
    form_translation = link.form.get_translation(language) or link.form.get_translation('en')
    return {
        'id': link.id,
        'form_id': link.form_id,
        'form_name': form_translation.name if form_translation else None,
        'order': link.order,
        'requirement': link.requirement,
        'prompt_message': translation.prompt_message if translation else None,
        # Every language's message, not just the resolved one above - the
        # editor needs all of them at once to populate each language's field.
        'prompt_messages': {t.language: t.prompt_message for t in link.translations},
    }


def serialize_generated_document(generated_document):
    return {
        'id': generated_document.id,
        'document_template_id': generated_document.document_template_id,
        'variant_id': generated_document.variant_id,
        'user_id': generated_document.user_id,
        'job_id': generated_document.job_id,
        'language': generated_document.language,
        'status': generated_document.status,
        'filename': generated_document.filename,
        'error_code': generated_document.error_code,
        'error_detail': generated_document.error_detail,
        'attempts': generated_document.attempts,
        'created_at': generated_document.created_at.isoformat() if generated_document.created_at else None,
        'generated_at': generated_document.generated_at.isoformat() if generated_document.generated_at else None,
        'download_url': (
            f'/api/v1/documents/generated/{generated_document.id}/download'
            if generated_document.status == GeneratedDocumentStatus.GENERATED else None
        ),
    }


def serialize_job(job):
    return {
        'id': job.id,
        'document_template_id': job.document_template_id,
        'requested_by_user_id': job.requested_by_user_id,
        'language': job.language,
        'override_eligibility': job.override_eligibility,
        'recipient_selection': job.recipient_selection,
        'status': job.status,
        'total_count': job.total_count,
        'succeeded_count': job.succeeded_count,
        'failed_count': job.failed_count,
        'pending_count': job.total_count - job.succeeded_count - job.failed_count,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
    }


def serialize_derived_placeholder(derived_placeholder):
    return {
        'id': derived_placeholder.id,
        'key': derived_placeholder.key,
        'description': derived_placeholder.description,
        'is_active': derived_placeholder.is_active,
        'rules': [serialize_derived_rule(r) for r in
                  sorted(derived_placeholder.rules, key=lambda r: r.order)],
        'updated_at': derived_placeholder.updated_at.isoformat() if derived_placeholder.updated_at else None,
    }


def serialize_derived_rule(rule):
    return {
        'id': rule.id,
        'order': rule.order,
        'condition_expression': rule.condition_expression,
        'is_otherwise': rule.condition_expression is None,
        'texts': {t.language: t.text for t in rule.translations},
    }


def serialize_user_event_data(row):
    return {
        'id': row.id,
        'user_id': row.user_id,
        'key': row.key,
        'value': row.value,
        'updated_at': row.updated_at.isoformat(),
    }


def _generation_error_response(error):
    return {'message': error.message, 'code': error.code, 'details': error.details}, 422


def _identity_fields():
    """service_account_email / has_configured_service_account for the
    access-check remediation UI - see google_client.describe_configured_identity
    for why this can't just read GCP_CREDENTIALS_DICT directly."""
    email, is_configured = describe_configured_identity()
    return {'service_account_email': email, 'has_configured_service_account': is_configured}


def _scan_placeholders_safely(client, file_id, file_type):
    """(placeholders, None) on success, (None, error_response_tuple) otherwise.

    check_access only proves Drive can see the file's metadata - actually
    reading its body through the Docs/Slides API can still fail independently,
    most often because that specific API isn't enabled yet on the calling
    project (a 403 distinct from anything a Drive-level permission fixes).
    Left unguarded here, that exception reached Flask's debug-mode exception
    page instead of a normal response, which bypasses the app's CORS
    after_request hook entirely - the browser reports a bare "Network error"
    rather than the (usually self-explanatory) message Google sent back.
    """
    try:
        return sorted(client.scan_placeholders(file_id, file_type)), None
    except GoogleApiError as e:
        return None, ({'message': f'Could not read this document to detect its placeholders: {e}'}, 502)


# ---------------------------------------------------------------------------
# Admin: templates
# ---------------------------------------------------------------------------

class DocumentTemplateListAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        language = request.args.get('language', 'en')
        templates = (
            db.session.query(DocumentTemplate)
            .filter_by(event_id=event_id)
            .order_by(DocumentTemplate.id)
            .all()
        )
        return [serialize_template(t, language) for t in templates], 200

    @event_admin_required
    def post(self, event_id):
        data = request.get_json() or {}
        key = (data.get('key') or '').strip()
        if not key:
            return errors.MISSING_FIELDS

        existing = db.session.query(DocumentTemplate).filter_by(event_id=event_id, key=key).first()
        if existing:
            return errors.DOCUMENT_TEMPLATE_KEY_IN_USE

        user = get_user_from_request()
        document_template = DocumentTemplate(
            event_id=event_id,
            created_by_user_id=user['id'],
            key=key,
            self_service=bool(data.get('self_service', False)),
            eligibility_expression=data.get('eligibility_expression'),
            delivery_mode=data.get('delivery_mode', 'attachment'),
            email_template_key=data.get('email_template_key'),
            filename_pattern=data.get('filename_pattern'),
            allow_blank_values=bool(data.get('allow_blank_values', False)),
        )
        db.session.add(document_template)
        db.session.flush()

        translations = data.get('translations') or {'en': {'name': data.get('name') or key}}
        for language, t in translations.items():
            db.session.add(DocumentTemplateTranslation(
                document_template_id=document_template.id,
                language=language,
                name=t.get('name') or key,
                description=t.get('description'),
                instructions=t.get('instructions'),
            ))

        db.session.commit()
        return serialize_template(document_template), 201


class DocumentTemplateAPI(restful.Resource):

    @document_admin_required
    def get(self, document_template):
        language = request.args.get('language', 'en')
        return serialize_template(document_template, language), 200

    @document_admin_required
    def put(self, document_template):
        data = request.get_json() or {}

        if 'key' in data and data['key'] != document_template.key:
            existing = db.session.query(DocumentTemplate).filter_by(
                event_id=document_template.event_id, key=data['key']).first()
            if existing:
                return errors.DOCUMENT_TEMPLATE_KEY_IN_USE
            document_template.key = data['key']

        for field in ('self_service', 'eligibility_expression', 'delivery_mode',
                      'email_template_key', 'filename_pattern', 'allow_blank_values', 'is_active'):
            if field in data:
                setattr(document_template, field, data[field])
        document_template.updated_at = datetime.now()

        for language, t in (data.get('translations') or {}).items():
            translation = document_template.get_translation(language)
            if translation:
                translation.name = t.get('name', translation.name)
                translation.description = t.get('description', translation.description)
                translation.instructions = t.get('instructions', translation.instructions)
            else:
                db.session.add(DocumentTemplateTranslation(
                    document_template_id=document_template.id,
                    language=language,
                    name=t.get('name') or document_template.key,
                    description=t.get('description'),
                    instructions=t.get('instructions'),
                ))

        db.session.commit()
        return serialize_template(document_template), 200

    @document_admin_required
    def delete(self, document_template):
        db.session.delete(document_template)
        db.session.commit()
        return {}, 204


class DocumentTemplateVariantListAPI(restful.Resource):

    @document_admin_required
    def post(self, document_template):
        data = request.get_json() or {}
        file_id = extract_file_id(data.get('google_file_url') or data.get('google_file_id') or '')
        if not file_id:
            return errors.DOCUMENT_SOURCE_NOT_SPECIFIED

        client = build_default_client()
        access = client.check_access(file_id)
        if access.status != AccessStatus.OK:
            return {'access': {**access.to_dict(), **_identity_fields()}}, 422

        placeholders, scan_error = _scan_placeholders_safely(client, file_id, access.file_type)
        if scan_error:
            return scan_error

        variant = DocumentTemplateVariant(
            document_template_id=document_template.id,
            name=data.get('name') or access.file_name or 'Untitled',
            google_file_id=file_id,
            google_file_type=access.file_type,
            google_file_name=access.file_name,
            language=data.get('language'),
            selection_expression=data.get('selection_expression'),
            priority=int(data.get('priority', 0)),
        )
        variant.detected_placeholders = placeholders
        variant.access_status = access.status
        variant.access_checked_at = datetime.now()
        db.session.add(variant)
        db.session.commit()
        return serialize_variant(variant), 201


class DocumentTemplateVariantAPI(restful.Resource):

    @document_admin_required
    def put(self, document_template, variant_id):
        variant = next((v for v in document_template.variants if v.id == variant_id), None)
        if not variant:
            return errors.DOCUMENT_VARIANT_NOT_FOUND

        data = request.get_json() or {}
        for field in ('name', 'language', 'selection_expression', 'priority', 'is_active'):
            if field in data:
                setattr(variant, field, data[field])
        variant.updated_at = datetime.now()
        db.session.commit()
        return serialize_variant(variant), 200

    @document_admin_required
    def delete(self, document_template, variant_id):
        variant = next((v for v in document_template.variants if v.id == variant_id), None)
        if not variant:
            return errors.DOCUMENT_VARIANT_NOT_FOUND
        db.session.delete(variant)
        db.session.commit()
        return {}, 204


class DocumentTemplateFormsAPI(restful.Resource):
    """Replaces the whole ordered list of linked forms in one call, matching
    the admin UI: forms are dragged into order and (un)linked on one screen,
    so there is no meaningful "add one" vs "reorder" distinction to preserve
    across requests."""

    @document_admin_required
    def put(self, document_template):
        data = request.get_json() or {}
        links_data = data.get('form_links') or []

        for link in list(document_template.form_links):
            db.session.delete(link)
        db.session.flush()

        for index, entry in enumerate(links_data):
            form_id = entry.get('form_id')
            form = db.session.query(Form).filter_by(
                id=form_id, event_id=document_template.event_id).first()
            if not form:
                db.session.rollback()
                return errors.FORM_NOT_FOUND

            link = DocumentTemplateForm(
                document_template_id=document_template.id,
                form_id=form_id,
                order=entry.get('order', len(links_data) - index),
                requirement=entry.get('requirement', DocumentTemplateForm.REQUIREMENT_NONE),
            )
            db.session.add(link)
            db.session.flush()

            for language, message in (entry.get('prompt_messages') or {}).items():
                if message:
                    db.session.add(DocumentTemplateFormTranslation(
                        document_template_form_id=link.id, language=language, prompt_message=message))

        db.session.commit()
        return serialize_template(document_template), 200


class DocumentValidateSourceAPI(restful.Resource):
    """Checks whether Baobab can access a pasted Google Docs/Slides link,
    before it is attached to any template - design section 6.2. Event-scoped
    rather than template-scoped so it can be used while creating a brand new
    template's first variant."""

    @event_admin_required
    def post(self, event_id):
        data = request.get_json() or {}
        file_id = extract_file_id(data.get('url') or '')
        if not file_id:
            return errors.DOCUMENT_SOURCE_NOT_SPECIFIED

        client = build_default_client()
        access = client.check_access(file_id)
        response = {**access.to_dict(), **_identity_fields()}
        if access.status == AccessStatus.OK:
            placeholders, scan_error = _scan_placeholders_safely(client, file_id, access.file_type)
            if scan_error:
                return scan_error
            response['detected_placeholders'] = placeholders
        return response, 200


class DocumentTemplateAnalyseAPI(restful.Resource):
    """Rescans every active variant and reports, for the union of placeholders
    found, whether each resolves and which linked forms would be tried -
    design section 9.5. Independent of any one recipient; see
    DocumentTemplatePreviewAPI for a specific person's resolved values."""

    @document_admin_required
    def post(self, document_template):
        client = build_default_client()
        for variant in document_template.variants:
            if not variant.is_active:
                continue
            access = client.check_access(variant.google_file_id)
            variant.access_status = access.status
            variant.access_checked_at = datetime.now()
            if access.status == AccessStatus.OK:
                placeholders, scan_error = _scan_placeholders_safely(
                    client, variant.google_file_id, access.file_type)
                if scan_error:
                    # One variant's Docs/Slides API failure (e.g. the API isn't
                    # enabled on this project) shouldn't abort rescanning every
                    # other variant - degrade this one to an error state and
                    # keep going, rather than losing the whole batch.
                    LOGGER.warning(
                        'Placeholder scan failed for variant %s (%s): %s',
                        variant.id, variant.google_file_id, scan_error[0]['message'])
                    variant.access_status = AccessStatus.ERROR
                    continue
                variant.detected_placeholders = placeholders
                variant.google_file_name = access.file_name
        db.session.commit()

        resolver = PlaceholderResolver(document_template, document_template.event)
        return {
            'variants': [serialize_variant(v) for v in document_template.variants],
            'placeholders': resolver.describe_placeholders(),
        }, 200


class DocumentTemplatePreviewAPI(restful.Resource):
    """Dry-run resolution for one real person - the "Test with a real person"
    control in design section 9.5. Nothing is generated, stored, or emailed."""

    @document_admin_required
    def post(self, document_template):
        data = request.get_json() or {}
        target_user_id = data.get('user_id')
        language = data.get('language', 'en')
        if not target_user_id:
            return errors.MISSING_FIELDS

        target_user = db.session.query(AppUser).filter_by(id=target_user_id).first()
        if not target_user:
            return errors.USER_NOT_FOUND

        resolver = PlaceholderResolver(document_template, document_template.event, language)
        answer_index = _AnswerIndex(target_user.id, resolver.form_links)
        context = build_eligibility_context(
            target_user.id, document_template.event_id,
            answer_resolver=lambda key: resolver.answer_value(target_user, answer_index, key))
        eligible = is_eligible(document_template, context)

        variant = None
        variant_error = None
        if eligible:
            try:
                variant = select_variant(document_template, context, language)
            except NoMatchingVariant as e:
                variant_error = str(e)

        blockers, prompts = evaluate_form_requirements(document_template, target_user, language)

        resolution_payload = None
        if variant:
            resolution = resolver.resolve(target_user, variant=variant, answer_index=answer_index)
            resolution_payload = {
                'values': resolution.snapshot,
                'errors': [e.to_dict() for e in resolution.errors],
            }

        return {
            'eligible': eligible,
            'variant': serialize_variant(variant),
            'variant_error': variant_error,
            'blockers': blockers,
            'prompts': prompts,
            'resolution': resolution_payload,
        }, 200


class DocumentGenerateAPI(restful.Resource):
    """Admin-triggered single-recipient generation. See
    DocumentTemplateBulkGenerateAPI for the many-recipients version (design
    section 8.2)."""

    @auth_required
    def post(self):
        data = request.get_json() or {}
        template_id = data.get('template_id')
        target_user_id = data.get('user_id')
        language = data.get('language', 'en')
        override_eligibility = bool(data.get('override_eligibility', False))

        document_template = db.session.query(DocumentTemplate).filter_by(id=template_id).first()
        if not document_template:
            return errors.DOCUMENT_TEMPLATE_NOT_FOUND

        requester = user_repository.get_by_id(g.current_user['id'])
        if not requester or not requester.is_event_admin(document_template.event_id):
            return errors.FORBIDDEN

        target_user = db.session.query(AppUser).filter_by(id=target_user_id).first()
        if not target_user:
            return errors.USER_NOT_FOUND

        try:
            generated_document = generate_document(
                document_template, target_user, requester, document_template.event,
                language=language, override_eligibility=override_eligibility,
            )
        except GenerationError as e:
            return _generation_error_response(e)

        return serialize_generated_document(generated_document), 201


def _preflight_candidates(document_template, event, selection, language, override_eligibility):
    """The dry-run summary design section 9.7 shows before an admin commits
    to a bulk run: who's excluded as ineligible, who'll fail and why, who's
    merely nudged (a recommended-but-incomplete form, never a failure), and
    who's clear to generate.

    Runs the same eligibility/blocker/variant/resolution checks generation
    itself will do, without calling Google or writing anything - so a
    misconfigured placeholder is caught for all 312 people before 298 emails
    go out, not after.
    """
    user_ids = resolve_recipient_user_ids(event, selection)
    users = (db.session.query(AppUser).filter(AppUser.id.in_(user_ids)).all()
             if user_ids else [])
    resolver = PlaceholderResolver(document_template, event, language)

    succeed_user_ids, failures = [], []
    excluded_ineligible = 0
    recommended_incomplete_user_ids = []

    for user in users:
        answer_index = _AnswerIndex(user.id, resolver.form_links)
        context = build_eligibility_context(
            user.id, event.id,
            answer_resolver=lambda key, u=user, ai=answer_index: resolver.answer_value(u, ai, key))

        if not override_eligibility and not is_eligible(document_template, context):
            excluded_ineligible += 1
            continue

        blockers, prompts = evaluate_form_requirements(document_template, user, language)
        if prompts:
            recommended_incomplete_user_ids.append(user.id)
        if blockers:
            failures.append({'user_id': user.id, 'reason': 'required_form_not_submitted', 'detail': blockers})
            continue

        try:
            variant = select_variant(document_template, context, language)
        except NoMatchingVariant as e:
            failures.append({'user_id': user.id, 'reason': 'no_matching_variant', 'detail': str(e)})
            continue

        resolution = resolver.resolve(user, variant=variant, answer_index=answer_index)
        if not resolution.ok:
            failures.append({
                'user_id': user.id, 'reason': 'placeholder_resolution_failed',
                'detail': [e.to_dict() for e in resolution.errors],
            })
            continue

        succeed_user_ids.append(user.id)

    return {
        'total_candidates': len(users),
        'excluded_ineligible_count': excluded_ineligible,
        'will_succeed_count': len(succeed_user_ids),
        'will_succeed_user_ids': succeed_user_ids,
        'will_fail_count': len(failures),
        'failures': failures,
        'recommended_incomplete_count': len(recommended_incomplete_user_ids),
        'recommended_incomplete_user_ids': recommended_incomplete_user_ids,
    }


class DocumentTemplatePreflightAPI(restful.Resource):
    """POST .../templates/<id>/generate/preflight - the dry run behind design
    section 9.7's "312 people selected... 298 will succeed" screen."""

    @document_admin_required
    def post(self, document_template):
        data = request.get_json() or {}
        selection = data.get('recipients') or {'type': 'everyone'}
        language = data.get('language', 'en')
        override_eligibility = bool(data.get('override_eligibility', False))

        result = _preflight_candidates(
            document_template, document_template.event, selection, language, override_eligibility)
        return result, 200


class DocumentTemplateBulkGenerateAPI(restful.Resource):
    """POST .../templates/<id>/generate/bulk - creates the job and one
    `pending` GeneratedDocument per recipient who preflight confirmed will
    succeed; the worker behind /api/v1/tasks/document-generation
    (app/documents/worker.py) drains them. Recipients preflight flagged as
    ineligible or blocked are never given a row - the admin already saw why
    on the preflight screen, and there's nothing to attempt for them."""

    @document_admin_required
    def post(self, document_template):
        data = request.get_json() or {}
        selection = data.get('recipients') or {'type': 'everyone'}
        language = data.get('language', 'en')
        override_eligibility = bool(data.get('override_eligibility', False))
        event = document_template.event
        requester = user_repository.get_by_id(g.current_user['id'])

        preflight = _preflight_candidates(document_template, event, selection, language, override_eligibility)
        recipient_user_ids = preflight['will_succeed_user_ids']
        if not recipient_user_ids:
            return errors.NO_RECIPIENTS_SELECTED

        job = DocumentGenerationJob(
            event_id=event.id, document_template_id=document_template.id,
            requested_by_user_id=requester.id, total_count=len(recipient_user_ids),
            language=language, override_eligibility=override_eligibility,
            recipient_selection=selection,
        )
        db.session.add(job)
        db.session.flush()

        now = datetime.now()
        rows = [{
            'event_id': event.id,
            'document_template_id': document_template.id,
            'variant_id': None,
            'user_id': user_id,
            'requested_by_user_id': requester.id,
            'job_id': job.id,
            'status': GeneratedDocumentStatus.PENDING,
            'language': language,
            'attempts': 0,
            'created_at': now,
        } for user_id in recipient_user_ids]
        db.session.bulk_insert_mappings(GeneratedDocument, rows)
        db.session.commit()

        return serialize_job(job), 201


class DocumentGenerationJobAPI(restful.Resource):
    """GET .../jobs/<id> - polled by the bulk-generate progress screen."""

    @auth_required
    def get(self, job_id):
        job = db.session.query(DocumentGenerationJob).filter_by(id=job_id).first()
        if not job:
            return errors.DOCUMENT_GENERATION_JOB_NOT_FOUND

        requester = user_repository.get_by_id(g.current_user['id'])
        if not requester or not requester.is_event_admin(job.event_id):
            return errors.FORBIDDEN

        return serialize_job(job), 200


class DocumentGenerationWorkerAPI(restful.Resource):
    """GET|POST /api/v1/tasks/document-generation - drains pending bulk
    generation rows. Driven every minute by App Engine cron (api/cron.yaml),
    guarded the same way as OutboxWorkerAPI (app/outbox/api.py): GET is what
    the scheduler actually sends, POST is accepted for a manual run."""

    def _run(self):
        if not is_scheduler_request():
            return errors.FORBIDDEN
        summary = run_bulk_generation()
        LOGGER.info('Document generation worker run complete: %s', summary)
        return summary, 200

    def get(self):
        return self._run()

    def post(self):
        return self._run()


class GeneratedDocumentResendAPI(restful.Resource):
    """POST .../generated/<id>/resend - re-queues the delivery email for an
    already-generated document (design section 9.7's results tab)."""

    @auth_required
    def post(self, document_id):
        generated_document = db.session.query(GeneratedDocument).filter_by(id=document_id).first()
        if not generated_document:
            return errors.GENERATED_DOCUMENT_NOT_FOUND

        requester = user_repository.get_by_id(g.current_user['id'])
        if not requester or not requester.is_event_admin(generated_document.event_id):
            return errors.FORBIDDEN
        if generated_document.status != GeneratedDocumentStatus.GENERATED:
            return errors.DOCUMENT_NOT_YET_GENERATED

        document_template = db.session.query(DocumentTemplate).filter_by(
            id=generated_document.document_template_id).first()
        target_user = db.session.query(AppUser).filter_by(id=generated_document.user_id).first()
        if not document_template or not target_user:
            return errors.GENERATED_DOCUMENT_NOT_FOUND
        if document_template.delivery_mode == 'none':
            return {'message': 'This document has no delivery configured - it is download-only.'}, 400

        queued = enqueue_resend(document_template, generated_document, target_user, document_template.event)
        if not queued:
            return {'message': 'No email template is configured for this document.'}, 400
        return {'message': 'Resend queued.'}, 200


class GeneratedDocumentRegenerateAPI(restful.Resource):
    """POST .../generated/<id>/regenerate - a fresh generation attempt for
    the same person, e.g. after fixing a placeholder that failed to resolve.
    Creates a new GeneratedDocument row rather than overwriting the old one,
    which stays as the audit record of what happened the first time."""

    @auth_required
    def post(self, document_id):
        original = db.session.query(GeneratedDocument).filter_by(id=document_id).first()
        if not original:
            return errors.GENERATED_DOCUMENT_NOT_FOUND

        requester = user_repository.get_by_id(g.current_user['id'])
        if not requester or not requester.is_event_admin(original.event_id):
            return errors.FORBIDDEN

        document_template = db.session.query(DocumentTemplate).filter_by(
            id=original.document_template_id).first()
        target_user = db.session.query(AppUser).filter_by(id=original.user_id).first()
        if not document_template or not target_user:
            return errors.GENERATED_DOCUMENT_NOT_FOUND

        try:
            generated_document = generate_document(
                document_template, target_user, requester, document_template.event,
                language=original.language, override_eligibility=True,
            )
        except GenerationError as e:
            return _generation_error_response(e)

        return serialize_generated_document(generated_document), 201


class GeneratedDocumentListAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('template_id', type=int, required=False)
        req_parser.add_argument('job_id', type=int, required=False)
        args = req_parser.parse_args()

        query = db.session.query(GeneratedDocument).filter_by(event_id=event_id)
        if args['template_id']:
            query = query.filter_by(document_template_id=args['template_id'])
        if args['job_id']:
            query = query.filter_by(job_id=args['job_id'])
        docs = query.order_by(GeneratedDocument.created_at.desc()).limit(500).all()
        return [serialize_generated_document(d) for d in docs], 200


# ---------------------------------------------------------------------------
# Admin: derived placeholders
# ---------------------------------------------------------------------------

def _validate_rules_payload(rules_data):
    """Enforced on save (design section 9.6): at most one "otherwise" rule
    (a null condition_expression), and only as the last rule. Returns an
    error message, or None when the payload is valid."""
    otherwise_count = sum(1 for r in rules_data if r.get('condition_expression') is None)
    if otherwise_count > 1:
        return 'Only one rule may be the "otherwise" rule.'
    for index, rule in enumerate(rules_data):
        if rule.get('condition_expression') is None and index != len(rules_data) - 1:
            return 'The "otherwise" rule (a null condition) must be the last rule.'
    return None


def _save_rules(derived_placeholder, rules_data):
    for index, rule_data in enumerate(rules_data):
        rule = DerivedPlaceholderRule(
            derived_placeholder_id=derived_placeholder.id,
            order=rule_data.get('order', index),
            condition_expression=rule_data.get('condition_expression'),
        )
        db.session.add(rule)
        db.session.flush()
        for language, text in (rule_data.get('texts') or {}).items():
            db.session.add(DerivedPlaceholderRuleTranslation(
                rule_id=rule.id, language=language, text=text or ''))


def _get_derived_placeholder_for_admin(derived_placeholder_id):
    """(derived_placeholder, None) or (None, error_response) - the shared
    lookup+authorize step for the by-id endpoints below, which take no
    event_id path segment to check against via event_admin_required_from_path."""
    derived = db.session.query(DerivedPlaceholder).filter_by(id=derived_placeholder_id).first()
    if not derived:
        return None, errors.DERIVED_PLACEHOLDER_NOT_FOUND
    requester = user_repository.get_by_id(g.current_user['id'])
    if not requester or not requester.is_event_admin(derived.event_id):
        return None, errors.FORBIDDEN
    return derived, None


class DerivedPlaceholderListAPI(restful.Resource):

    @event_admin_required_from_path
    def get(self, event_id):
        rows = (db.session.query(DerivedPlaceholder).filter_by(event_id=event_id)
                .order_by(DerivedPlaceholder.key).all())
        return [serialize_derived_placeholder(r) for r in rows], 200

    @event_admin_required_from_path
    def post(self, event_id):
        data = request.get_json() or {}
        key = (data.get('key') or '').strip().lower()
        if not key:
            return errors.MISSING_FIELDS

        existing = db.session.query(DerivedPlaceholder).filter_by(event_id=event_id, key=key).first()
        if existing:
            return errors.DERIVED_PLACEHOLDER_KEY_IN_USE

        rules_data = data.get('rules') or []
        validation_error = _validate_rules_payload(rules_data)
        if validation_error:
            return {'message': validation_error}, 400

        rule_texts = [text for rule in rules_data for text in (rule.get('texts') or {}).values()]
        cycle = find_cycle(event_id, changed_key=key, changed_rule_texts=rule_texts)
        if cycle:
            return {**errors.DERIVED_PLACEHOLDER_CYCLE[0], 'cycle': cycle}, errors.DERIVED_PLACEHOLDER_CYCLE[1]

        derived_placeholder = DerivedPlaceholder(
            event_id=event_id, key=key, description=data.get('description'),
            is_active=bool(data.get('is_active', True)),
        )
        db.session.add(derived_placeholder)
        db.session.flush()
        _save_rules(derived_placeholder, rules_data)
        db.session.commit()

        return serialize_derived_placeholder(derived_placeholder), 201


class DerivedPlaceholderAPI(restful.Resource):

    @auth_required
    def put(self, derived_placeholder_id):
        derived_placeholder, error = _get_derived_placeholder_for_admin(derived_placeholder_id)
        if error:
            return error

        data = request.get_json() or {}
        rules_data = data.get('rules') or []
        validation_error = _validate_rules_payload(rules_data)
        if validation_error:
            return {'message': validation_error}, 400

        rule_texts = [text for rule in rules_data for text in (rule.get('texts') or {}).values()]
        cycle = find_cycle(derived_placeholder.event_id, changed_key=derived_placeholder.key,
                            changed_rule_texts=rule_texts)
        if cycle:
            return {**errors.DERIVED_PLACEHOLDER_CYCLE[0], 'cycle': cycle}, errors.DERIVED_PLACEHOLDER_CYCLE[1]

        # The key is not editable here - every document already referencing
        # {this_key} would silently break if it moved out from under them.
        if 'description' in data:
            derived_placeholder.description = data.get('description')
        if 'is_active' in data:
            derived_placeholder.is_active = bool(data.get('is_active'))
        derived_placeholder.updated_at = datetime.now()

        for rule in list(derived_placeholder.rules):
            db.session.delete(rule)
        db.session.flush()
        _save_rules(derived_placeholder, rules_data)
        db.session.commit()

        return serialize_derived_placeholder(derived_placeholder), 200

    @auth_required
    def delete(self, derived_placeholder_id):
        derived_placeholder, error = _get_derived_placeholder_for_admin(derived_placeholder_id)
        if error:
            return error
        db.session.delete(derived_placeholder)
        db.session.commit()
        return '', 204


# ---------------------------------------------------------------------------
# Admin: user event data
# ---------------------------------------------------------------------------

class UserEventDataListAPI(restful.Resource):

    @event_admin_required_from_path
    def get(self, event_id):
        rows = db.session.query(UserEventData).filter_by(event_id=event_id).all()
        return [serialize_user_event_data(r) for r in rows], 200

    @event_admin_required_from_path
    def put(self, event_id):
        data = request.get_json() or {}
        entries = data.get('entries') or []
        user = get_user_from_request()

        for entry in entries:
            target_user_id = entry.get('user_id')
            key = (entry.get('key') or '').strip()
            if not target_user_id or not key:
                continue
            value = entry.get('value')

            row = db.session.query(UserEventData).filter_by(
                event_id=event_id, user_id=target_user_id, key=key).first()
            if row:
                row.value = value
                row.updated_by_user_id = user['id']
                row.updated_at = datetime.now()
            else:
                db.session.add(UserEventData(
                    event_id=event_id, user_id=target_user_id, key=key,
                    value=value, updated_by_user_id=user['id'],
                ))

        db.session.commit()
        rows = db.session.query(UserEventData).filter_by(event_id=event_id).all()
        return [serialize_user_event_data(r) for r in rows], 200


def _user_event_data_by_user(event_id):
    """{user_id: {key: value}} for an event, and the sorted set of keys in
    use - the shape both the grid and the CSV export build their columns
    from."""
    rows = db.session.query(UserEventData).filter_by(event_id=event_id).all()
    by_user = {}
    for row in rows:
        by_user.setdefault(row.user_id, {})[row.key] = row.value
    keys = sorted({row.key for row in rows})
    return by_user, keys


class UserEventDataGridAPI(restful.Resource):
    """GET .../user-data/grid - attendees x keys, design section 9.8. Rows
    cover the event's whole population (design 9.8: "a grid of attendees x
    keys"), not just people who already have a value - that's the point of
    a grid over the plain list UserEventDataListAPI already served."""

    @event_admin_required_from_path
    def get(self, event_id):
        by_user, keys = _user_event_data_by_user(event_id)

        event = db.session.query(Event).filter_by(id=event_id).first()
        user_ids = set(resolve_recipient_user_ids(event, {'type': 'everyone'})) if event else set()
        user_ids |= by_user.keys()

        users = (db.session.query(AppUser).filter(AppUser.id.in_(user_ids)).all()
                 if user_ids else [])

        rows = [{
            'user_id': user.id,
            'name': user.full_name,
            'email': user.email,
            'values': by_user.get(user.id, {}),
        } for user in sorted(users, key=lambda u: (u.lastname or '', u.firstname or ''))]

        return {'keys': keys, 'rows': rows}, 200


class UserEventDataExportAPI(restful.Resource):
    """GET .../user-data/export - a CSV with one row per person who has at
    least one value set, one column per key in use. Only people already in
    user_event_data are included (unlike the grid, which shows the whole
    population) - an all-blank row for everyone else isn't useful in a file
    meant to be edited and re-imported."""

    @event_admin_required_from_path
    def get(self, event_id):
        by_user, keys = _user_event_data_by_user(event_id)
        users = (db.session.query(AppUser).filter(AppUser.id.in_(by_user.keys())).all()
                 if by_user else [])
        users_by_id = {u.id: u for u in users}

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['email'] + keys)
        for user_id in sorted(by_user.keys()):
            user = users_by_id.get(user_id)
            if not user:
                continue
            writer.writerow([user.email] + [by_user[user_id].get(key, '') for key in keys])

        output = io.BytesIO(buffer.getvalue().encode('utf-8'))
        return send_file(
            output, mimetype='text/csv', as_attachment=True,
            attachment_filename='attendee_data.csv')


class UserEventDataImportAPI(restful.Resource):
    """POST .../user-data/import - CSV import, matched on email (design
    section 9.8). Columns other than `email` become keys.

    `apply: false` (the default) computes and returns the diff without
    writing anything - the "preview diff before applying" step; the frontend
    shows it, and only re-posts the same CSV with `apply: true` once the
    admin confirms. Stateless on purpose: nothing about the upload is kept
    server-side between the two calls, so there's no expiring session state
    to manage for what is, in practice, a single admin clicking two buttons
    a few seconds apart.
    """

    @event_admin_required_from_path
    def post(self, event_id):
        data = request.get_json() or {}
        csv_text = data.get('csv') or ''
        apply_changes = bool(data.get('apply', False))

        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames = reader.fieldnames or []
        email_field = next((f for f in fieldnames if f.strip().lower() == 'email'), None)
        if not email_field:
            return {'message': 'The CSV must have an "email" column.'}, 400
        key_fields = [f for f in fieldnames if f != email_field and f.strip()]

        rows_by_email = {}
        for row in reader:
            email = (row.get(email_field) or '').strip().lower()
            if email:
                rows_by_email[email] = row
        if not rows_by_email:
            return {'message': 'No rows with an email were found in the CSV.'}, 400

        users_by_email = {
            u.email.lower(): u for u in
            db.session.query(AppUser).filter(func.lower(AppUser.email).in_(rows_by_email.keys())).all()
        }
        matched_user_ids = [u.id for u in users_by_email.values()]
        existing = {
            (row.user_id, row.key): row for row in
            (db.session.query(UserEventData).filter_by(event_id=event_id)
             .filter(UserEventData.user_id.in_(matched_user_ids)).all()
             if matched_user_ids else [])
        }

        requester = get_user_from_request()
        preview_rows, unmatched_emails = [], []

        for email, row in rows_by_email.items():
            user = users_by_email.get(email)
            if not user:
                unmatched_emails.append(email)
                continue

            changes = {}
            for key in key_fields:
                new_value = (row.get(key) or '').strip()
                existing_row = existing.get((user.id, key))
                old_value = existing_row.value if existing_row else None
                if (old_value or '') == new_value:
                    continue
                changes[key] = {'old': old_value, 'new': new_value}
                if apply_changes:
                    if existing_row:
                        existing_row.value = new_value
                        existing_row.updated_by_user_id = requester['id']
                        existing_row.updated_at = datetime.now()
                    else:
                        db.session.add(UserEventData(
                            event_id=event_id, user_id=user.id, key=key,
                            value=new_value, updated_by_user_id=requester['id'],
                        ))

            if changes:
                preview_rows.append({'email': email, 'user_id': user.id, 'changes': changes})

        if apply_changes:
            db.session.commit()

        return {
            'rows': preview_rows,
            'unmatched_emails': unmatched_emails,
            'changed_count': len(preview_rows),
            'applied': apply_changes,
        }, 200


# ---------------------------------------------------------------------------
# Attendee-facing
# ---------------------------------------------------------------------------

class DocumentAvailableAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        language = request.args.get('language', 'en')

        user = db.session.query(AppUser).filter_by(id=g.current_user['id']).first()
        if not user:
            return errors.USER_NOT_FOUND

        templates = db.session.query(DocumentTemplate).filter_by(
            event_id=args['event_id'], is_active=True, self_service=True).all()

        results = []
        for template in templates:
            # One resolver per template (not shared across all of them, unlike
            # a single flat eligibility context would be) so an
            # eligibility_expression using the `key`/`operator` answer leaf
            # reads through that template's own linked-form chain.
            resolver = PlaceholderResolver(template, template.event, language)
            answer_index = _AnswerIndex(user.id, resolver.form_links)
            context = build_eligibility_context(
                user.id, args['event_id'],
                answer_resolver=lambda key, r=resolver, ai=answer_index: r.answer_value(user, ai, key))
            if not is_eligible(template, context):
                continue

            translation = template.get_translation(language) or template.get_translation('en')
            blockers, prompts = evaluate_form_requirements(template, user, language)

            previous = (
                db.session.query(GeneratedDocument)
                .filter_by(document_template_id=template.id, user_id=user.id,
                           status=GeneratedDocumentStatus.GENERATED)
                .order_by(GeneratedDocument.generated_at.desc())
                .all()
            )

            results.append({
                'id': template.id,
                'key': template.key,
                'name': translation.name if translation else template.key,
                'description': translation.description if translation else None,
                'instructions': translation.instructions if translation else None,
                'blockers': blockers,
                'prompts': prompts,
                'previous_documents': [serialize_generated_document(d) for d in previous],
            })

        return results, 200


class DocumentRequestAPI(restful.Resource):

    @auth_required
    def post(self):
        data = request.get_json() or {}
        template_id = data.get('template_id')
        language = data.get('language', 'en')

        document_template = db.session.query(DocumentTemplate).filter_by(
            id=template_id, is_active=True, self_service=True).first()
        if not document_template:
            return errors.DOCUMENT_TEMPLATE_NOT_FOUND

        user = db.session.query(AppUser).filter_by(id=g.current_user['id']).first()
        if not user:
            return errors.USER_NOT_FOUND

        try:
            generated_document = generate_document(
                document_template, user, user, document_template.event, language=language)
        except GenerationError as e:
            return _generation_error_response(e)

        return serialize_generated_document(generated_document), 201


class GeneratedDocumentDownloadAPI(restful.Resource):

    @auth_required
    def get(self, document_id):
        generated_document = db.session.query(GeneratedDocument).filter_by(id=document_id).first()
        if not generated_document:
            return errors.GENERATED_DOCUMENT_NOT_FOUND
        if (generated_document.status != GeneratedDocumentStatus.GENERATED
                or not generated_document.storage_blob_name):
            return errors.DOCUMENT_NOT_YET_GENERATED

        requester = user_repository.get_by_id(g.current_user['id'])
        is_owner = requester and generated_document.user_id == requester.id
        is_admin = requester and requester.is_event_admin(generated_document.event_id)
        if not (is_owner or is_admin):
            return errors.FORBIDDEN

        bucket = storage.get_storage_bucket()
        blob = bucket.blob(generated_document.storage_blob_name)
        with tempfile.NamedTemporaryFile(suffix='.pdf') as temp:
            blob.download_to_filename(temp.name)
            return send_file(
                temp.name, as_attachment=True,
                attachment_filename=generated_document.filename or 'document.pdf')
