from datetime import datetime
import csv
import io
import re
import traceback
import random

import flask_restful as restful
from flask_restful import reqparse
from flask import g, request, Response, stream_with_context

from app.forms.models import (
    Form, FormResponse, FormAnswer, FormSection, FormQuestion,
    FormTranslation, FormSectionTranslation, FormQuestionTranslation,
    DependencyEvaluator, FormResponseTag, ValidationError,
    DISPLAY_ONLY_QUESTION_TYPES, MULTI_VALUE_SEPARATOR
)
from app.forms.visibility import VisibilityEvaluator
from app.forms.mixins import (
    uses_new_form, get_form_by_type,
    apply_form_type_defaults, validate_form_type_constraints,
    form_admin_required, verify_form_event, is_admin_of_form
)
from app.utils.auth import auth_required, event_admin_required
from app.utils import errors
from app import db, LOGGER
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app.utils.emailer import email_user
from app.utils import misc
from app.applicationModel.models import ApplicationForm
from app.registration.models import RegistrationForm
from app.reviews.models import ReviewForm, ReviewerTag
from app.events.models import EventRole
from app.tags.repository import TagRepository as tag_repository


def serialize_form(form, language='en', include_inactive=False):
    """Serialize a form with all sections and questions with all translations
    
    Args:
        form: Form object to serialize
        language: Language code (deprecated, kept for compatibility - now returns all languages)
        include_inactive: If True, include inactive sections/questions (for admin audit)
    """
    sections_data = []

    # Section and question translations are lazy='dynamic' relationships, so
    # iterating them per row issues a query each. Fetch them all up front in
    # two queries and group in memory - this endpoint is on the hot path for
    # both the editor and every respondent loading the form.
    section_ids = [s.id for s in form.sections]
    question_ids = [q.id for s in form.sections for q in s.questions]

    section_translations_by_section = {}
    if section_ids:
        for translation in db.session.query(FormSectionTranslation).filter(
            FormSectionTranslation.form_section_id.in_(section_ids)
        ).all():
            section_translations_by_section.setdefault(
                translation.form_section_id, {}
            )[translation.language] = translation

    question_translations_by_question = {}
    if question_ids:
        for translation in db.session.query(FormQuestionTranslation).filter(
            FormQuestionTranslation.form_question_id.in_(question_ids)
        ).all():
            question_translations_by_question.setdefault(
                translation.form_question_id, {}
            )[translation.language] = translation

    for section in form.sections:
        if not include_inactive and not section.is_active:
            continue

        section_translations_dict = section_translations_by_section.get(section.id, {})

        questions_data = []
        for question in section.questions:
            if not include_inactive and not question.is_active:
                continue

            question_translations_dict = question_translations_by_question.get(question.id, {})

            # Build i18n objects for all translatable fields
            headline_i18n = {}
            description_i18n = {}
            placeholder_i18n = {}
            validation_regex_i18n = {}
            validation_text_i18n = {}
            options_i18n = {}
            
            for lang, trans in question_translations_dict.items():
                headline_i18n[lang] = trans.headline
                description_i18n[lang] = trans.description
                placeholder_i18n[lang] = trans.placeholder
                validation_regex_i18n[lang] = trans.validation_regex
                validation_text_i18n[lang] = trans.validation_text
                options_i18n[lang] = trans.options
            
            question_data = {
                'id': question.id,
                'type': question.type,
                'order': question.order,
                'is_required': question.is_required,
                'key': question.key,
                'dependency_expression': question.dependency_expression,
                'tag_expression': question.tag_expression,
                'linked_question_id': question.linked_question_id,
                'settings': question.settings,
                'is_active': question.is_active,
                'version': question.version,
                'created_at': question.created_at.isoformat() if question.created_at else None,
                'updated_at': question.updated_at.isoformat() if question.updated_at else None,
                'headline': headline_i18n,
                'description': description_i18n,
                'placeholder': placeholder_i18n,
                'validation_regex': validation_regex_i18n,
                'validation_text': validation_text_i18n,
                'options': options_i18n
            }
            questions_data.append(question_data)
        
        # Build i18n objects for section translatable fields
        name_i18n = {}
        description_i18n = {}
        for lang, trans in section_translations_dict.items():
            name_i18n[lang] = trans.name
            description_i18n[lang] = trans.description
        
        section_data = {
            'id': section.id,
            'order': section.order,
            'key': section.key,
            'dependency_expression': section.dependency_expression,
            'tag_expression': section.tag_expression,
            'is_active': section.is_active,
            'version': section.version,
            'created_at': section.created_at.isoformat() if section.created_at else None,
            'updated_at': section.updated_at.isoformat() if section.updated_at else None,
            'name': name_i18n,
            'description': description_i18n,
            'questions': questions_data
        }
        sections_data.append(section_data)
    
    # Get all translations for the form name and description
    form_translations_dict = {}
    for translation in form.translations:
        form_translations_dict[translation.language] = translation
    
    name_i18n = {}
    description_i18n = {}
    for lang, trans in form_translations_dict.items():
        name_i18n[lang] = trans.name
        description_i18n[lang] = trans.description
    
    return {
        'id': form.id,
        'event_id': form.event_id,
        'form_type': form.form_type,
        'stage': form.stage,
        'name': name_i18n,
        'description': description_i18n,
        'is_active': form.is_active,
        'is_open': form.is_open,
        'multiple_responses': form.multiple_responses,
        'allow_edits': form.allow_edits,
        'visibility_expression': form.visibility_expression,
        'settings': form.settings,
        'created_at': form.created_at.isoformat() if form.created_at else None,
        'updated_at': form.updated_at.isoformat() if form.updated_at else None,
        'linked_form_id': form.linked_form_id,
        'sections': sections_data
    }


def _error(message, status):
    """Build an error response carrying both conventional keys.

    Most of the API returns errors under `message` (see app/utils/errors.py)
    while the forms endpoints grew up returning `error`, so clients had to
    guess. Emitting both keeps existing consumers working and lets generic
    error handling find a message.
    """
    return {'error': message, 'message': message}, status


def serialize_form_summary(form):
    """Serialize a form without its sections or questions.

    For list views and form pickers. serialize_form walks every section and
    question and their (lazy='dynamic') translations, so using it for a list
    means a query per section and per question, per form.
    """
    name_i18n = {}
    description_i18n = {}
    for translation in form.translations:
        name_i18n[translation.language] = translation.name
        description_i18n[translation.language] = translation.description

    return {
        'id': form.id,
        'event_id': form.event_id,
        'form_type': form.form_type,
        'stage': form.stage,
        'name': name_i18n,
        'description': description_i18n,
        'is_active': form.is_active,
        'is_open': form.is_open,
        'multiple_responses': form.multiple_responses,
        'allow_edits': form.allow_edits,
        'settings': form.settings,
        'linked_form_id': form.linked_form_id,
        'created_at': form.created_at.isoformat() if form.created_at else None,
        'updated_at': form.updated_at.isoformat() if form.updated_at else None,
    }


def _get_question_ids_for_form(form_id):
    """Set of active question ids belonging to a form."""
    return {
        row[0]
        for row in db.session.query(FormQuestion.id).filter(
            FormQuestion.form_id == form_id,
            FormQuestion.is_active == True  # noqa: E712
        ).all()
    }


def _get_response_for_event(response_id, form_id, event_id):
    """Load a FormResponse, checking it belongs to a form owned by event_id.

    event_admin_required only proves the caller administers event_id, so admin
    response endpoints must confirm the form they are addressing is actually
    that event's - see verify_form_event.
    """
    return (
        db.session.query(FormResponse)
        .join(Form, FormResponse.form_id == Form.id)
        .filter(
            FormResponse.id == response_id,
            FormResponse.form_id == form_id,
            Form.event_id == event_id,
        )
        .first()
    )


def _linked_form_is_in_event(linked_form_id, event_id):
    """Whether linked_form_id names a form belonging to event_id.

    Linking across events would leak one event's responses into another's
    review/prepopulation flows.
    """
    linked = db.session.query(Form).filter_by(id=linked_form_id).first()
    return linked is not None and linked.event_id == event_id


def serialize_response(response):
    """Serialize a form response with answers"""
    answers_data = []
    for answer in response.answers:
        answers_data.append({
            'id': answer.id,
            'question_id': answer.question_id,
            'value': answer.value,
            'is_active': answer.is_active
        })

    tags_data = []
    for rt in response.response_tags:
        tag_translation = rt.tag.get_translation('en')
        tags_data.append({
            'id': rt.tag_id,
            'name': tag_translation.name if tag_translation else ''
        })

    return {
        'id': response.id,
        'form_id': response.form_id,
        'user_id': response.user_id,
        'is_submitted': response.is_submitted,
        'submitted_timestamp': response.submitted_timestamp.isoformat() if response.submitted_timestamp else None,
        'is_withdrawn': response.is_withdrawn,
        'withdrawn_timestamp': response.withdrawn_timestamp.isoformat() if response.withdrawn_timestamp else None,
        'started_timestamp': response.started_timestamp.isoformat() if response.started_timestamp else None,
        'language': response.language,
        'linked_response_id': response.linked_response_id,
        'answers': answers_data,
        'tags': tags_data
    }


