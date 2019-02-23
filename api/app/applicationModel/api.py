from datetime import datetime

import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with


from app.applicationModel.mixins import ApplicationFormMixin
from app.applicationModel.models import ApplicationForm, Question, Section

from app.utils.errors import EVENT_NOT_FOUND, QUESTION_NOT_FOUND, SECTION_NOT_FOUND, DB_NOT_AVAILABLE, FORM_NOT_FOUND

from app import db, bcrypt
from app import LOGGER


class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):

    option_fields = {
        'selection': fields.String
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

    @marshal_with(form_fields)
    def get(self):
        LOGGER.info('Received get request for application form')
        args = self.req_parser.parse_args()
        LOGGER.info('Parsed Args: {}'.format(args['event_id']))

        try:
            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
            if(not form):
                return FORM_NOT_FOUND

            sections = db.session.query(Section).filter(Section.application_form_id == form.id).all()   #All sections in our form
            if(not sections):
                return SECTION_NOT_FOUND

            questions = db.session.query(Question).filter(Question.application_form_id == form.id).all() #All questions in our form        
            if(not questions):
                return QUESTION_NOT_FOUND

            form.sections = sections

            for s in form.sections:
                s.questions = []
                for q in questions:
                    if(q.section_id == s.id):
                        s.questions.append(q)

            if (form): 
                return form
            else: 
                return EVENT_NOT_FOUND
        except:
            return DB_NOT_AVAILABLE
