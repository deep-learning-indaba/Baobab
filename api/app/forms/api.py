from datetime import datetime
import traceback

import flask_restful as restful
from flask import g, request

from app.forms.models import (
    Form, FormResponse, FormAnswer, FormSection, FormQuestion,
    FormTranslation, FormSectionTranslation, FormQuestionTranslation,
    DependencyEvaluator
)
from app.utils.auth import auth_required
from app.utils import errors
from app import db, LOGGER


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
            'is_active': section.is_active,
            'version': section.version,
            'created_at': section.created_at.isoformat() if section.created_at else None,
            'updated_at': section.updated_at.isoformat() if section.updated_at else None,
            'name': name_i18n,
            'description': description_i18n,
            'questions': questions_data
        }
        sections_data.append(section_data)
    
    # Get all translations for the form name
    form_translations_dict = {}
    for translation in form.translations:
        form_translations_dict[translation.language] = translation
    
    name_i18n = {}
    for lang, trans in form_translations_dict.items():
        name_i18n[lang] = trans.name
    
    return {
        'id': form.id,
        'name': name_i18n,
        'is_active': form.is_active,
        'is_open': form.is_open,
        'multiple_responses': form.multiple_responses,
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
        'answers': answers_data
    }


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
            
            # Create empty form
            form = Form(
                created_by_user_id=user_id,
                is_open=args.get('is_open', False),
                is_active=args.get('is_active', True),
                linked_form_id=args.get('linked_form_id'),
                multiple_responses=args.get('multiple_responses', False),
                settings=args.get('settings')
            )
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
            if 'settings' in args:
                form.settings = args['settings']
            
            # Update form name translations
            if 'name' in args and args['name']:
                for lang, name_text in args['name'].items():
                    # Find or create translation
                    translation = db.session.query(FormTranslation).filter_by(
                        form_id=form.id,
                        language=lang
                    ).first()
                    
                    if translation:
                        translation.name = name_text
                    else:
                        translation = FormTranslation(
                            form_id=form.id,
                            language=lang,
                            name=name_text
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
            
            # Update form name translations if provided
            if 'name' in args and args['name']:
                for lang, name_text in args['name'].items():
                    translation = db.session.query(FormTranslation).filter_by(
                        form_id=form.id,
                        language=lang
                    ).first()
                    
                    if translation:
                        translation.name = name_text
                    else:
                        translation = FormTranslation(
                            form_id=form.id,
                            language=lang,
                            name=name_text
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
            
            # Create new response
            language = args.get('language', 'en')
            response = FormResponse(
                form_id=form_id,
                user_id=user_id,
                language=language
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
            
            # response_id is required for PUT
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
        """Get user's response(s)"""
        try:
            form = db.session.query(Form).filter_by(id=form_id).first()
            if not form:
                return errors.FORM_NOT_FOUND
            
            user_id = g.current_user['id']
            
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
                
                # Check if question is visible
                if answer.question.dependency_expression:
                    question_visible = DependencyEvaluator.evaluate(
                        answer.question.dependency_expression,
                        answers_dict
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
