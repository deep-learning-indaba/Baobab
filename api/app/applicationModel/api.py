from datetime import datetime
import traceback

import flask_restful as restful

from flask_restful import reqparse, fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError
from flask import g

from app.applicationModel.models import ApplicationForm, Question, Section, SectionTranslation, QuestionTranslation
from app.events.repository import EventRepository as event_repository
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required, event_admin_required
from app.utils.errors import APPLICATION_FORM_EXISTS, QUESTION_NOT_FOUND, SECTION_NOT_FOUND, DB_NOT_AVAILABLE, FORM_NOT_FOUND, APPLICATIONS_CLOSED, UPDATE_CONFLICT

from app import db, bcrypt
from app import LOGGER

from typing import Sequence

def get_form_fields(form, language):
    section_fields = []
    for section in form.sections:
        question_fields = []
        for question in section.questions:
            question_translation = question.get_translation(language)
            question_field = {
                'id': question.id,
                'type': question.type,
                'description': question_translation.description,
                'headline': question_translation.headline,
                'order': question.order,
                'options': question_translation.options,
                'placeholder': question_translation.placeholder,
                'validation_regex': question_translation.validation_regex,
                'validation_text': question_translation.validation_text,
                'is_required': question.is_required,
                'depends_on_question_id': question.depends_on_question_id,
                'show_for_values': question_translation.show_for_values,
                'key': question.key
            }
            question_fields.append(question_field)

        section_translation = section.get_translation(language)
        section_field = {
            'id': section.id,
            'name': section_translation.name,
            'description': section_translation.description,
            'order': section.order,
            'depends_on_question_id': section.depends_on_question_id,
            'show_for_values': section_translation.show_for_values,
            'questions': question_fields
        }
        section_fields.append(section_field)

    form_fields = {
        'id': form.id,
        'event_id': form.event_id,
        'is_open':  form.is_open,
        'nominations': form.nominations,
        'sections': section_fields
    }
    return form_fields

question_detail_fields = {
    'id': fields.Integer,
    'type': fields.String,
    'description': fields.Raw(attribute=lambda q: q.description_translations),
    'headline': fields.Raw(attribute=lambda q: q.headline_translations),
    'order': fields.Integer,
    'options': fields.Raw(attribute=lambda q: q.options_translations),
    'placeholder': fields.Raw(attribute=lambda q: q.placeholder_translations),
    'validation_regex': fields.Raw(attribute=lambda q: q.validation_regex_translations),
    'validation_text': fields.Raw(attribute=lambda q: q.validation_text_translations),
    'is_required': fields.Boolean,
    'depends_on_question_id': fields.Integer,
    'show_for_values': fields.Raw(attribute=lambda q: q.show_for_values_translations),
    'key': fields.String
}

section_detail_fields = {
    'id': fields.Integer,
    'name': fields.Raw(attribute=lambda s: s.name_translations),
    'description': fields.Raw(attribute=lambda s: s.description_translations),
    'order': fields.Integer,
    'depends_on_question_id': fields.Integer,
    'show_for_values': fields.Raw(attribute=lambda s: s.show_for_values_translations),
    'questions': fields.List(fields.Nested(question_detail_fields)),
    'key': fields.String
}

application_form_detail_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'is_open':  fields.Boolean,
    'nominations': fields.Boolean,
    'sections': fields.List(fields.Nested(section_detail_fields))
}

class ApplicationFormAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True, help='Invalid event_id requested. Event_id\'s should be of type int.')
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()

        language = args['language']

        try:
            form = application_form_repository.get_by_event_id(args['event_id'])
            event = event_repository.get_by_id(args['event_id'])

            if not form:
                return FORM_NOT_FOUND

            if not event.is_application_open and not user_repository.get_by_id(g.current_user['id']).is_event_admin(args['event_id']):
                return APPLICATIONS_CLOSED
            
            if not form.sections:
                return SECTION_NOT_FOUND
            
            if not form.questions:
                return QUESTION_NOT_FOUND

            return get_form_fields(form, language)

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return DB_NOT_AVAILABLE

