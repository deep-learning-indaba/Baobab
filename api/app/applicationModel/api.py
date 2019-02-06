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

    #@auth_required

    form_fields = {
        'id': fields.Integer,
        'event_id': fields.Integer,
        'is_open':  fields.Boolean,
        'deadline': fields.DateTime
    }

    @marshal_with(form_fields)
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True, help = 'Invalid event_id requested. Event_id\'s should be of type int.')
        args = req_parser.parse_args()
        form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()
        if form: 
            return form
        else: 
            return EVENT_NOT_FOUND
        
        
