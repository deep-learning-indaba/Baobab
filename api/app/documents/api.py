import tempfile
from datetime import datetime

import flask_restful as restful
from flask_restful import reqparse
from flask import g, request, send_file

from app import db, LOGGER
from app.utils import errors, storage
from app.utils.auth import auth_required, event_admin_required, get_user_from_request
from app.users.repository import UserRepository as user_repository
from app.users.models import AppUser
from app.forms.models import Form


from app.documents.models import (
    DocumentTemplate, DocumentTemplateTranslation, DocumentTemplateVariant,
    DocumentTemplateForm, DocumentTemplateFormTranslation, UserEventData,
    GeneratedDocument, GeneratedDocumentStatus,
)
from app.documents.mixins import document_admin_required, event_admin_required_from_path
from app.documents.google_client import (
    build_default_client, describe_configured_identity, extract_file_id, AccessStatus, GoogleApiError,
)
from app.documents.resolver import PlaceholderResolver, evaluate_form_requirements
from app.documents.variant_selection import select_variant, is_eligible, NoMatchingVariant
from app.documents.eligibility import build_eligibility_context
from app.documents.generator import generate_document, GenerationError


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
        'status': generated_document.status,
        'filename': generated_document.filename,
        'error_code': generated_document.error_code,
        'error_detail': generated_document.error_detail,
        'created_at': generated_document.created_at.isoformat() if generated_document.created_at else None,
        'generated_at': generated_document.generated_at.isoformat() if generated_document.generated_at else None,
        'download_url': (
            f'/api/v1/documents/generated/{generated_document.id}/download'
            if generated_document.status == GeneratedDocumentStatus.GENERATED else None
        ),
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

        context = build_eligibility_context(target_user.id, document_template.event_id)
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
            resolver = PlaceholderResolver(document_template, document_template.event, language)
            resolution = resolver.resolve(target_user, variant=variant)
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
    """Admin-triggered single-recipient generation. Bulk generation (a job
    fanning out to many recipients via a worker) is design section 8.2 and is
    not part of this phase."""

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


class GeneratedDocumentListAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('template_id', type=int, required=False)
        args = req_parser.parse_args()

        query = db.session.query(GeneratedDocument).filter_by(event_id=event_id)
        if args['template_id']:
            query = query.filter_by(document_template_id=args['template_id'])
        docs = query.order_by(GeneratedDocument.created_at.desc()).limit(500).all()
        return [serialize_generated_document(d) for d in docs], 200


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

        context = build_eligibility_context(user.id, args['event_id'])

        results = []
        for template in templates:
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
