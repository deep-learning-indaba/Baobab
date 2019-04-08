from app import db
from app.responses.models import Response
from app.users.models import AppUser

class UserRepository():

    @staticmethod
    def get_all_users_with_unsubmitted_response():
        return db.session.query(AppUser)\
                         .filter_by(active=True, is_deleted=False)\
                         .join(Response, Response.user_id==AppUser.id)\
                         .filter_by(is_submitted=True, is_withdrawn=False)\
                         .all()