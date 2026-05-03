from datetime import datetime
import traceback
import random

import flask_restful as restful
from flask import g, request

from app.forms.models import (
    Form, FormResponse, FormAnswer, FormSection, FormQuestion,
    FormTranslation, FormSectionTranslation, FormQuestionTranslation,
    DependencyEvaluator
)
from app.forms.visibility import VisibilityEvaluator
from app.forms.mixins import (
    uses_new_form, get_form_by_type,
    apply_form_type_defaults, validate_form_type_constraints
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
from app.reviews.models import ReviewForm


def serialize_form(form, language='en', include_inactive=False):
    """Serialize a form with all sections and questions with all translations
    
    Args:
        form: Form object to serialize
        language: Language code (deprecated, kept for compatibility - now returns all languages)
        include_inactive: If True, include inactive sections/questions (for admin audit)
    """
    sections_data = []
    
    for section in form.sections:
        if not include_inactive and not section.is_active:
            continue
            
        # Get all translations for this section
        section_translations_dict = {}
        for translation in section.translations:
            section_translations_dict[translation.language] = translation
        
        questions_data = []
        for question in section.questions:
            if not include_inactive and not question.is_active:
                continue
            
            # Get all translations for this question
            question_translations_dict = {}
            for translation in question.translations:
                question_translations_dict[translation.language] = translation
            
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
        'answers': answers_data
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
    
    @auth_required
    def get(self):
        """Get list of forms"""
        try:
            user_id = g.current_user['id']
            language = request.args.get('language', 'en')
            
            # Build query
            query = db.session.query(Form)
            
            # Filter by active status if specified
            is_active = request.args.get('is_active')
            if is_active is not None:
                query = query.filter_by(is_active=is_active.lower() == 'true')
            
            # Filter by open status if specified
            is_open = request.args.get('is_open')
            if is_open is not None:
                query = query.filter_by(is_open=is_open.lower() == 'true')
            
            # Filter by event_id
            event_id = request.args.get('event_id')
            if event_id:
                query = query.filter_by(event_id=int(event_id))
            
            # Filter by created_by if specified (admin feature)
            created_by = request.args.get('created_by')
            if created_by:
                query = query.filter_by(created_by_user_id=created_by)
            
            forms = query.order_by(Form.created_at.desc()).all()
            
            # Serialize forms
            forms_data = []
            for form in forms:
                forms_data.append(serialize_form(form, language))
            
            return forms_data, 200
            
        except Exception as e:
            LOGGER.error(f"Error getting forms list: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE
    
    @auth_required
    def post(self):
        """Create a new empty form (use FormStructureAPI to add sections/questions)"""
        try:
            args = request.get_json()
            user_id = g.current_user['id']
            
            event_id = args.get('event_id')
            if not event_id:
                return {'error': 'event_id is required'}, 400
            
            form_type = args.get('form_type')
            stage = args.get('stage')

            # Validate form type constraints before creating
            if form_type:
                constraint_error = validate_form_type_constraints(event_id, form_type)
                if constraint_error:
                    return {'error': constraint_error}, 400

            # Create empty form
            form = Form(
                event_id=event_id,
                created_by_user_id=user_id,
                is_open=args.get('is_open', False),
                is_active=args.get('is_active', True),
                linked_form_id=args.get('linked_form_id'),
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
    
    @auth_required
    def get(self, form_id):
        """Get form definition"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            # Check visibility if expression exists
            if form.visibility_expression:
                user_id = g.current_user['id']
                if not VisibilityEvaluator.check_form_visibility(form, user_id, form.event_id):
                    return {'error': 'You do not have permission to access this form'}, 403
            
            language = request.args.get('language', 'en')
            return serialize_form(form, language), 200
            
        except Exception as e:
            LOGGER.error(f"Error getting form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE
    
    @auth_required
    def put(self, form_id):
        """Update form definition"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
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
    
    @auth_required
    def delete(self, form_id):
        """Soft delete form"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            form.is_active = False
            form.updated_at = datetime.now()
            db.session.commit()
            
            return {}, 204
            
        except Exception as e:
            LOGGER.error(f"Error deleting form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class FormStructureAPI(restful.Resource):
    """Manage form structure - sections and questions"""
    
    @auth_required
    def get(self, form_id):
        """Get form structure with version info"""
        try:
            db.session.expire_all()  # Clear any cached objects
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            language = request.args.get('language', 'en')
            # Optionally include inactive items for admin audit
            include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
            return serialize_form(form, language, include_inactive=include_inactive), 200
            
        except Exception as e:
            LOGGER.error(f"Error getting form structure {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE
    
    @auth_required
    def put(self, form_id):
        """Update form structure (sections and questions) with soft delete support"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
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
            
            # Process sections
            for section_data in sections_data:
                if 'id' in section_data:
                    # Update existing section
                    section = db.session.query(FormSection).filter_by(
                        id=section_data['id'],
                        form_id=form_id
                    ).first()
                    
                    if not section:
                        return {'error': f"Section {section_data['id']} not found"}, 404
                    
                    # Reactivate if it was previously soft deleted
                    if not section.is_active and section_data.get('is_active', True):
                        section.is_active = True
                        section.version += 1
                    
                    section.order = section_data.get('order', section.order)
                    section.key = section_data.get('key', section.key)
                    section.dependency_expression = section_data.get('dependency_expression', section.dependency_expression)
                    section.updated_at = datetime.now()
                    
                    # Update translations
                    for lang, name in section_data.get('name', {}).items():
                        trans = section.translations.filter_by(language=lang).first()
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
                        key=section_data.get('key'),
                        dependency_expression=section_data.get('dependency_expression')
                    )
                    db.session.add(section)
                    db.session.flush()
                    
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
                        # Update existing question
                        question = db.session.query(FormQuestion).filter_by(
                            id=question_data['id'],
                            form_id=form_id
                        ).first()
                        
                        if not question:
                            return {'error': f"Question {question_data['id']} not found"}, 404
                        
                        # Reactivate if it was previously soft deleted
                        if not question.is_active and question_data.get('is_active', True):
                            question.is_active = True
                            question.version += 1
                        
                        question.section_id = section.id
                        question.order = question_data.get('order', question.order)
                        question.type = question_data.get('type', question.type)
                        question.is_required = question_data.get('is_required', question.is_required)
                        question.key = question_data.get('key', question.key)
                        question.settings = question_data.get('settings', question.settings)
                        question.dependency_expression = question_data.get('dependency_expression', question.dependency_expression)
                        question.linked_question_id = question_data.get('linked_question_id', question.linked_question_id)
                        question.updated_at = datetime.now()
                        
                        # Update translations
                        for lang, headline in question_data.get('headline', {}).items():
                            trans = question.translations.filter_by(language=lang).first()
                            if trans:
                                trans.headline = headline
                                trans.description = question_data.get('description', {}).get(lang, trans.description)
                                trans.placeholder = question_data.get('placeholder', {}).get(lang, trans.placeholder)
                                trans.validation_regex = question_data.get('validation_regex', {}).get(lang, trans.validation_regex)
                                trans.validation_text = question_data.get('validation_text', {}).get(lang, trans.validation_text)
                                trans.options = question_data.get('options', {}).get(lang, trans.options)
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
                            key=question_data.get('key'),
                            settings=question_data.get('settings'),
                            dependency_expression=question_data.get('dependency_expression'),
                            linked_question_id=question_data.get('linked_question_id')
                        )
                        db.session.add(question)
                        db.session.flush()
                        
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
                    return {'error': 'You do not have permission to access this form'}, 403
            
            linked_response_id = args.get('linked_response_id')

            # Check if multiple_responses is allowed
            if not form.multiple_responses:
                # Check if user already has an unsubmitted response
                existing_response = db.session.query(FormResponse).filter_by(
                    form_id=form_id,
                    user_id=user_id,
                    is_submitted=False
                ).first()
                
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
                for answer_data in args['answers']:
                    question_id = answer_data['question_id']
                    value = answer_data['value']
                    
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
                return {'error': 'response_id is required'}, 400
            
            # Find the response
            response = db.session.query(FormResponse).filter_by(
                id=response_id,
                form_id=form_id,
                user_id=user_id
            ).first()
            
            if not response:
                return {'error': 'Response not found'}, 404
            
            # Check visibility if expression exists
            if response.form.visibility_expression:
                if not VisibilityEvaluator.check_form_visibility(response.form, user_id, response.form.event_id):
                    return {'error': 'You do not have permission to access this form'}, 403
            
            # Cannot update submitted response
            if response.is_submitted:
                return {'error': 'Cannot update a submitted response'}, 400
            
            # Update answers
            if 'answers' in args:
                for answer_data in args['answers']:
                    question_id = answer_data['question_id']
                    value = answer_data['value']
                    
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
                    return {'error': 'You do not have permission to access this form'}, 403
            
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
            answered_question_ids = {answer.question_id for answer in response.answers if answer.is_active}
            
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
                    
                    # Check if required question is missing an answer
                    if question.is_required and question.id not in answered_question_ids:
                        validation_errors.append({
                            'question_id': question.id,
                            'error': 'REQUIRED'
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


class FormResponseListAdminAPI(restful.Resource):
    """Admin endpoint to list all responses for a form with pagination"""
    
    @event_admin_required
    def get(self, form_id, event_id):
        """Get paginated list of all responses for a form (admin only)"""
        try:
            # Verify form exists
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
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
            
            # Parse filter parameters
            is_submitted = request.args.get('is_submitted')
            is_withdrawn = request.args.get('is_withdrawn')
            user_id = request.args.get('user_id')
            email_search = request.args.get('email')
            name_search = request.args.get('name')
            
            # Build query with user join for user information
            query = db.session.query(FormResponse, AppUser).join(
                AppUser, FormResponse.user_id == AppUser.id
            ).filter(FormResponse.form_id == form_id)
            
            # Apply filters
            if is_submitted:
                query = query.filter(FormResponse.is_submitted == (is_submitted.lower() == 'true'))
            
            if is_withdrawn:
                query = query.filter(FormResponse.is_withdrawn == (is_withdrawn.lower() == 'true'))
            
            if user_id:
                query = query.filter(FormResponse.user_id == int(user_id))
            
            # Search by email (case-insensitive partial match)
            if email_search:
                query = query.filter(AppUser.email.ilike(f'%{email_search}%'))
            
            # Search by name (case-insensitive partial match on firstname or lastname)
            if name_search:
                query = query.filter(
                    db.or_(
                        AppUser.firstname.ilike(f'%{name_search}%'),
                        AppUser.lastname.ilike(f'%{name_search}%')
                    )
                )
            
            # Order by most recent first
            query = query.order_by(FormResponse.started_timestamp.desc())
            
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


class FormResponseDetailAdminAPI(restful.Resource):
    """Admin endpoint to retrieve full details of a single response"""
    
    @event_admin_required
    def get(self, form_id, response_id, event_id):
        """Get detailed response including answers and linked response (admin only)"""
        try:
            # Verify form exists
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            # Get response with user information
            result = db.session.query(FormResponse, AppUser).join(
                AppUser, FormResponse.user_id == AppUser.id
            ).filter(
                FormResponse.id == response_id,
                FormResponse.form_id == form_id
            ).first()
            
            if not result:
                return {'error': 'Response not found'}, 404
            
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

            return {
                'application': application_data,
                'review': review_data,
                'registration': registration_data,
                'generic_forms': generic_forms_data
            }, 200

        except Exception as e:
            LOGGER.error(f"Error getting form config for event {event_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE


class FormReviewAssignmentAPI(restful.Resource):
    """
    Manage review assignments for new-style review forms.

    A review assignment is simply a FormResponse (with no answers yet) on the
    review Form whose linked_response_id points to the applicant's FormResponse.
    This avoids any new model: assignment = pre-created unfilled FormResponse.
    """

    @event_admin_required
    def get(self, form_id, event_id):
        """Return per-reviewer allocation and completion counts for this review form."""
        try:
            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review'
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
                    'tags': []
                })
            return result, 200

        except Exception as e:
            LOGGER.error(f"Error getting review assignments for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def post(self, form_id, event_id):
        """Assign N reviews to a reviewer by bulk-creating FormResponse records."""
        try:
            args = request.get_json()
            reviewer_user_email = args.get('reviewer_user_email')
            num_reviews = args.get('num_reviews', 0)

            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review'
            ).first()
            if not review_form:
                return errors.FORM_NOT_FOUND

            if not review_form.linked_form_id:
                return {'error': 'Review form has no linked application form'}, 400

            reviewer = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
            if reviewer is None:
                return errors.USER_NOT_FOUND

            reviewer_id = reviewer.id
            reviewer_email = reviewer.email

            num_reviews_required = (review_form.settings or {}).get('num_reviews_required', 1)

            # All submitted, non-withdrawn application responses excluding the reviewer's own
            candidate_app_responses = db.session.query(FormResponse).filter(
                FormResponse.form_id == review_form.linked_form_id,
                FormResponse.is_submitted == True,
                FormResponse.is_withdrawn == False,
                FormResponse.user_id != reviewer_id
            ).all()

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
            LOGGER.error(f"Error assigning reviews for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE

    @event_admin_required
    def delete(self, form_id, event_id):
        """Remove up to N unstarted (no answers) review assignments from a reviewer."""
        try:
            args = request.get_json()
            reviewer_user_email = args.get('reviewer_user_email')
            num_reviews = args.get('num_reviews', 0)

            review_form = db.session.query(Form).filter_by(
                id=form_id, form_type='review'
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

            counter = 0
            for response in unstarted:
                db.session.delete(response)
                counter += 1
                if counter >= num_reviews:
                    break

            db.session.commit()
            return {'num_deleted': counter}, 200

        except Exception as e:
            LOGGER.error(f"Error removing review assignments for form {form_id}: {str(e)}")
            LOGGER.error(traceback.format_exc())
            db.session.rollback()
            return errors.DB_NOT_AVAILABLE
