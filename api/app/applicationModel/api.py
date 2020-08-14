from datetime import datetime
import traceback

import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError

from app.applicationModel.mixins import ApplicationFormMixin
from app.applicationModel.models import ApplicationForm, Question, Section
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND, QUESTION_NOT_FOUND, SECTION_NOT_FOUND, DB_NOT_AVAILABLE, FORM_NOT_FOUND, APPLICATIONS_CLOSED

from app import db, bcrypt
from app import LOGGER

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

class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        language = args['language']

        try:
            form = application_form_repository.get_by_event_id(args['event_id'])
            if not form:
                return FORM_NOT_FOUND

            if not form.is_open:
                return APPLICATIONS_CLOSED

            if not form.sections:
                return SECTION_NOT_FOUND

            return get_form_fields(form, language)

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return DB_NOT_AVAILABLE
