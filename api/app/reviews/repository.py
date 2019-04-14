from sqlalchemy.sql import func, exists
from sqlalchemy import and_
from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import ResponseReviewer, Response
from app.reviews.models import ReviewResponse, ReviewForm
from app.users.models import AppUser
from app.events.models import EventRole

class ReviewRepository():

    @staticmethod
    def count_reviews_allocated_and_completed_per_reviewer(event_id):
        return (
            db.session.query(
                AppUser.email, AppUser.user_title, AppUser.firstname, AppUser.lastname, 
                func.count(ResponseReviewer.response_id).label('reviews_allocated'), 
                func.count(ReviewResponse.response_id).label('reviews_completed'))
            .join(EventRole, EventRole.user_id==AppUser.id)
            .filter(EventRole.event_id==event_id)
            .filter(EventRole.role=="reviewer")
            .join(ApplicationForm, ApplicationForm.event_id==EventRole.event_id)
            .outerjoin(ResponseReviewer, ResponseReviewer.reviewer_user_id==AppUser.id)
            .outerjoin(Response, Response.id==ResponseReviewer.response_id)
            .filter(Response.application_form_id==ApplicationForm.id)
            .outerjoin(
                ReviewResponse, 
                and_(
                    ReviewResponse.response_id==ResponseReviewer.response_id, 
                    ReviewResponse.reviewer_user_id==ResponseReviewer.reviewer_user_id)
            )
            .group_by(
                ResponseReviewer.reviewer_user_id, AppUser.email, AppUser.user_title, 
                AppUser.firstname, AppUser.lastname)
            .all()
        )

    @staticmethod
    def count_unassigned_reviews(event_id, required_reviews_per_response):
        responses =  (
            db.session.query(func.count(Response.id))
            .join(ApplicationForm, Response.application_form_id ==ApplicationForm.id)
            .filter(ApplicationForm.event_id == event_id)
            .filter(Response.is_submitted==True, Response.is_withdrawn==False)
            .first()[0]
        )

        reviews = (
            db.session.query(func.count(ResponseReviewer.id))
            .join(Response, ResponseReviewer.response_id ==Response.id)
            .join(ApplicationForm, Response.application_form_id ==ApplicationForm.id)
            .filter(ApplicationForm.event_id == event_id).first()[0]
        )

        return responses*required_reviews_per_response - reviews