class ApplicationFormDetailAPI(restful.Resource):

    @event_admin_required
    @marshal_with(application_form_detail_fields)
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        app_form = application_form_repository.get_by_event_id(event_id)
        return app_form

    @event_admin_required
    @marshal_with(application_form_detail_fields)
    def post(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('is_open', type=bool, required=True)
        req_parser.add_argument('nominations', type=bool, required=True)
        req_parser.add_argument('sections', type=dict, required=True, action='append')
        req_parser.add_argument('allows_edits', type=bool, required=True)
        args = req_parser.parse_args()

        app_form = application_form_repository.get_by_event_id(event_id)
        if app_form:
            return APPLICATION_FORM_EXISTS

        is_open = args['is_open']
        nominations = args['nominations']
        allows_edits = args['allows_edits']

        app_form = ApplicationForm(
            event_id,
            is_open,
            nominations,
            allows_edits)
        application_form_repository.add(app_form)
        sections_data = args['sections']

        # Keep track of which objects match with which incoming data for populating dependencies later.
        section_data_map = {}
        question_data_map = {}
        question_id_map = {}

        for section_data in sections_data:
            section = Section(
                app_form.id,
                section_data['order'],
                key=section_data['key']
            )
            application_form_repository.add(section)
            section_data_map[section] = section_data

            languages = section_data['name'].keys()
            for language in languages:
                section_translation = SectionTranslation(
                    section.id, 
                    language, 
                    section_data['name'][language], 
                    section_data['description'][language],
                    section_data['show_for_values'][language])
                application_form_repository.add(section_translation)

            for question_data in section_data['questions']:
                # application_form_id, section_id, order, questionType, is_required=True
                question = Question(
                    app_form.id,
                    section.id,
                    question_data['order'],
                    question_data['type'],
                    question_data['is_required']
                )
                application_form_repository.add(question)
                question_data_map[question] = question_data

                if "surrogate_id" in question_data:
                    question_id_map[question_data["surrogate_id"]] = question.id

                for language in languages:
                    question_translation = QuestionTranslation(
                        question_id=question.id,
                        language=language,
                        headline=question_data['headline'][language],
                        description=question_data['description'][language],
                        placeholder=question_data['placeholder'][language],
                        validation_regex=question_data['validation_regex'][language],
                        validation_text=question_data['validation_text'][language],
                        options=question_data['options'][language],
                        show_for_values=question_data['show_for_values'][language])
                    application_form_repository.add(question_translation)

        # Now that all the questions have been created, we can populate the dependencies
        for section, section_data in section_data_map.items():
            if section_data['depends_on_question_id']:
                section.depends_on_question_id = question_id_map[section_data['depends_on_question_id']]
        
        for question, question_data in question_data_map.items():
            if question_data['depends_on_question_id']:
                question.depends_on_question_id = question_id_map[question_data['depends_on_question_id']]

        application_form_repository.save()

        app_form = application_form_repository.get_by_id(app_form.id)
        return app_form, 201

    @event_admin_required
    @marshal_with(application_form_detail_fields)
    def put(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('is_open', type=bool, required=True)
        req_parser.add_argument('nominations', type=bool, required=True)
        req_parser.add_argument('id', type=int, required=True)
        req_parser.add_argument('sections', type=dict, required=True, action='append')
        req_parser.add_argument('allows_edits', type=bool, required=True)

        args = req_parser.parse_args()
        user_id = g.current_user['id']
        application_form_id = args['id']

        app_form = application_form_repository.get_by_id(application_form_id)  # type: ApplicationForm
        if not app_form:
            return FORM_NOT_FOUND

        if event_id != app_form.event_id:
            return UPDATE_CONFLICT

        app_form.is_open = args['is_open']
        app_form.nominations = args['nominations']
        app_form.allows_edits = args['allows_edits']

        current_sections = app_form.sections
        incoming_sections = args['sections']

        # Delete questions in the application form that no longer exist
        all_question_ids = [q['id'] for s in incoming_sections for q in s['questions'] if 'id' in q]
        
        for question in app_form.questions:
            if question.id not in all_question_ids:
                print("DELETING QUESTION ID ", question.id)
                application_form_repository.delete_question(question)

        all_section_ids = [s['id'] for s in incoming_sections if 'id' in s]
        
        for section in app_form.sections:
            if section.id not in all_section_ids:
                print("DELETING SECTION ID ", section.id)
                application_form_repository.delete_section(section)
        
        # Keep track of which objects match with which incoming data for populating dependencies later.
        section_data_map = {}
        question_data_map = {}
        question_id_map = {}

        for section_data in incoming_sections:
            if 'id' in section_data:
                # If ID is populated, then update the existing section
                section = next((s for s in current_sections if s.id == section_data['id']), None)  # type: Section
                if not section:
                    return SECTION_NOT_FOUND

                current_translations = section.section_translations  # type: Sequence[SectionTranslation]
                for current_translation in current_translations:
                    current_translation.description = section_data['description'][current_translation.language]
                    current_translation.name = section_data['name'][current_translation.language]
                    current_translation.show_for_values = section_data['show_for_values'][current_translation.language]

                section.key = section_data['key']
                section.order = section_data['order']
                
                db.session.commit()
            else:
                # if not populated, then add new section
                section = Section(
                    app_form.id,
                    section_data['order'],
                    key=section_data['key']
                )
                application_form_repository.add(section)

                languages = section_data['name'].keys()
                for language in languages:
                    section_translation = SectionTranslation(
                        section.id, 
                        language, 
                        section_data['name'][language], 
                        section_data['description'][language],
                        section_data['show_for_values'][language])
                    application_form_repository.add(section_translation)

            section_data_map[section] = section_data
            try:
                question_map, question_ids = _process_questions(section_data['questions'], app_form, section.id)
                question_data_map.update(question_map)
                question_id_map.update(question_ids)
            except ValueError:
                return QUESTION_NOT_FOUND

        db.session.commit()

        # Now that all the questions have been created, we can populate the dependencies
        for section, section_data in section_data_map.items():
            if section_data['depends_on_question_id']:
                section.depends_on_question_id = question_id_map[section_data['depends_on_question_id']]
        
        for question, question_data in question_data_map.items():
            if question_data['depends_on_question_id']:
                question.depends_on_question_id = question_id_map[question_data['depends_on_question_id']]

        db.session.commit()

        app_form = application_form_repository.get_by_id(app_form.id)

        return app_form, 200


def _process_questions(questions, application_form, section_id):
    current_questions = application_form.questions
    question_data_map = {}
    question_ids = {}
    for question_data in questions:
        if 'id' in question_data:
            current_question = next((s for s in current_questions if s.id == question_data['id']), None)  # type: Question
            if not current_question:
                raise ValueError(f'Question with id {question_data["id"]} not found')
            
            current_question.order = question_data['order']
            current_question.section_id = section_id
            current_question.is_required = question_data['is_required']
            current_question.key = question_data['key']
            current_question.type = question_data['type']
            
            current_translations = current_question.question_translations  # type: Sequence[QuestionTranslation]
            for current_translation in current_translations:
                current_translation.description = question_data['description'][current_translation.language]
                current_translation.headline = question_data['headline'][current_translation.language]
                current_translation.options = question_data['options'][current_translation.language]
                current_translation.placeholder = question_data['placeholder'][current_translation.language]
                current_translation.show_for_values = question_data['show_for_values'][current_translation.language]
                current_translation.validation_regex = question_data['validation_regex'][current_translation.language]
                current_translation.validation_text = question_data['validation_text'][current_translation.language]

            question_ids[question_data['id']] = question_data['id']
            question_data_map[current_question] = question_data
        else:
            question = Question(
                application_form_id=application_form.id, 
                section_id=section_id, 
                order=question_data['order'], 
                questionType=question_data['type'], 
                is_required=question_data['is_required'])
            question.key = question_data['key']
            application_form_repository.add(question)

            for language in question_data['headline'].keys():
                translation = QuestionTranslation(
                    question.id,
                    language,
                    headline=question_data['headline'][language],
                    description=question_data['description'][language],
                    placeholder=question_data['placeholder'][language],
                    validation_regex=question_data['validation_regex'][language],
                    validation_text=question_data['validation_text'][language],
                    options=question_data['options'][language],
                    show_for_values=question_data['show_for_values'][language])
                application_form_repository.add(translation)

            if 'surrogate_id' in question_data:
                question_ids[question_data['surrogate_id']] = question.id
            question_data_map[question] = question_data
    
    return question_data_map, question_ids

def _serialize_question(question, language):
    translation = question.get_translation(language)
    if not translation:
        LOGGER.warn('Could not find {} translation for question id {}'.format(language, question.id))
        translation = question.get_translation('en')
    return dict(
        question_id=question.id,
        headline=translation.headline,
        type=question.type
    )

class QuestionListApi(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()
        language = args['language']

        questions = application_form_repository.get_questions_for_event(event_id)
        return [_serialize_question(q, language) for q in questions]
