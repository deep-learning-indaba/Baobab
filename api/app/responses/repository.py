from app import db
from app.responses.models import Response


class ResponseRepository():

    @staticmethod
    def get_by_id(response_id):
        return db.session.query(Response).get(response_id)