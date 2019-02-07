from datetime import datetime

from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError


from app.applicationModel.mixins import ApplicationFormMixin
from app.applicationModel.models import ApplicationForm, Question, Section

from app.utils.errors import EVENT_NOT_FOUND

from app import db, bcrypt



class ApplicationFormAPI(ApplicationFormMixin, restful.Resource):

    question_fields = {
        'id': fields.Integer,
        'type': fields.String,
        'description': fields.String,
        'order': fields.Integer
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
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True, help = 'Invalid event_id requested. Event_id\'s should be of type int.')
        args = req_parser.parse_args()

        form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
        sections = db.session.query(Section).filter(Section.application_form_id == form.id).all()   #All sections in our form
        questions = db.session.query(Question).filter(Question.application_form_id == form.id).all() #All questions in our form        

        form.sections = sections

        for s in form.sections:
            s.questions = []
            for q in questions:
                if(q.section_id == s.id):
                    s.questions.append(q)

        if form: 
            return form
        else: 
            return EVENT_NOT_FOUND
        
        
