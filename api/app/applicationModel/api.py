from datetime import datetime
import traceback

import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError

from app.applicationModel.mixins import ApplicationFormMixin
from app.applicationModel.models import ApplicationForm, Question, Section

from app.utils.errors import EVENT_NOT_FOUND, QUESTION_NOT_FOUND, SECTION_NOT_FOUND, DB_NOT_AVAILABLE, FORM_NOT_FOUND, APPLICATIONS_CLOSED

from app import db, bcrypt
from app import LOGGER


class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):

    option_fields = {
        'value': fields.String,
        'label': fields.String
    }

    question_fields = {
        'id': fields.Integer,
        'type': fields.String,
        'description': fields.String,
        'headline': fields.String,
        'order': fields.Integer,
        'options': fields.List(fields.Nested(option_fields)),
        'placeholder': fields.String,
        'validation_regex': fields.String,
        'validation_text': fields.String,
        'is_required': fields.Boolean
    } 

    section_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'order': fields.Integer,  
        'questions': fields.List(fields.Nested(question_fields))   
    }

    form_fields = {
        'id': fields.Integer,
        'event_id': fields.Integer,
        'is_open':  fields.Boolean,
        'deadline': fields.DateTime,
        'sections': fields.List(fields.Nested(section_fields)) 
    }

    def get(self):
        LOGGER.debug('Received get request for application form')
        args = self.req_parser.parse_args()
        LOGGER.debug('Parsed Args for event_id: {}'.format(args))

        try:
            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
            if(not form):
                LOGGER.warn('Form not found for event_id: {}'.format(args['event_id']))
                return FORM_NOT_FOUND

            if not form.is_open:
                return APPLICATIONS_CLOSED

            sections = db.session.query(Section).filter(Section.application_form_id == form.id).all()   #All sections in our form
            if(not sections):
                LOGGER.warn('Sections not found for event_id: {}'.format(args['event_id']))
                return SECTION_NOT_FOUND

            questions = db.session.query(Question).filter(Question.application_form_id == form.id).all() #All questions in our form        
            if(not questions):
                LOGGER.warn('Questions not found for  event_id: {}'.format(args['event_id']))
                return QUESTION_NOT_FOUND

            form.sections = sections

            for s in form.sections:
                s.questions = []
                for q in questions:
                    if(q.section_id == s.id):
                        s.questions.append(q)

            if (form): 
                return marshal(form, self.form_fields)
            else:
                LOGGER.warn("Event not found for event_id: {}".format(args['event_id'])) 
                return EVENT_NOT_FOUND

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return DB_NOT_AVAILABLE
