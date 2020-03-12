from app import db
from app.responses.models import Response


class ResponseRepository():

    @staticmethod
    def get_by_id_and_user_id(response_id, user_id):
        return db.session.query(Response)\
                         .filter_by(id=response_id, user_id=user_id)\
                         .first()


    @staticmethod
    def get_by_id(response_id):
        return db.session.query(Response).get(response_id)

    
    @staticmethod
    def get_all_for_user_application(user_id, application_form_id):
        return db.session.query(Response)\
            .filter(Response.application_form_id == application_form_id, Response.user_id == user_id)