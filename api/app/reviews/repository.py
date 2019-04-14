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
        return db.engine.execute("""
                (
                    select 
                        email, 
                        user_title, 
                        firstname, 
                        lastname, 
                        0 as reviews_allocated, 
                        0 as reviews_completed
                    from app_user
                    join event_role on event_role.user_id = app_user.id
                    where event_role.role = 'reviewer'
                    and event_role.event_id = :event_id
                    and not exists (
                        select 1
                        from response_reviewer
                        where response_reviewer.reviewer_user_id = app_user.id
                    )
                )
                union
                (
                    select        
                        email, 
                        user_title, 
                        firstname, 
                        lastname, 
                        count(response_reviewer.id) as reviews_allocated, 
                        count(review_response.id) as reviews_completed
                    from response_reviewer
                    join app_user 
                    on response_reviewer.reviewer_user_id = response_reviewer.reviewer_user_id
                    join event_role 
                        on app_user.id = event_role.user_id 
                    join response 
                    on response.id = response_reviewer.response_id
                    left join review_response
                    on review_response.response_id = response.id
                    where 
                        event_role.role = 'reviewer'
                        and event_role.event_id = :event_id
                    group by app_user.id

                )
            """, {'event_id': event_id})

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