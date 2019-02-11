import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from app.responses.models import Response, Answer

from app.utils.errors import EVENT_NOT_FOUND, QUESTION_NOT_FOUND, DB_NOT_AVAILABLE

from app import db, bcrypt

class ResponseAPI(restful.Resource):

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

    @marshal_with(response_fields)
    def get(self):
        pass

    def post(self):
        pass

    def delete(self):
        pass
