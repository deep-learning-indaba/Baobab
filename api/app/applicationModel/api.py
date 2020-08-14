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


class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):
    question_fields = {
        'id': fields.Integer,
        'type': fields.String,
        # 'description': fields.String,
        # 'headline': fields.String,
        'order': fields.Integer,
        # 'options': fields.Raw,
        # 'placeholder': fields.String,
        # 'validation_regex': fields.String,
        # 'validation_text': fields.String,
        'is_required': fields.Boolean,
        'depends_on_question_id': fields.Integer,
        # 'show_for_values': fields.Raw,
        'key': fields.String
    }

    section_fields = {
        'id': fields.Integer,
        #'name': fields.String,
        #'description': fields.String,
        'order': fields.Integer,
        'depends_on_question_id': fields.Integer,
        'show_for_values': fields.Raw,
        'questions': fields.List(fields.Nested(question_fields)),
    }

    form_fields = {
        'id': fields.Integer,
        'event_id': fields.Integer,
        'is_open':  fields.Boolean,
        'nominations': fields.Boolean,
        'sections': fields.List(fields.Nested(section_fields))
    }

    @auth_required
    @marshal_with(form_fields)
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

            return form

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return DB_NOT_AVAILABLE