def serialize_response_summary(response):
    """Serialize a form response summary without answers (for list views)"""
    return {
        'id': response.id,
        'form_id': response.form_id,
        'user_id': response.user_id,
        'is_submitted': response.is_submitted,
        'submitted_timestamp': response.submitted_timestamp.isoformat() if response.submitted_timestamp else None,
        'is_withdrawn': response.is_withdrawn,
        'withdrawn_timestamp': response.withdrawn_timestamp.isoformat() if response.withdrawn_timestamp else None,
        'started_timestamp': response.started_timestamp.isoformat() if response.started_timestamp else None,
        'language': response.language,
        'answer_count': len(response.answers) if response.answers else 0
    }


def serialize_response_with_linked(response):
    """Serialize a form response with answers and linked response details (for detail views)"""
    response_data = serialize_response(response)
    
    # Add linked response if it exists
    if response.linked_response_id and response.linked_response:
        response_data['linked_response'] = serialize_response(response.linked_response)
    else:
        response_data['linked_response'] = None
    
    return response_data


class FormListAPI(restful.Resource):
    """Form list and creation operations"""

    # Scoped to a single event and restricted to that event's admins: this
    # returns full form definitions, so an unscoped list would hand every
    # form in the system to any authenticated user.
    @event_admin_required
    def get(self, event_id):
        """Get list of forms for an event (admin only)"""
        try:
            language = request.args.get('language', 'en')

            query = db.session.query(Form).filter_by(event_id=event_id)

            # Filter by active status if specified
            is_active = request.args.get('is_active')
            if is_active is not None:
                query = query.filter_by(is_active=is_active.lower() == 'true')

            # Filter by open status if specified
            is_open = request.args.get('is_open')
            if is_open is not None:
                query = query.filter_by(is_open=is_open.lower() == 'true')

            # Filter by created_by if specified (admin feature)
            created_by = request.args.get('created_by')
            if created_by:
                query = query.filter_by(created_by_user_id=created_by)

            forms = query.order_by(Form.created_at.desc()).all()

            # Summary only - the full structure of every form is a lot of
            # payload for what callers use this for (form pickers and lists),
            # and building it triggers a query per section and per question.
            forms_data = [serialize_form_summary(form) for form in forms]

            return forms_data, 200

        except Exception as e:
            LOGGER.error(f"Error getting forms list: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def post(self, event_id):
        """Create a new empty form (use FormStructureAPI to add sections/questions)"""
        try:
            args = request.get_json()
            user_id = g.current_user['id']

            # event_id comes from event_admin_required, which has verified the
            # caller administers it - never trust a body-supplied event_id.
            form_type = args.get('form_type')
            stage = args.get('stage')

            # Validate form type constraints before creating
            if form_type:
                constraint_error = validate_form_type_constraints(event_id, form_type)
                if constraint_error:
                    return _error(constraint_error, 400)

            linked_form_id = args.get('linked_form_id')
            if linked_form_id and not _linked_form_is_in_event(linked_form_id, event_id):
                return _error('Linked form must belong to the same event', 400)

            # Create empty form
            form = Form(
                event_id=event_id,
                created_by_user_id=user_id,
                is_open=args.get('is_open', False),
                is_active=args.get('is_active', True),
                linked_form_id=linked_form_id,
                multiple_responses=args.get('multiple_responses', False),
                settings=args.get('settings'),
                form_type=form_type,
                stage=stage
            )

            # Apply form-type defaults after construction so explicit args win
            if form_type:
                apply_form_type_defaults(form, form_type, stage)
            
            db.session.add(form)
            db.session.commit()
            
            return {'id': form.id, 'message': 'Form created successfully. Use PUT /forms/{id}/structure to add sections and questions.'}, 201
            
        except Exception as e:
            LOGGER.error(f"Error creating form: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormAPI(restful.Resource):
    """Generic form operations - used by all form types"""

    # Admin-only: returns the full authoring view of the form. Applicants read
    # forms through FormStructureAPI.get, which applies visibility rules.
    @form_admin_required
    def get(self, form_id, form):
        """Get form definition (admin only)"""
        try:
            language = request.args.get('language', 'en')
            return serialize_form(form, language), 200

        except Exception as e:
            LOGGER.error(f"Error getting form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @form_admin_required
    def put(self, form_id, form):
        """Update form definition (admin only)"""
        try:
            args = request.get_json()

            # Update form properties
            if 'is_open' in args:
                form.is_open = args['is_open']
            if 'is_active' in args:
                form.is_active = args['is_active']
            if 'allow_edits' in args:
                form.allow_edits = args['allow_edits']
            if 'visibility_expression' in args:
                form.visibility_expression = args['visibility_expression']
            if 'linked_form_id' in args:
                if args['linked_form_id'] and not _linked_form_is_in_event(
                    args['linked_form_id'], form.event_id
                ):
                    return _error('Linked form must belong to the same event', 400)
                form.linked_form_id = args['linked_form_id']
            if 'settings' in args:
                form.settings = args['settings']

            # Update form name and description translations
            if 'name' in args and args['name']:
                for lang, name_text in args['name'].items():
                    # Find or create translation
                    translation = db.session.query(FormTranslation).filter_by(
                        form_id=form.id,
                        language=lang
                    ).first()
                    
                    if translation:
                        translation.name = name_text
                        if 'description' in args and args['description']:
                            translation.description = args['description'].get(lang)
                    else:
                        translation = FormTranslation(
                            form_id=form.id,
                            language=lang,
                            name=name_text,
                            description=args.get('description', {}).get(lang) if 'description' in args else None
                        )
                        db.session.add(translation)
            
            form.updated_at = datetime.now()
            
            db.session.commit()
            
            language = request.args.get('language', 'en')
            return serialize_form(form, language), 200
            
        except Exception as e:
            LOGGER.error(f"Error updating form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE
    
    @form_admin_required
    def delete(self, form_id, form):
        """Soft delete form (admin only)"""
        try:
            form.is_active = False
            form.updated_at = datetime.now()
            db.session.commit()

            return {}, 204

        except Exception as e:
            LOGGER.error(f"Error deleting form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


def _remap_dependency_expression(expression, id_map):
    """Recursively remap question_id values in a dependency expression using id_map."""
    if expression is None or not id_map:
        return expression
    if isinstance(expression, dict):
        if 'question_id' in expression:
            qid = expression.get('question_id')
            if qid in id_map:
                return {**expression, 'question_id': id_map[qid]}
        elif 'conditions' in expression:
            return {**expression, 'conditions': [_remap_dependency_expression(c, id_map) for c in expression['conditions']]}
    return expression


class FormStructureAPI(restful.Resource):
    """Manage form structure - sections and questions"""
    
    # Readable by applicants as well as admins - this is the endpoint the form
    # renderer loads. Non-admins only get active forms they are allowed to see.
    @auth_required
    def get(self, form_id):
        """Get form structure with version info"""
        try:
            db.session.expire_all()  # Clear any cached objects
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND

            is_admin = is_admin_of_form(form)
            if not is_admin:
                if not form.is_active:
                    return errors.FORM_NOT_FOUND
                if not VisibilityEvaluator.check_form_visibility(
                    form, g.current_user['id'], form.event_id
                ):
                    return errors.FORBIDDEN

            language = request.args.get('language', 'en')
            # Inactive (soft-deleted) sections and questions are an admin audit
            # concern - never expose them to respondents.
            include_inactive = (
                is_admin and request.args.get('include_inactive', 'false').lower() == 'true'
            )
            return serialize_form(form, language, include_inactive=include_inactive), 200

        except Exception as e:
            LOGGER.error(f"Error getting form structure {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @form_admin_required
    def put(self, form_id, form):
        """Update form structure (sections and questions) with soft delete support (admin only)"""
        try:
            args = request.get_json()

            # Update form name and description translations if provided
            if 'name' in args and args['name']:
                for lang, name_text in args['name'].items():
                    translation = db.session.query(FormTranslation).filter_by(
                        form_id=form.id,
                        language=lang
                    ).first()
                    
                    if translation:
                        translation.name = name_text
                        if 'description' in args and args['description']:
                            translation.description = args['description'].get(lang)
                    else:
                        translation = FormTranslation(
                            form_id=form.id,
                            language=lang,
                            name=name_text,
                            description=args.get('description', {}).get(lang) if 'description' in args else None
                        )
                        db.session.add(translation)
            
            # Update form settings if provided
            if 'settings' in args:
                form.settings = args['settings']
            if 'is_open' in args:
                form.is_open = args['is_open']
            if 'is_active' in args:
                form.is_active = args['is_active']
            if 'multiple_responses' in args:
                form.multiple_responses = args['multiple_responses']
            if 'allow_edits' in args:
                form.allow_edits = args['allow_edits']
            if 'visibility_expression' in args:
                form.visibility_expression = args['visibility_expression']
            if 'linked_form_id' in args:
                form.linked_form_id = args['linked_form_id']
            
            sections_data = args.get('sections', [])

            # Maps frontend client_id of new questions to their real DB id after flush
            client_id_to_real_id = {}
            # (object, raw_dep_expr) pairs for second-pass remapping
            sections_needing_dep_remap = []
            questions_needing_dep_remap = []

            # Track which sections/questions are in the incoming data
            incoming_section_ids = [s['id'] for s in sections_data if 'id' in s]
            incoming_question_ids = []
            for section_data in sections_data:
                for question_data in section_data.get('questions', []):
                    if 'id' in question_data:
                        incoming_question_ids.append(question_data['id'])
            
            # Soft delete sections that are no longer in the structure
            for section in form.sections:
                if section.id not in incoming_section_ids and section.is_active:
                    section.is_active = False
                    section.version += 1
                    section.updated_at = datetime.now()
                    LOGGER.info(f"Soft deleting section {section.id}")
            
            # Soft delete questions that are no longer in the structure
            for question in form.questions:
                if question.id not in incoming_question_ids and question.is_active:
                    question.is_active = False
                    question.version += 1
                    question.updated_at = datetime.now()
                    LOGGER.info(f"Soft deleting question {question.id}")

            # Index this form's existing sections and questions once, rather
            # than issuing a lookup query per incoming section and question.
            existing_sections = {s.id: s for s in form.sections}
            existing_questions = {q.id: q for q in form.questions}

            # Process sections
            for section_data in sections_data:
                if 'id' in section_data:
                    # Update existing section (scoped to this form)
                    section = existing_sections.get(section_data['id'])

                    if not section:
                        return _error(f"Section {section_data['id']} not found", 404)
                    
                    # Reactivate if it was previously soft deleted
                    if not section.is_active and section_data.get('is_active', True):
                        section.is_active = True
                        section.version += 1
                    
                    section.order = section_data.get('order', section.order)
                    # `key in data` rather than `.get(key, current)`: the editor
                    # signals "cleared" by sending null/empty, and .get()'s
                    # default swallowed that and kept the stale value, making
                    # keys, dependencies and tag rules impossible to remove.
                    if 'key' in section_data:
                        section.key = section_data['key'] or None
                    if 'dependency_expression' in section_data:
                        section.dependency_expression = section_data['dependency_expression']
                    if 'tag_expression' in section_data:
                        section.tag_expression = section_data['tag_expression']
                    section.updated_at = datetime.now()
                    if section_data.get('dependency_expression'):
                        sections_needing_dep_remap.append((section, section_data['dependency_expression']))

                    # Update translations
                    section_translations = {
                        t.language: t for t in section.translations.all()
                    }
                    for lang, name in section_data.get('name', {}).items():
                        trans = section_translations.get(lang)
                        if trans:
                            trans.name = name
                            trans.description = section_data.get('description', {}).get(lang, trans.description)
                        else:
                            trans = FormSectionTranslation(
                                form_section_id=section.id,
                                language=lang,
                                name=name,
                                description=section_data.get('description', {}).get(lang)
                            )
                            db.session.add(trans)
                else:
                    # Create new section
                    section = FormSection(
                        form_id=form_id,
                        order=section_data['order'],
                        key=section_data.get('key') or None,
                        dependency_expression=section_data.get('dependency_expression'),
                        tag_expression=section_data.get('tag_expression')
                    )
                    db.session.add(section)
                    db.session.flush()
                    if section_data.get('dependency_expression'):
                        sections_needing_dep_remap.append((section, section_data['dependency_expression']))

                    # Add translations
                    for lang, name in section_data.get('name', {}).items():
                        trans = FormSectionTranslation(
                            form_section_id=section.id,
                            language=lang,
                            name=name,
                            description=section_data.get('description', {}).get(lang)
                        )
                        db.session.add(trans)
                
                # Process questions in this section
                for question_data in section_data.get('questions', []):
                    if 'id' in question_data:
                        # Update existing question (scoped to this form)
                        question = existing_questions.get(question_data['id'])

                        if not question:
                            return _error(f"Question {question_data['id']} not found", 404)
                        
                        # Reactivate if it was previously soft deleted
                        if not question.is_active and question_data.get('is_active', True):
                            question.is_active = True
                            question.version += 1
                        
                        question.section_id = section.id
                        question.order = question_data.get('order', question.order)
                        question.type = question_data.get('type', question.type)
                        question.is_required = question_data.get('is_required', question.is_required)
                        # See the section branch above: presence-checked so the
                        # editor can clear these, not just overwrite them.
                        if 'key' in question_data:
                            question.key = question_data['key'] or None
                        if 'settings' in question_data:
                            question.settings = question_data['settings']
                        if 'dependency_expression' in question_data:
                            question.dependency_expression = question_data['dependency_expression']
                        if 'tag_expression' in question_data:
                            question.tag_expression = question_data['tag_expression']
                        if 'linked_question_id' in question_data:
                            question.linked_question_id = question_data['linked_question_id']
                        question.updated_at = datetime.now()
                        if question_data.get('dependency_expression'):
                            questions_needing_dep_remap.append((question, question_data['dependency_expression']))

                        # Update translations. `options` is presence-checked for
                        # the same reason: changing a question away from a choice
                        # type sends no options, and defaulting to the stored
                        # value left orphaned options behind that then failed
                        # every free-text answer as an invalid option.
                        has_options_key = 'options' in question_data
                        question_translations = {
                            t.language: t for t in question.translations.all()
                        }
                        for lang, headline in question_data.get('headline', {}).items():
                            trans = question_translations.get(lang)
                            if trans:
                                trans.headline = headline
                                trans.description = question_data.get('description', {}).get(lang, trans.description)
                                trans.placeholder = question_data.get('placeholder', {}).get(lang, trans.placeholder)
                                trans.validation_regex = question_data.get('validation_regex', {}).get(lang, trans.validation_regex)
                                trans.validation_text = question_data.get('validation_text', {}).get(lang, trans.validation_text)
                                if has_options_key:
                                    trans.options = (question_data['options'] or {}).get(lang)
                            else:
                                trans = FormQuestionTranslation(
                                    form_question_id=question.id,
                                    language=lang,
                                    headline=headline,
                                    description=question_data.get('description', {}).get(lang),
                                    placeholder=question_data.get('placeholder', {}).get(lang),
                                    validation_regex=question_data.get('validation_regex', {}).get(lang),
                                    validation_text=question_data.get('validation_text', {}).get(lang),
                                    options=question_data.get('options', {}).get(lang)
                                )
                                db.session.add(trans)
                    else:
                        # Create new question
                        question = FormQuestion(
                            form_id=form_id,
                            section_id=section.id,
                            order=question_data['order'],
                            question_type=question_data['type'],
                            is_required=question_data.get('is_required', True),
                            key=question_data.get('key') or None,
                            settings=question_data.get('settings'),
                            dependency_expression=question_data.get('dependency_expression'),
                            tag_expression=question_data.get('tag_expression'),
                            linked_question_id=question_data.get('linked_question_id')
                        )
                        db.session.add(question)
                        db.session.flush()
                        if 'client_id' in question_data:
                            client_id_to_real_id[question_data['client_id']] = question.id
                        if question_data.get('dependency_expression'):
                            questions_needing_dep_remap.append((question, question_data['dependency_expression']))

                        # Add translations
                        for lang, headline in question_data.get('headline', {}).items():
                            trans = FormQuestionTranslation(
                                form_question_id=question.id,
                                language=lang,
                                headline=headline,
                                description=question_data.get('description', {}).get(lang),
                                placeholder=question_data.get('placeholder', {}).get(lang),
                                validation_regex=question_data.get('validation_regex', {}).get(lang),
                                validation_text=question_data.get('validation_text', {}).get(lang),
                                options=question_data.get('options', {}).get(lang)
                            )
                            db.session.add(trans)

            # Second pass: remap dependency expressions that reference client IDs of newly created questions
            if client_id_to_real_id:
                for section, dep_expr in sections_needing_dep_remap:
                    section.dependency_expression = _remap_dependency_expression(dep_expr, client_id_to_real_id)
                for question, dep_expr in questions_needing_dep_remap:
                    question.dependency_expression = _remap_dependency_expression(dep_expr, client_id_to_real_id)

            form.updated_at = datetime.now()
            db.session.commit()

            language = request.args.get('language', 'en')
            return serialize_form(form, language), 200
            
        except Exception as e:
            LOGGER.error(f"Error updating form structure {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormResponseAPI(restful.Resource):
    """Form response management"""
    
    @auth_required
    def post(self, form_id):
        """Create a new response"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            if not form.is_open:
                return errors.APPLICATIONS_CLOSED
            
            user_id = g.current_user['id']
            args = request.get_json()
            
            # Check visibility if expression exists
            if form.visibility_expression:
                if not VisibilityEvaluator.check_form_visibility(form, user_id, form.event_id):
                    return _error('You do not have permission to access this form', 403)
            
            linked_response_id = args.get('linked_response_id')

            # Check if multiple_responses is allowed
            if not form.multiple_responses:
                # Check if user already has any response (submitted or not)
                existing_response = db.session.query(FormResponse).filter_by(
                    form_id=form_id,
                    user_id=user_id
                ).order_by(FormResponse.id.desc()).first()

                if existing_response:
                    return {
                        'error': 'Response already exists',
                        'message': 'A response already exists for this form. Use PUT to update it.',
                        'response_id': existing_response.id
                    }, 400
            elif linked_response_id:
                # For multi-response forms (review forms), prevent duplicate assignments:
                # one reviewer should only have one response per linked application response.
                existing_review = db.session.query(FormResponse).filter_by(
                    form_id=form_id,
                    user_id=user_id,
                    linked_response_id=linked_response_id
                ).first()
                if existing_review:
                    return {
                        'error': 'Review already exists',
                        'message': 'You are already assigned to review this response.',
                        'response_id': existing_review.id
                    }, 400

            # Create new response
            language = args.get('language', 'en')
            response = FormResponse(
                form_id=form_id,
                user_id=user_id,
                language=language,
                linked_response_id=linked_response_id
            )
            db.session.add(response)
            db.session.flush()

            # Add answers
            if 'answers' in args:
                valid_question_ids = _get_question_ids_for_form(form_id)
                for answer_data in args['answers']:
                    question_id = answer_data['question_id']
                    value = answer_data['value']

                    # Only accept answers to this form's own active questions -
                    # the FK alone would happily let a caller write answers
                    # against another form's questions.
                    if question_id not in valid_question_ids:
                        return {
                            'error': 'Invalid question',
                            'message': f'Question {question_id} does not belong to this form'
                        }, 400

                    new_answer = FormAnswer(
                        response_id=response.id,
                        question_id=question_id,
                        value=value
                    )
                    db.session.add(new_answer)

            db.session.commit()
            return serialize_response(response), 201
            
        except Exception as e:
            LOGGER.error(f"Error creating response for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE
    
    @auth_required
    def put(self, form_id):
        """Update an existing response"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            if not form.is_open:
                return errors.APPLICATIONS_CLOSED
            
            user_id = g.current_user['id']
            args = request.get_json()
            response_id = args.get('response_id')
            
            if not response_id:
                return _error('response_id is required', 400)
            
            # Find the response
            response = db.session.query(FormResponse).filter_by(
                id=response_id,
                form_id=form_id,
                user_id=user_id
            ).first()
            
            if not response:
                return _error('Response not found', 404)
            
            # Check visibility if expression exists
            if response.form.visibility_expression:
                if not VisibilityEvaluator.check_form_visibility(response.form, user_id, response.form.event_id):
                    return _error('You do not have permission to access this form', 403)
            
            # Cannot update submitted response unless the form allows edits
            if response.is_submitted and not response.form.allow_edits:
                return _error('Cannot update a submitted response', 400)

            # A submitted response stays submitted while it is edited. Silently
            # flipping is_submitted back to False here meant that saving a
            # draft - or the renderer's periodic autosave firing on its own -
            # turned an applicant's completed submission into a draft that
            # would be excluded from review, with nothing telling them so.
            # Withdrawal is the explicit way to retract a submission.

            # Update answers
            if 'answers' in args:
                valid_question_ids = _get_question_ids_for_form(form_id)
                for answer_data in args['answers']:
                    question_id = answer_data['question_id']
                    value = answer_data['value']

                    if question_id not in valid_question_ids:
                        return {
                            'error': 'Invalid question',
                            'message': f'Question {question_id} does not belong to this form'
                        }, 400

                    # Find existing answer
                    existing_answer = db.session.query(FormAnswer).filter_by(
                        response_id=response.id,
                        question_id=question_id,
                        is_active=True
                    ).first()

                    if existing_answer:
                        # Update existing
                        existing_answer.value = value
                        existing_answer.updated_on = datetime.now()
                    else:
                        # Create new
                        new_answer = FormAnswer(
                            response_id=response.id,
                            question_id=question_id,
                            value=value
                        )
                        db.session.add(new_answer)

            db.session.commit()
            return serialize_response(response), 200
            
        except Exception as e:
            LOGGER.error(f"Error updating response for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE
    
    @auth_required
    def get(self, form_id):
        """Get response(s) for current user"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            user_id = g.current_user['id']
            
            # Check visibility if expression exists
            if form.visibility_expression:
                if not VisibilityEvaluator.check_form_visibility(form, user_id, form.event_id):
                    return _error('You do not have permission to access this form', 403)
            
            if form.multiple_responses:
                # Return all responses for this user
                responses = db.session.query(FormResponse).filter_by(
                    form_id=form_id,
                    user_id=user_id
                ).order_by(FormResponse.started_timestamp.desc()).all()
                
                if not responses:
                    return {'responses': []}, 200
                
                return {
                    'responses': [serialize_response(r) for r in responses]
                }, 200
            else:
                # Return single response (latest unsubmitted or most recent)
                response = db.session.query(FormResponse).filter_by(
                    form_id=form_id,
                    user_id=user_id
                ).order_by(FormResponse.started_timestamp.desc()).first()
                
                if not response:
                    return {'message': 'Response not found'}, 404
                
                return serialize_response(response), 200
            
        except Exception as e:
            LOGGER.error(f"Error getting response for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class FormResponseSubmitAPI(restful.Resource):
    """Submit form response"""
    
    @auth_required
    def post(self, form_id, response_id):
        """Submit response"""
        try:
            response = db.session.query(FormResponse).filter_by(id=response_id).first()
            
            if not response:
                return {'message': 'Response not found'}, 404
            
            # Verify ownership
            if response.user_id != g.current_user['id']:
                return errors.UNAUTHORIZED
            
            # Verify form match
            if response.form_id != form_id:
                return {'message': 'Form ID mismatch'}, 400
            
            # Load the form
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return {'message': 'Form not found'}, 404

            if not form.is_open:
                return errors.APPLICATIONS_CLOSED

            if response.is_submitted and not form.allow_edits:
                return _error('This response has already been submitted', 400)

            # Server-side validation (backup to client validation)
            # Build answers dictionary for dependency evaluation
            answers_dict = {}
            for answer in response.answers:
                if answer.is_active and answer.question_id:
                    answers_dict[answer.question_id] = answer.value
            
            # Get user tags for tag-based visibility
            user_id = response.user_id
            user_tags = VisibilityEvaluator.get_user_tags_for_event(user_id, form.event_id)
            
            validation_errors = []
            # A blank answer row is not an answer. Without this an unticked
            # required checkbox (stored as the string 'false') and a cleared
            # text field both satisfied the required check just by having a row.
            answered_question_ids = {
                answer.question_id
                for answer in response.answers
                if answer.is_active and not answer.is_blank()
            }

            # Only validate answers for active and visible questions
            for section in form.sections:
                if not section.is_active:
                    continue
                
                # Check section visibility based on dependencies
                section_visible = True
                if section.dependency_expression:
                    section_visible = DependencyEvaluator.evaluate(
                        section.dependency_expression,
                        answers_dict
                    )
                
                # Check section visibility based on tags
                if section_visible and section.tag_expression:
                    section_visible = VisibilityEvaluator.evaluate(
                        section.tag_expression,
                        user_tags
                    )
                
                if not section_visible:
                    continue
                
                for question in section.questions:
                    if not question.is_active:
                        continue
                    
                    # Check question visibility based on dependencies
                    question_visible = True
                    if question.dependency_expression:
                        question_visible = DependencyEvaluator.evaluate(
                            question.dependency_expression,
                            answers_dict
                        )
                    
                    # Check question visibility based on tags
                    if question_visible and question.tag_expression:
                        question_visible = VisibilityEvaluator.evaluate(
                            question.tag_expression,
                            user_tags
                        )
                    
                    if not question_visible:
                        continue

                    # Display-only questions render no input, so they can never
                    # be answered and must not be treated as required.
                    if question.type in DISPLAY_ONLY_QUESTION_TYPES:
                        continue

                    # Check if required question is missing an answer
                    if question.is_required and question.id not in answered_question_ids:
                        validation_errors.append({
                            'question_id': question.id,
                            'error': ValidationError.REQUIRED.value
                        })
            
            # Validate existing answers (only for visible questions)
            for answer in response.answers:
                if not answer.is_active or not answer.question or not answer.question.is_active:
                    continue
                
                # Check if question's section is visible
                section = answer.question.section
                if section and section.dependency_expression:
                    section_visible = DependencyEvaluator.evaluate(
                        section.dependency_expression,
                        answers_dict
                    )
                    if not section_visible:
                        continue
                
                # Check section visibility based on tags
                if section and section.tag_expression:
                    section_visible = VisibilityEvaluator.evaluate(
                        section.tag_expression,
                        user_tags
                    )
                    if not section_visible:
                        continue
                
                # Check if question is visible
                if answer.question.dependency_expression:
                    question_visible = DependencyEvaluator.evaluate(
                        answer.question.dependency_expression,
                        answers_dict
                    )
                    if not question_visible:
                        continue
                
                # Check question visibility based on tags
                if answer.question.tag_expression:
                    question_visible = VisibilityEvaluator.evaluate(
                        answer.question.tag_expression,
                        user_tags
                    )
                    if not question_visible:
                        continue
                
                # Validate the answer
                is_valid, error = answer.validate(response.language)
                if not is_valid:
                    validation_errors.append({
                        'question_id': answer.question_id,
                        'error': error.value if error else 'unknown'
                    })
            
            if validation_errors:
                return {
                    'error': 'Validation failed',
                    'details': validation_errors
                }, 400
            
            # Mark as submitted
            response.is_submitted = True
            response.submitted_timestamp = datetime.now()
            db.session.commit()
            
            return serialize_response(response), 200
            
        except Exception as e:
            LOGGER.error(f"Error submitting response {response_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormResponseWithdrawAPI(restful.Resource):
    """Withdraw form response"""
    
    @auth_required
    def post(self, form_id, response_id):
        """Withdraw response"""
        try:
            response = db.session.query(FormResponse).filter_by(id=response_id).first()
            
            if not response:
                return {'message': 'Response not found'}, 404
            
            # Verify ownership
            if response.user_id != g.current_user['id']:
                return errors.UNAUTHORIZED
            
            # Verify form match
            if response.form_id != form_id:
                return {'message': 'Form ID mismatch'}, 400
            
            # Mark as withdrawn
            response.is_withdrawn = True
            response.withdrawn_timestamp = datetime.now()
            db.session.commit()
            
            return serialize_response(response), 200
            
        except Exception as e:
            LOGGER.error(f"Error withdrawing response {response_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


def _filtered_admin_response_query(form_id, args):
    """FormResponse+AppUser query for a form, with the admin list/export
    filters (is_submitted, is_withdrawn, user_id, email, name) from `args`
    (a request.args-like mapping) applied. Shared by FormResponseListAdminAPI
    and FormResponseExportAPI so the export always matches what the admin
    filtered the table to.
    """
    is_submitted = args.get('is_submitted')
    is_withdrawn = args.get('is_withdrawn')
    user_id = args.get('user_id')
    email_search = args.get('email')
    name_search = args.get('name')

    query = db.session.query(FormResponse, AppUser).join(
        AppUser, FormResponse.user_id == AppUser.id
    ).filter(FormResponse.form_id == form_id)

    if is_submitted:
        query = query.filter(FormResponse.is_submitted == (is_submitted.lower() == 'true'))

    if is_withdrawn:
        query = query.filter(FormResponse.is_withdrawn == (is_withdrawn.lower() == 'true'))

    if user_id:
        query = query.filter(FormResponse.user_id == int(user_id))

    if email_search:
        query = query.filter(AppUser.email.ilike(f'%{email_search}%'))

    if name_search:
        query = query.filter(
            db.or_(
                AppUser.firstname.ilike(f'%{name_search}%'),
                AppUser.lastname.ilike(f'%{name_search}%')
            )
        )

    return query.order_by(FormResponse.started_timestamp.desc())


class FormResponseListAdminAPI(restful.Resource):
    """Admin endpoint to list all responses for a form with pagination"""

    @event_admin_required
    def get(self, form_id, event_id):
        """Get paginated list of all responses for a form (admin only)"""
        try:
            # Verify form exists and belongs to the event the caller administers
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            if not verify_form_event(form, event_id):
                return errors.FORBIDDEN

            # Parse pagination parameters
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 25))
                if page < 1:
                    page = 1
                if per_page < 1:
                    per_page = 25
                if per_page > 10000:
                    per_page = 10000
            except ValueError:
                return errors.INVALID_INPUT_MALFORMED_PAGINATION

            query = _filtered_admin_response_query(form_id, request.args)

            # Paginate
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Serialize results with user information (without answers for efficiency)
            results = []
            for response, user in paginated.items:
                response_data = serialize_response_summary(response)
                response_data['user'] = {
                    'id': user.id,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                    'email': user.email,
                    'user_title': user.user_title
                }
                results.append(response_data)
            
            return {
                'pagination': {
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'total': paginated.total,
                    'pages': paginated.pages
                },
                'responses': results
            }, 200
            
        except Exception as e:
            LOGGER.error(f"Error getting responses for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


def _form_name(form, language):
    translations_by_language = {t.language: t for t in form.translations}
    translation = (
        translations_by_language.get(language)
        or translations_by_language.get('en')
        or next(iter(translations_by_language.values()), None)
    )
    return translation.name if translation else f'Form {form.id}'


def _build_export_columns(form, language):
    """Ordered [{question_id, header, options}] for every active,
    answerable question on `form`, used as the CSV/Sheet columns.

    Question translations are a lazy='dynamic' relationship, so looking one
    up per question would be a query per question on top of the per-response
    answer fetch; batching them into one query mirrors serialize_form.
    """
    questions = [
        question
        for section in form.sections if section.is_active
        for question in section.questions
        if question.is_active and question.type not in DISPLAY_ONLY_QUESTION_TYPES
    ]
    question_ids = [question.id for question in questions]

    translations_by_question = {}
    if question_ids:
        for translation in db.session.query(FormQuestionTranslation).filter(
            FormQuestionTranslation.form_question_id.in_(question_ids)
        ).all():
            translations_by_question.setdefault(
                translation.form_question_id, {}
            )[translation.language] = translation

    columns = []
    for question in questions:
        by_language = translations_by_question.get(question.id, {})
        translation = by_language.get(language) or by_language.get('en') or next(iter(by_language.values()), None)
        header = (translation.headline if translation else None) or question.key or f'Question {question.id}'
        options_by_value = {}
        if translation and translation.options:
            for option in translation.options:
                options_by_value[option.get('value')] = option.get('label', option.get('value'))
        columns.append({'question_id': question.id, 'header': header, 'options': options_by_value})
    return columns


def _format_export_answer(raw_value, options_by_value):
    """A stored answer value as export-ready text: choice questions render
    their option labels instead of the stored option value, and multi-value
    answers (MULTI_VALUE_SEPARATOR-joined in storage) render each part
    resolved the same way.
    """
    if raw_value is None:
        return ''
    parts = raw_value.split(MULTI_VALUE_SEPARATOR)
    return MULTI_VALUE_SEPARATOR.join(options_by_value.get(part, part) for part in parts)


def _build_export_row(response, user, columns, answers_by_response):
    if response.is_withdrawn:
        status = 'Withdrawn'
    elif response.is_submitted:
        status = 'Submitted'
    else:
        status = 'Draft'

    row = [
        f'{user.firstname} {user.lastname}'.strip(),
        user.email,
        status,
        response.started_timestamp.isoformat() if response.started_timestamp else '',
        response.submitted_timestamp.isoformat() if response.submitted_timestamp else '',
    ]
    answers = answers_by_response.get(response.id, {})
    for column in columns:
        row.append(_format_export_answer(answers.get(column['question_id']), column['options']))
    return row


class FormResponseExportAPI(restful.Resource):
    """Admin endpoint to export every question and answer across a form's
    responses as CSV or a freshly created, shared Google Sheet. Honours the
    same filters as FormResponseListAdminAPI, so an export matches whatever
    the admin currently has the response list filtered/searched to.
    """

    @event_admin_required
    def get(self, form_id, event_id):
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            if not verify_form_event(form, event_id):
                return errors.FORBIDDEN

            export_format = request.args.get('format', 'csv')
            if export_format not in ('csv', 'sheets'):
                return errors.INVALID_EXPORT_FORMAT

            language = request.args.get('language', 'en')

            rows = _filtered_admin_response_query(form_id, request.args).all()
            response_ids = [response.id for response, _ in rows]

            # .with_entities avoids instantiating a full FormAnswer ORM
            # object per row - a large form's answer count (questions x
            # responses) can run into the hundreds of thousands, where that
            # per-row object/state-tracking overhead is the dominant cost.
            answers_by_response = {}
            if response_ids:
                answer_rows = db.session.query(
                    FormAnswer.response_id, FormAnswer.question_id, FormAnswer.value
                ).filter(
                    FormAnswer.response_id.in_(response_ids),
                    FormAnswer.is_active == True
                )
                for response_id, question_id, value in answer_rows:
                    answers_by_response.setdefault(response_id, {})[question_id] = value

            columns = _build_export_columns(form, language)
            header = ['Name', 'Email', 'Status', 'Started', 'Submitted'] + \
                [column['header'] for column in columns]
            form_name = _form_name(form, language)

            if export_format == 'csv':
                def generate_csv():
                    # Written straight to the wire row by row rather than
                    # built up as one in-memory string - a large form's
                    # export can otherwise mean holding tens of MB of CSV
                    # text (more with long free-text answers) in one worker
                    # for the whole request before a single byte goes out.
                    buffer = io.StringIO()
                    writer = csv.writer(buffer)

                    writer.writerow(header)
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

                    for response, user in rows:
                        writer.writerow(_build_export_row(response, user, columns, answers_by_response))
                        yield buffer.getvalue()
                        buffer.seek(0)
                        buffer.truncate(0)

                filename = re.sub(r'[^A-Za-z0-9_-]+', '_', form_name).strip('_') or f'form-{form.id}'
                return Response(
                    stream_with_context(generate_csv()),
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}_responses.csv"'}
                )

            # Google Sheets export: create a new sheet under the app's service
            # account and share it with the requesting admin, rather than
            # returning file bytes. Unlike the CSV path, the Sheets API needs
            # the full row matrix up front to write it in row-range batches
            # (see create_spreadsheet), so there's no equivalent streaming win
            # available here.
            data_rows = [_build_export_row(response, user, columns, answers_by_response) for response, user in rows]
            requester = user_repository.get_by_id(g.current_user['id'])

            from config import GCP_DOCS_WORKING_FOLDER_ID
            from app.documents.google_client import build_default_client, GoogleApiError
            try:
                client = build_default_client(working_folder_id=GCP_DOCS_WORKING_FOLDER_ID)
                url = client.create_spreadsheet(
                    title=f'{form_name} Responses',
                    rows=[header] + data_rows,
                    share_with_email=requester.email,
                )
            except GoogleApiError as e:
                LOGGER.error(f"Error creating export spreadsheet for form {form_id}: {str(e)}")
                message = str(e) or errors.EXPORT_GOOGLE_SHEETS_FAILED[0]['message']
                return {'message': message}, 502

            return {'url': url}, 200

        except Exception as e:
            LOGGER.error(f"Error exporting responses for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class FormResponseDetailAdminAPI(restful.Resource):
    """Admin endpoint to retrieve full details of a single response"""
    
    @event_admin_required
    def get(self, form_id, response_id, event_id):
        """Get detailed response including answers and linked response (admin only)"""
        try:
            # Verify form exists and belongs to the event the caller administers
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            if not verify_form_event(form, event_id):
                return errors.FORBIDDEN

            # Get response with user information
            result = db.session.query(FormResponse, AppUser).join(
                AppUser, FormResponse.user_id == AppUser.id
            ).filter(
                FormResponse.id == response_id,
                FormResponse.form_id == form_id
            ).first()
            
            if not result:
                return _error('Response not found', 404)
            
            response, user = result
            
            # Serialize with full details including linked response
            response_data = serialize_response_with_linked(response)
            
            # Add user information
            response_data['user'] = {
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'user_title': user.user_title
            }
            
            # Add linked response user information if linked response exists
            if response_data['linked_response'] and response.linked_response:
                linked_user = db.session.query(AppUser).filter_by(
                    id=response.linked_response.user_id
                ).first()
                if linked_user:
                    response_data['linked_response']['user'] = {
                        'id': linked_user.id,
                        'firstname': linked_user.firstname,
                        'lastname': linked_user.lastname,
                        'email': linked_user.email,
                        'user_title': linked_user.user_title
                    }
            
            return response_data, 200
            
        except Exception as e:
            LOGGER.error(f"Error getting response detail {response_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class EventFormConfigAPI(restful.Resource):
    """Returns form system configuration for all form types for an event."""

    @event_admin_required
    def get(self, event_id):
        """Get form system config for all types (old vs new, form IDs, stages)."""
        try:
            # --- Application ---
            new_app_form = db.session.query(Form).filter_by(
                event_id=event_id, form_type='application'
            ).first()

            if new_app_form:
                response_count = db.session.query(FormResponse).filter_by(
                    form_id=new_app_form.id, is_submitted=True
                ).count()
                name_trans = new_app_form.get_translation('en')
                application_data = {
                    'system': 'new',
                    'form_id': new_app_form.id,
                    'form_name': name_trans.name if name_trans else None,
                    'is_open': new_app_form.is_open,
                    'is_active': new_app_form.is_active,
                    'response_count': response_count
                }
            else:
                legacy_app_form = db.session.query(ApplicationForm).filter_by(
                    event_id=event_id
                ).first()
                application_data = {
                    'system': 'old',
                    'form_id': None,
                    'legacy_form_id': legacy_app_form.id if legacy_app_form else None
                }

            # --- Review ---
            new_review_forms = db.session.query(Form).filter_by(
                event_id=event_id, form_type='review'
            ).order_by(Form.stage).all()

            if new_review_forms:
                stages_data = []
                for review_form in new_review_forms:
                    settings = review_form.settings or {}
                    num_reviews_required = settings.get('num_reviews_required', 3)
                    total_assignments = db.session.query(FormResponse).filter_by(
                        form_id=review_form.id
                    ).count()
                    completed_assignments = db.session.query(FormResponse).filter_by(
                        form_id=review_form.id, is_submitted=True
                    ).count()
                    name_trans = review_form.get_translation('en')
                    stages_data.append({
                        'stage': review_form.stage,
                        'form_id': review_form.id,
                        'form_name': name_trans.name if name_trans else None,
                        'is_active': review_form.is_active,
                        'num_reviews_required': num_reviews_required,
                        'completed_count': completed_assignments,
                        'total_count': total_assignments
                    })
                review_data = {'system': 'new', 'stages': stages_data}
            else:
                legacy_app = db.session.query(ApplicationForm).filter_by(
                    event_id=event_id
                ).first()
                legacy_review_form = None
                if legacy_app:
                    legacy_review_form = db.session.query(ReviewForm).filter_by(
                        application_form_id=legacy_app.id
                    ).first()
                review_data = {
                    'system': 'old',
                    'legacy_form_id': legacy_review_form.id if legacy_review_form else None
                }

            # --- Registration ---
            new_reg_form = db.session.query(Form).filter_by(
                event_id=event_id, form_type='registration'
            ).first()

            if new_reg_form:
                response_count = db.session.query(FormResponse).filter_by(
                    form_id=new_reg_form.id, is_submitted=True
                ).count()
                name_trans = new_reg_form.get_translation('en')
                registration_data = {
                    'system': 'new',
                    'form_id': new_reg_form.id,
                    'form_name': name_trans.name if name_trans else None,
                    'is_open': new_reg_form.is_open,
                    'is_active': new_reg_form.is_active,
                    'response_count': response_count
                }
            else:
                legacy_reg_form = db.session.query(RegistrationForm).filter_by(
                    event_id=event_id
                ).first()
                registration_data = {
                    'system': 'old',
                    'form_id': None,
                    'legacy_form_id': legacy_reg_form.id if legacy_reg_form else None
                }

            # --- Generic Forms (form_type=NULL) ---
            generic_forms = db.session.query(Form).filter(
                Form.event_id == event_id,
                Form.form_type == None
            ).order_by(Form.created_at.desc()).all()

            generic_forms_data = []
            for gf in generic_forms:
                name_trans = gf.get_translation('en')
                response_count = db.session.query(FormResponse).filter_by(
                    form_id=gf.id
                ).count()
                generic_forms_data.append({
                    'id': gf.id,
                    'name': name_trans.name if name_trans else None,
                    'is_active': gf.is_active,
                    'response_count': response_count
                })

            # --- Survey ---
            event = event_repository.get_by_id(event_id)
            survey_data = None
            if event and (event.survey_form_id or event.survey_open):
                survey_form_name = None
                if event.survey_form_id:
                    survey_form = db.session.query(Form).filter_by(id=event.survey_form_id).first()
                    if survey_form:
                        name_trans = survey_form.get_translation('en')
                        survey_form_name = name_trans.name if name_trans else None
                survey_data = {
                    'form_id': event.survey_form_id,
                    'form_name': survey_form_name,
                    'survey_open': event.survey_open.strftime('%Y-%m-%dT%H:%M:%S') if event.survey_open is not None else None
                }

            return {
                'application': application_data,
                'review': review_data,
                'registration': registration_data,
                'generic_forms': generic_forms_data,
                'survey': survey_data
            }, 200

        except Exception as e:
            LOGGER.error(f"Error getting form config for event {event_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class EventSurveyFormAPI(restful.Resource):
    """Assigns an existing Form as an event's post-event survey, and when it opens."""

    @event_admin_required
    def put(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('form_id', type=int, required=False)
        req_parser.add_argument('survey_open', type=str, required=False)
        args = req_parser.parse_args()

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        form_id = args['form_id']
        if form_id is not None:
            form = db.session.query(Form).filter_by(id=form_id, event_id=event_id).first()
            if not form:
                return errors.FORM_NOT_FOUND_BY_ID

        survey_open = None
        if args['survey_open']:
            try:
                survey_open = datetime.strptime(args['survey_open'], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                try:
                    survey_open = datetime.strptime(args['survey_open'], '%Y-%m-%dT%H:%M')
                except ValueError:
                    return errors.INVALID_SURVEY_OPEN

        event.set_survey_form_id(form_id)
        event.set_survey_open(survey_open)
        db.session.commit()

        return {
            'survey_form_id': event.survey_form_id,
            'survey_open': event.survey_open.strftime('%Y-%m-%dT%H:%M:%S') if event.survey_open is not None else None
        }, 200


class FormReviewAssignmentAPI(restful.Resource):
    """
    Manage review assignments for new-style review forms.

    A review assignment is simply a FormResponse (with no answers yet) on the
    review Form whose linked_response_id points to the applicant's FormResponse.
    This avoids any new model: assignment = pre-created unfilled FormResponse.
    """

    @event_admin_required
    def get(self, form_id, event_id):
        """Return per-reviewer allocation and completion counts, with reviewer tags."""
        try:
            # event_id is scoped into the lookup so an admin of another event
            # cannot address this event's review form.
            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review', event_id=event_id
            ).first()
            if not review_form:
                return errors.FORM_NOT_FOUND

            rows = (
                db.session.query(
                    AppUser,
                    db.func.count(FormResponse.id).label('reviews_allocated'),
                    db.func.sum(
                        db.case([(FormResponse.is_submitted == True, 1)], else_=0)
                    ).label('reviews_completed')
                )
                .join(FormResponse, FormResponse.user_id == AppUser.id)
                .filter(
                    FormResponse.form_id == form_id,
                    FormResponse.is_withdrawn == False
                )
                .group_by(AppUser.id)
                .all()
            )

            # Load all reviewer tags for this event once to avoid N+1 queries
            reviewer_tags = db.session.query(ReviewerTag).filter_by(
                event_id=event_id
            ).all()

            def _tags_for_reviewer(reviewer_user_id):
                language = 'en'
                result = []
                for rt in reviewer_tags:
                    if rt.reviewer_user_id != reviewer_user_id:
                        continue
                    translation = rt.tag.get_translation(language)
                    if translation is None:
                        translation = rt.tag.get_translation('en')
                    result.append({
                        'id': rt.tag_id,
                        'name': translation.name if translation else '',
                        'description': translation.description if translation else ''
                    })
                return result

            result = []
            for user, allocated, completed in rows:
                result.append({
                    'reviewer_user_id': user.id,
                    'email': user.email,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                    'user_title': user.user_title,
                    'reviews_allocated': allocated,
                    'reviews_completed': int(completed) if completed else 0,
                    'tags': _tags_for_reviewer(user.id)
                })
            return result, 200

        except Exception as e:
            LOGGER.error('Error getting review assignments for form {}: {}'.format(form_id, str(e)))
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def post(self, form_id, event_id):
        """Assign N reviews to a reviewer, optionally filtered by response tags."""
        try:
            args = request.get_json()
            reviewer_user_email = args.get('reviewer_user_email')
            num_reviews = args.get('num_reviews', 0)
            tag_ids = args.get('tag_ids') or []

            # event_id is scoped into the lookup so an admin of another event
            # cannot address this event's review form.
            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review', event_id=event_id
            ).first()
            if not review_form:
                return errors.FORM_NOT_FOUND

            if not review_form.linked_form_id:
                return _error('Review form has no linked application form', 400)

            reviewer = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
            if reviewer is None:
                return errors.USER_NOT_FOUND

            reviewer_id = reviewer.id
            reviewer_email = reviewer.email

            # Ensure the user has the reviewer event role (required for ReviewerTagAPI)
            existing_role = db.session.query(EventRole).filter_by(
                role='reviewer', user_id=reviewer_id, event_id=event_id
            ).first()
            if not existing_role:
                db.session.add(EventRole('reviewer', reviewer_id, event_id))

            num_reviews_required = (review_form.settings or {}).get('num_reviews_required', 1)

            # Merge explicitly requested tags with the reviewer's own tags
            reviewer_tags = db.session.query(ReviewerTag).filter_by(
                event_id=event_id, reviewer_user_id=reviewer_id
            ).all()
            reviewer_tag_ids = [rt.tag_id for rt in reviewer_tags]
            filter_tag_ids = list(set(tag_ids) | set(reviewer_tag_ids))

            # All submitted, non-withdrawn application responses excluding the reviewer's own
            candidate_app_responses = db.session.query(FormResponse).filter(
                FormResponse.form_id == review_form.linked_form_id,
                FormResponse.is_submitted == True,
                FormResponse.is_withdrawn == False,
                FormResponse.user_id != reviewer_id
            ).all()

            # Apply tag filtering: response must have ALL selected tags
            if filter_tag_ids:
                filtered = []
                for resp in candidate_app_responses:
                    resp_tag_ids = [rt.tag_id for rt in resp.response_tags]
                    if all(t in resp_tag_ids for t in filter_tag_ids):
                        filtered.append(resp)
                candidate_app_responses = filtered

            # Responses already at the required reviewer count
            fully_assigned_ids = set(
                row[0]
                for row in db.session.query(FormResponse.linked_response_id)
                .filter(
                    FormResponse.form_id == form_id,
                    FormResponse.is_withdrawn == False
                )
                .group_by(FormResponse.linked_response_id)
                .having(db.func.count(FormResponse.id) >= num_reviews_required)
                .all()
            )

            # Responses already assigned to this reviewer
            already_assigned_ids = set(
                row[0]
                for row in db.session.query(FormResponse.linked_response_id)
                .filter(
                    FormResponse.form_id == form_id,
                    FormResponse.user_id == reviewer_id,
                    FormResponse.is_withdrawn == False
                )
                .all()
            )

            eligible_ids = [
                r.id for r in candidate_app_responses
                if r.id not in fully_assigned_ids and r.id not in already_assigned_ids
            ]

            # Clamp: a negative num_reviews made random.sample raise, which the
            # blanket handler then reported as a database error.
            try:
                num_reviews = max(0, int(num_reviews))
            except (TypeError, ValueError):
                return _error('num_reviews must be a number', 400)

            to_assign = random.sample(eligible_ids, min(len(eligible_ids), num_reviews))

            for app_response_id in to_assign:
                assignment = FormResponse(
                    form_id=form_id,
                    user_id=reviewer_id,
                    linked_response_id=app_response_id
                )
                db.session.add(assignment)

            db.session.commit()

            if len(to_assign) > 0:
                event = event_repository.get_by_id(event_id)
                reviewer = user_repository.get_by_email(reviewer_email, g.organisation.id)
                email_user(
                    'reviews-assigned',
                    template_parameters=dict(
                        num_reviews=len(to_assign),
                        baobab_host=misc.get_baobab_host(),
                        system_name=g.organisation.system_name,
                        event_key=event.key
                    ),
                    event=event,
                    user=reviewer
                )

            return {'reviews_assigned': len(to_assign)}, 201

        except Exception as e:
            LOGGER.error('Error assigning reviews for form {}: {}'.format(form_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def delete(self, form_id, event_id):
        """Remove up to N unstarted (no answers) review assignments, optionally filtered by tags."""
        try:
            args = request.get_json()
            reviewer_user_email = args.get('reviewer_user_email')
            num_reviews = args.get('num_reviews', 0)
            tag_ids = args.get('tag_ids') or []

            # event_id is scoped into the lookup so an admin of another event
            # cannot address this event's review form.
            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review', event_id=event_id
            ).first()
            if not review_form:
                return errors.FORM_NOT_FOUND

            reviewer = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
            if reviewer is None:
                return errors.USER_NOT_FOUND

            # Unstarted = not submitted and has no answers
            unstarted = (
                db.session.query(FormResponse)
                .filter(
                    FormResponse.form_id == form_id,
                    FormResponse.user_id == reviewer.id,
                    FormResponse.is_submitted == False,
                    FormResponse.is_withdrawn == False
                )
                .all()
            )
            unstarted = [r for r in unstarted if len(r.answers) == 0]

            # Apply tag filter: only remove assignments whose linked response has all selected tags
            if tag_ids:
                def _has_all_tags(assignment):
                    if not assignment.linked_response_id:
                        return False
                    linked = db.session.query(FormResponse).get(assignment.linked_response_id)
                    if not linked:
                        return False
                    resp_tag_ids = [rt.tag_id for rt in linked.response_tags]
                    return all(t in resp_tag_ids for t in tag_ids)
                unstarted = [r for r in unstarted if _has_all_tags(r)]

            # Guard before the loop: a post-increment check here would delete one
            # assignment even when num_reviews is 0.
            try:
                num_reviews = int(num_reviews)
            except (TypeError, ValueError):
                return _error('num_reviews must be a number', 400)
            if num_reviews <= 0:
                return {'num_deleted': 0}, 200

            counter = 0
            for response in unstarted:
                if counter >= num_reviews:
                    break
                db.session.delete(response)
                counter += 1

            db.session.commit()
            return {'num_deleted': counter}, 200

        except Exception as e:
            LOGGER.error('Error removing review assignments for form {}: {}'.format(form_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormResponseTagAPI(restful.Resource):
    """Add or remove tags from a FormResponse (application response)."""

    @event_admin_required
    def post(self, form_id, response_id, event_id):
        """Add a tag to a FormResponse."""
        try:
            args = request.get_json()
            tag_id = args.get('tag_id')
            if not tag_id:
                return _error('tag_id is required', 400)

            form_response = _get_response_for_event(response_id, form_id, event_id)
            if not form_response:
                return errors.OBJECT_NOT_FOUND

            tag = tag_repository.get_by_id(tag_id)
            if not tag:
                return errors.TAG_NOT_FOUND
            if tag.event_id != event_id:
                return errors.FORBIDDEN

            existing = db.session.query(FormResponseTag).filter_by(
                form_response_id=response_id, tag_id=tag_id
            ).first()
            if existing:
                return _error('Tag already applied to this response', 400)

            frt = FormResponseTag(form_response_id=response_id, tag_id=tag_id)
            db.session.add(frt)
            db.session.commit()

            translation = tag.get_translation('en')
            return {
                'id': frt.id,
                'form_response_id': frt.form_response_id,
                'tag_id': frt.tag_id,
                'name': translation.name if translation else '',
                'description': translation.description if translation else ''
            }, 201

        except Exception as e:
            LOGGER.error('Error adding tag to form response {}: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def delete(self, form_id, response_id, event_id):
        """Remove a tag from a FormResponse."""
        try:
            args = request.get_json()
            tag_id = args.get('tag_id')
            if not tag_id:
                return _error('tag_id is required', 400)

            if not _get_response_for_event(response_id, form_id, event_id):
                return errors.OBJECT_NOT_FOUND

            frt = db.session.query(FormResponseTag).filter_by(
                form_response_id=response_id, tag_id=tag_id
            ).first()
            if not frt:
                return errors.OBJECT_NOT_FOUND

            db.session.delete(frt)
            db.session.commit()
            return {}, 200

        except Exception as e:
            LOGGER.error('Error removing tag from form response {}: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormResponseAdminUpdateAPI(restful.Resource):
    """Admin endpoint to update response status (submit/withdraw/unsubmit/unwithdraw)."""

    @event_admin_required
    def patch(self, form_id, response_id, event_id):
        try:
            response = _get_response_for_event(response_id, form_id, event_id)
            if not response:
                return _error('Response not found', 404)

            args = request.get_json() or {}

            if 'is_submitted' in args:
                response.is_submitted = bool(args['is_submitted'])
                if response.is_submitted and not response.submitted_timestamp:
                    response.submitted_timestamp = datetime.now()
                elif not response.is_submitted:
                    response.submitted_timestamp = None

            if 'is_withdrawn' in args:
                response.is_withdrawn = bool(args['is_withdrawn'])
                if response.is_withdrawn and not response.withdrawn_timestamp:
                    response.withdrawn_timestamp = datetime.now()
                elif not response.is_withdrawn:
                    response.withdrawn_timestamp = None

            db.session.commit()
            return serialize_response(response), 200

        except Exception as e:
            LOGGER.error('Error updating response {} status: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormResponseReviewsAdminAPI(restful.Resource):
    """Admin endpoints to list, assign, and remove reviewers for a specific application response."""

    def _get_review_form(self, form_id, event_id):
        return db.session.query(Form).filter_by(
            linked_form_id=form_id,
            form_type='review',
            event_id=event_id
        ).first()

    @event_admin_required
    def get(self, form_id, response_id, event_id):
        """List all review assignments (reviewer + status) for an application response."""
        try:
            review_form = self._get_review_form(form_id, event_id)
            if not review_form:
                return [], 200

            rows = (
                db.session.query(FormResponse, AppUser)
                .join(AppUser, FormResponse.user_id == AppUser.id)
                .filter(
                    FormResponse.form_id == review_form.id,
                    FormResponse.linked_response_id == response_id,
                    FormResponse.is_withdrawn == False
                )
                .all()
            )

            return [
                {
                    'review_response_id': rr.id,
                    'reviewer_user_id': reviewer.id,
                    'user_title': reviewer.user_title,
                    'firstname': reviewer.firstname,
                    'lastname': reviewer.lastname,
                    'email': reviewer.email,
                    'is_submitted': rr.is_submitted,
                    'submitted_timestamp': rr.submitted_timestamp.isoformat() if rr.submitted_timestamp else None
                }
                for rr, reviewer in rows
            ], 200

        except Exception as e:
            LOGGER.error('Error getting reviews for response {}: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def post(self, form_id, response_id, event_id):
        """Assign a reviewer to an application response by email."""
        try:
            args = request.get_json() or {}
            reviewer_email = args.get('reviewer_email', '').strip()
            if not reviewer_email:
                return _error('reviewer_email is required', 400)

            reviewer = db.session.query(AppUser).filter(
                db.func.lower(AppUser.email) == reviewer_email.lower()
            ).first()
            if not reviewer:
                return _error('No user found with that email address', 404)

            review_form = self._get_review_form(form_id, event_id)
            if not review_form:
                return _error('No review form is configured for this event', 404)

            existing = db.session.query(FormResponse).filter_by(
                form_id=review_form.id,
                user_id=reviewer.id,
                linked_response_id=response_id
            ).first()
            if existing and not existing.is_withdrawn:
                return _error('This reviewer is already assigned', 400)

            review_response = FormResponse(
                form_id=review_form.id,
                user_id=reviewer.id,
                language='en',
                linked_response_id=response_id
            )
            db.session.add(review_response)
            db.session.commit()

            return {
                'review_response_id': review_response.id,
                'reviewer_user_id': reviewer.id,
                'user_title': reviewer.user_title,
                'firstname': reviewer.firstname,
                'lastname': reviewer.lastname,
                'email': reviewer.email,
                'is_submitted': False,
                'submitted_timestamp': None
            }, 201

        except Exception as e:
            LOGGER.error('Error assigning reviewer to response {}: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def delete(self, form_id, response_id, event_id):
        """Remove a not-yet-submitted reviewer assignment."""
        try:
            args = request.get_json() or {}
            reviewer_user_id = args.get('reviewer_user_id')
            if not reviewer_user_id:
                return _error('reviewer_user_id is required', 400)

            review_form = self._get_review_form(form_id, event_id)
            if not review_form:
                return errors.FORM_NOT_FOUND

            review_response = db.session.query(FormResponse).filter_by(
                form_id=review_form.id,
                user_id=reviewer_user_id,
                linked_response_id=response_id
            ).first()
            if not review_response:
                return errors.OBJECT_NOT_FOUND

            if review_response.is_submitted:
                return _error('Cannot remove a reviewer who has already submitted their review', 400)

            db.session.delete(review_response)
            db.session.commit()
            return {}, 200

        except Exception as e:
            LOGGER.error('Error removing reviewer from response {}: {}'.format(response_id, str(e)))
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE


class FormReviewSummaryAPI(restful.Resource):
    """Count unallocated reviews for a new-style review form, optionally filtered by response tags."""

    @event_admin_required
    def get(self, form_id, event_id):
        try:
            # event_id is scoped into the lookup so an admin of another event
            # cannot address this event's review form.
            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review', event_id=event_id
            ).first()
            if not review_form:
                return errors.FORM_NOT_FOUND

            if not review_form.linked_form_id:
                return {'reviews_unallocated': 0}, 200

            from flask_restful import reqparse as rp
            parser = rp.RequestParser()
            parser.add_argument('tags[]', type=int, action='append', location='args')
            args = parser.parse_args()
            tag_ids = args['tags[]'] or []

            num_reviews_required = (review_form.settings or {}).get('num_reviews_required', 1)

            # All submitted app responses for the linked form
            app_responses = db.session.query(FormResponse).filter(
                FormResponse.form_id == review_form.linked_form_id,
                FormResponse.is_submitted == True,
                FormResponse.is_withdrawn == False
            ).all()

            # Apply tag filter
            if tag_ids:
                filtered = []
                for resp in app_responses:
                    resp_tag_ids = [rt.tag_id for rt in resp.response_tags]
                    if all(t in resp_tag_ids for t in tag_ids):
                        filtered.append(resp)
                app_responses = filtered

            app_response_ids = [r.id for r in app_responses]

            if not app_response_ids:
                return {'reviews_unallocated': 0}, 200

            # Count existing active review assignments per app response
            assignment_counts = dict(
                db.session.query(
                    FormResponse.linked_response_id,
                    db.func.count(FormResponse.id)
                )
                .filter(
                    FormResponse.form_id == form_id,
                    FormResponse.linked_response_id.in_(app_response_ids),
                    FormResponse.is_withdrawn == False
                )
                .group_by(FormResponse.linked_response_id)
                .all()
            )

            total_required = len(app_response_ids) * num_reviews_required
            assigned = sum(
                min(assignment_counts.get(rid, 0), num_reviews_required)
                for rid in app_response_ids
            )

            return {'reviews_unallocated': total_required - assigned}, 200

        except Exception as e:
            LOGGER.error('Error getting review summary for form {}: {}'.format(form_id, str(e)))
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE
