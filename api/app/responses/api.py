import flask_restful as restful
from flask import g, request
from flask_restful import reqparse, fields, marshal_with
from app.applicationModel.mixins import ApplicationFormMixin
from app.responses.models import Response, Answer
from app.applicationModel.models import ApplicationForm
from app.events.models import Event
from app.utils.auth import auth_required

from app.utils.errors import FORM_NOT_FOUND, EVENT_NOT_FOUND, QUESTION_NOT_FOUND, DB_NOT_AVAILABLE, RESPONSE_NOT_FOUND

from app import db, bcrypt

# TODO: Refactor ApplicationFormMixin
class ResponseAPI(ApplicationFormMixin, restful.Resource):

    answer_fields = {
        'id': fields.Integer,
        'question_id': fields.Integer,
        'value': fields.String
    }

    response_fields = {
        'id': fields.Integer,
        'application_form_id': fields.Integer,
        'user_id': fields.Integer,
        'is_submitted': fields.Boolean,
        'submitted_timestamp': fields.DateTime,
        'is_withdrawn': fields.Boolean,
        'withdrawn_timestamp': fields.DateTime,
        'started_timestamp': fields.DateTime,
        'answers': fields.List(fields.Nested(answer_fields))
    }

    @auth_required
    @marshal_with(response_fields)
    def get(self):
        args = self.req_parser.parse_args()

        try:
            event = db.session.query(Event).filter(Event.id == args['event_id']).first()
            if not event:
                return EVENT_NOT_FOUND

            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
            if not form:
                return FORM_NOT_FOUND

            response = db.session.query(Response).filter(Response.application_form_id == form.id and Response.user_id == g.current_user['id']).first()
            if not response:
                return RESPONSE_NOT_FOUND
            
            answers = db.session.query(Answer).filter(Answer.response_id == response.id).all()
            response.answers = list(answers)

            return response
        except:
            return DB_NOT_AVAILABLE

    @auth_required
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('is_submitted', type=bool, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        try: 
            response = Response(args['application_form_id'], user_id)
            db.session.add(response)
            db.session.commit()

            for answer_args in args['answers']:
                answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
                db.session.add(answer)
            db.session.commit()

        except:
            return DB_NOT_AVAILABLE

    def put(self, response_id):
        # Update an existing response for the logged-in user.
        pass

    def delete(self, response_id):
        # Delete an existing response for the logged-in user.
        pass
