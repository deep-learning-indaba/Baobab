from app import db
from app.responses.models import Response


class ResponseRepository():

    @staticmethod
    def get_by_id_and_user_id(response_id, user_id):
        return db.session.query(Response)\
                         .filter_by(id=response_id, user_id=user_id)\
                         .first()