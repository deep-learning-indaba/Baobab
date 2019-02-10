import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from app.responses.models import Response, Answer

from app.utils.errors import EVENT_NOT_FOUND, QUESTION_NOT_FOUND, DB_NOT_AVAILABLE

from app import db, bcrypt

class ResponseAPI(restful.Resource):
    def get(self):
        pass

    def post(self):
        pass

    def delete(self):
        pass
