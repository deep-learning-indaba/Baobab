from sqlalchemy.sql import func
from sqlalchemy import and_

from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import ResponseReviewer, Response
from app.reviews.models import ReviewResponse, ReviewForm
from app.users.models import AppUser

class ReviewRepository():

    @staticmethod
    def count_reviews_allocated_and_completed_per_reviewer(event_id):
        return db.session.query(AppUser.email, AppUser.user_title, AppUser.firstname, AppUser.lastname, func.count(ResponseReviewer.response_id).label('reviews_allocated'), func.count(ReviewResponse.response_id).label('reviews_completed'))\
                        .join(ResponseReviewer, ResponseReviewer.reviewer_user_id==AppUser.id)\
                        .join(Response, Response.id==ResponseReviewer.response_id)\
                        .join(ApplicationForm, ApplicationForm.id==Response.application_form_id)\
                        .filter_by(event_id=event_id)\
                        .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==ResponseReviewer.reviewer_user_id))\
                        .group_by(ResponseReviewer.reviewer_user_id, AppUser.email, AppUser.user_title, AppUser.firstname, AppUser.lastname)\
                        .all()