from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response
from app.users.models import AppUser

class UserRepository():

    @staticmethod
    def get_by_id(user_id):
        return db.session.query(AppUser).get(user_id)

    @staticmethod
    def get_by_email(email):
        return db.session.query(AppUser).filter_by(email=email).first()

    @staticmethod
    def get_all_with_unsubmitted_response():
        return db.session.query(AppUser)\
                         .filter_by(active=True, is_deleted=False)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .filter_by(is_submitted=False, is_withdrawn=False)\
                         .all()
    
    @staticmethod
    def get_all_without_responses():
        return db.session.query(AppUser)\
                         .filter_by(active=True, is_deleted=False)\
                         .outerjoin(Response, Response.user_id==AppUser.id)\
                         .filter_by(id=None)\
                         .all()
    
    @staticmethod
    def get_all_with_responses_for(event_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(active=True, is_deleted=False)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .join(ApplicationForm, ApplicationForm.id==Response.application_form_id)\
                         .filter_by(event_id=event_id)\
                         .all()