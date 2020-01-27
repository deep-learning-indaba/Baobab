from app import db
from app.applicationModel.models import ApplicationForm
from app.events.models import EventRole
from app.responses.models import Response
from app.users.models import AppUser
from app.organisation.models import Organisation
from sqlalchemy import func

class UserRepository():

    @staticmethod
    def get_by_id(user_id):
        return db.session.query(AppUser).get(user_id)

    @staticmethod
    def get_by_id_with_response(user_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(id=user_id)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .first()

    @staticmethod
    def get_by_email(email, organisation_id):
        return db.session.query(AppUser)\
            .filter(func.lower(AppUser.email) == func.lower(email))\
            .filter_by(organisation_id=organisation_id).first()

    @staticmethod
    def get_by_event_admin(user_id, event_admin_user_id):
        return db.session.query(AppUser, Response)\
                         .filter_by(id=user_id)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .join(ApplicationForm, ApplicationForm.id==Response.application_form_id)\
                         .join(EventRole, EventRole.event_id==ApplicationForm.event_id)\
                         .filter_by(user_id=event_admin_user_id, role='admin')\
                         .first()

    @staticmethod
    def get_all_with_unsubmitted_response():
        # TODO: Filter this to event
        return db.session.query(AppUser)\
                         .filter_by(active=True, is_deleted=False)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .filter_by(is_submitted=False, is_withdrawn=False)\
                         .all()
    
    @staticmethod
    def get_all_without_responses():
        # TODO: Filter this to event
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