from sqlalchemy.sql import exists
from sqlalchemy import and_, or_, func, cast, Date
from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response, ResponseReviewer
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore, ReviewSection, ReviewSectionTranslation, ReviewQuestion, ReviewQuestionTranslation, ReviewConfiguration
from app.users.models import AppUser
from app.references.models import Reference
from app.events.models import EventRole
from app.utils import misc

class ReviewRepository():

    @staticmethod
    def count_reviews_allocated_and_completed_per_reviewer(event_id):
        return db.engine.execute("""
                (
                    select
                        app_user.id as reviewer_user_id,
                        email,
                        user_title,
                        firstname,
                        lastname,
                        0 as reviews_allocated,
                        0 as reviews_completed
                    from app_user
                    join event_role on event_role.user_id = app_user.id
                    where event_role.role = 'reviewer'
                    and event_role.event_id = {event_id}
                    and not exists (
                        select 1
                        from response_reviewer
                        inner join response on response_reviewer.response_id = response.id
                        inner join application_form on response.application_form_id = application_form.id
                        where response_reviewer.reviewer_user_id = app_user.id
                        and application_form.event_id = {event_id}
                    )
                )
                union
                (
                    select
                        app_user.id as reviewer_user_id,
                        email,
                        user_title,
                        firstname,
                        lastname,
                        count(response_reviewer.id) as reviews_allocated,
                        count(review_response.id) as reviews_completed
                    from response_reviewer
                    join app_user
                    on response_reviewer.reviewer_user_id = app_user.id
                    join event_role
                        on app_user.id = event_role.user_id
                    join response
                    on response.id = response_reviewer.response_id
                    join application_form on response.application_form_id = application_form.id
                    left join review_response
                    on review_response.response_id = response.id
                    and review_response.reviewer_user_id = app_user.id
                    where
                        event_role.role = 'reviewer'
                        and event_role.event_id = {event_id}
                        and application_form.event_id = {event_id}
                    group by app_user.id

                )
            """.format(event_id=event_id))

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

    @staticmethod
    def get_review_form(event_id, stage=None):
        query = db.session.query(ReviewForm)
        
        if stage:
            query = query.filter_by(stage=stage)
        else:
            query = query.filter_by(active=True)

        review_form = (query.join(ApplicationForm, ApplicationForm.id==ReviewForm.application_form_id)
                      .filter_by(event_id=event_id)
                      .first())

        return review_form

    @staticmethod
    def get_review_forms(event_id):
        review_forms = (db.session.query(ReviewForm)
            .join(ApplicationForm, ApplicationForm.id==ReviewForm.application_form_id)
            .filter_by(event_id=event_id)
            .all())
        
        return review_forms

    @staticmethod
    def get_review_form_by_id(id):
        return db.session.query(ReviewForm).get(id)

    @staticmethod
    def get_remaining_reviews_count(reviewer_user_id, application_form_id):
        remaining = (
            db.session.query(func.count(ResponseReviewer.id))
                    .filter_by(reviewer_user_id=reviewer_user_id, active=True)
                    .join(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==reviewer_user_id))
                    .filter(or_(ReviewResponse.id == None, ReviewResponse.is_submitted == False))
                    .all()[0][0]
        )
        return remaining

    @staticmethod
    def get_response_to_review(skip, reviewer_user_id, application_form_id):
        response = (
            db.session.query(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .join(ResponseReviewer)
                    .filter_by(reviewer_user_id=reviewer_user_id, active=True)
                    .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==reviewer_user_id))
                    .filter(or_(ReviewResponse.id == None, ReviewResponse.is_submitted == False))
                    .order_by(ResponseReviewer.response_id)
                    .offset(skip)
                    .first()
        )
        return response

    @staticmethod
    def get_review_response_with_form(id, reviewer_user_id):
        review_form_response = (
            db.session.query(ReviewForm, ReviewResponse)
                    .filter(ReviewForm.active == True)
                    .join(ReviewResponse)
                    .filter_by(id=id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return review_form_response

    @staticmethod
    def get_response_by_review_response(id, reviewer_user_id, application_form_id):
        response = (
            db.session.query(Response)
                    .filter_by(is_withdrawn=False, application_form_id=application_form_id, is_submitted=True)
                    .join(ResponseReviewer)
                    .filter_by(reviewer_user_id=reviewer_user_id)
                    .join(ReviewResponse)
                    .filter_by(id=id)
                    .first()
        )
        return response

    @staticmethod
    def get_response_reviewer(response_id, reviewer_user_id):
        response_reviewer = (
            db.session.query(ResponseReviewer)
                    .filter_by(response_id=response_id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return response_reviewer

    @staticmethod
    def get_review_response(review_form_id, response_id, reviewer_user_id):
        review_response = (
            db.session.query(ReviewResponse)
                    .filter_by(review_form_id=review_form_id, response_id=response_id, reviewer_user_id=reviewer_user_id)
                    .first()
        )
        return review_response

    @staticmethod
    def get_response_by_reviewer(response_id, reviewer_user_id):
        return (db.session.query(Response)
                    .filter_by(id=response_id)
                    .join(ResponseReviewer, Response.id == ResponseReviewer.response_id)
                    .filter_by(reviewer_user_id=reviewer_user_id)
                    .first())

    @staticmethod
    def add_model(model):
        db.session.add(model)
        db.session.commit()

    @staticmethod
    def get_review_history(reviewer_user_id, event_id):
        reviews = (db.session.query(ReviewResponse.id, ReviewResponse.submitted_timestamp, AppUser, Response)
                        .filter(ReviewResponse.reviewer_user_id == reviewer_user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.application_form_id == event_id, ReviewForm.active == True)
                        .join(Response, ReviewResponse.response_id == Response.id)
                        .join(AppUser, Response.user_id == AppUser.id))
        return reviews

    @staticmethod
    def get_review_list(reviewer_user_id, event_id):
        reviews = (db.session.query(Response, ReviewResponse)
                        .join(ResponseReviewer, Response.id == ResponseReviewer.response_id)
                        .filter_by(reviewer_user_id=reviewer_user_id)
                        .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                        .filter_by(event_id=event_id)
                        .outerjoin(ReviewResponse, and_(Response.id == ReviewResponse.response_id, ReviewResponse.reviewer_user_id==reviewer_user_id)))
        return reviews

    @staticmethod
    def get_review_history_count(reviewer_user_id, event_id):
        count = (db.session.query(ReviewResponse)
                        .filter(ReviewResponse.reviewer_user_id == reviewer_user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.active == True)
                        .join(ApplicationForm, ReviewForm.application_form_id == ApplicationForm.id)
                        .filter(ApplicationForm.event_id == event_id)
                        .count())
        return count

    @staticmethod
    def get_count_reviews_completed_for_event(event_id):
        count = (db.session.query(ReviewResponse)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.active == True)
                        .join(ApplicationForm, ReviewForm.application_form_id == ApplicationForm.id)
                        .filter(ApplicationForm.event_id == event_id)
                        .count())
        return count

    @staticmethod
    def get_count_reviews_incomplete_for_event(event_id):
        count = (db.session.query(ResponseReviewer)
                        .join(Response, ResponseReviewer.response_id == Response.id)
                        .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                        .filter(ApplicationForm.event_id == event_id)
                        .join(ReviewForm, ApplicationForm.id == ReviewForm.application_form_id)
                        .filter(ReviewForm.active == True)
                        .outerjoin(ReviewResponse, and_(
                            ReviewResponse.review_form_id == ReviewForm.id,
                            ReviewResponse.reviewer_user_id == ResponseReviewer.reviewer_user_id))
                        .filter(ReviewResponse.id == None)
                        .count())
        return count

    @staticmethod
    def get_review_complete_timeseries_by_event(event_id):
        timeseries = (db.session.query(cast(ReviewResponse.submitted_timestamp, Date), func.count(ReviewResponse.submitted_timestamp))
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.active == True)
                        .join(ApplicationForm, ReviewForm.application_form_id == ApplicationForm.id)
                        .filter(ApplicationForm.event_id == event_id)
                        .group_by(cast(ReviewResponse.submitted_timestamp, Date))
                        .order_by(cast(ReviewResponse.submitted_timestamp, Date))
                        .all())
        return timeseries

    @staticmethod
    def get_already_assigned(reviewer_user_id):
        already_assigned = db.session.query(ResponseReviewer.response_id) \
            .filter(ResponseReviewer.reviewer_user_id == reviewer_user_id) \
            .all()
        return already_assigned


    @staticmethod
    def get_form_id(event_id):
        form_id = db.session.query(ApplicationForm.id).filter_by(event_id=event_id).first()[0]
        return form_id

    @staticmethod
    def deactivate_review(review_response):
        scores = db.session.query(ReviewScore).filter(ReviewScore.review_response_id == review_response.id,
                                                      ReviewScore.is_active == True).all()
        for score in scores:
            score.is_active = False
            db.session.merge(score)
        db.session.commit()

    @staticmethod
    def get_reference_models(response_id):
        references = db.session.query(Reference).filter(response_id=response_id).all()
        return references

    @staticmethod
    def get_candidate_response_ids(event_id, reviewer_user_id, reviews_required):
        candidate_response_ids = db.session.query(Response.id) \
            .filter(Response.user_id != reviewer_user_id,
                    Response.is_submitted == True,
                    Response.is_withdrawn == False) \
            .join(ApplicationForm, Response.application_form_id == ApplicationForm.id) \
            .filter(ApplicationForm.event_id == event_id) \
            .outerjoin(ResponseReviewer, Response.id == ResponseReviewer.response_id) \
            .group_by(Response.id) \
            .having(func.count(ResponseReviewer.reviewer_user_id) < reviews_required) \
            .all()
        return candidate_response_ids

    def get_response_reviewers_for_event(event_id):
        return (db.session.query(ResponseReviewer)
                  .join(Response, Response.id == ResponseReviewer.response_id)
                  .join(ApplicationForm, Response.application_form_id == ApplicationForm.id)
                  .filter_by(event_id=event_id)
                  .order_by(ResponseReviewer.response_id)
                  .all())

    @staticmethod
    def get_review_responses_for_event(event_id):
        return (db.session.query(ReviewResponse)
                  .join(ReviewForm, ReviewResponse.review_form_id == ReviewForm.id)
                  .filter_by(active=True)
                  .join(ApplicationForm, ReviewForm.application_form_id == ApplicationForm.id)
                  .filter_by(event_id=event_id)
                  .all())

    @staticmethod
    def delete_response_reviewer(response_id, reviewer_user_id):
        db.session.query(ResponseReviewer).filter_by(response_id=response_id, reviewer_user_id=reviewer_user_id).delete()
        db.session.commit()

    @staticmethod
    def get_all_review_responses_by_event(event_id):
        return (
            db.session.query(ReviewResponse)
            .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
            .filter_by(active=True)
            .join(ApplicationForm, ApplicationForm.id == ReviewForm.application_form_id)
            .filter_by(event_id=event_id)
            .all()
        )

    @staticmethod
    def get_average_score_for_review_question(response_id: int, review_question_id: int):
        review_score_values = (
            db.session.query(ReviewScore.value)
            .filter(ReviewScore.review_question_id == review_question_id, ReviewScore.is_active == True)
            .join(ReviewResponse, ReviewResponse.id == ReviewScore.review_response_id)
            .join(Response, Response.id == ReviewResponse.response_id)
            .filter_by(id=response_id)
            .all()
        )

        review_score_values = [misc.try_parse_float(review_score_value[0]) for review_score_value in review_score_values]

        if len(review_score_values) == 0:
            average_review_score = 0
        else:
            average_review_score = sum(review_score_values) / len(review_score_values)

        return average_review_score

    @staticmethod
    def get_all_review_forms_for_event(event_id):
        forms = (
            db.session.query(ReviewForm)
            .join(ApplicationForm, ApplicationForm.id == ReviewForm.application_form_id)
            .filter_by(event_id=event_id)
            .all())

        return forms
    
    @staticmethod
    def delete_review_question(question_to_delete: ReviewQuestion):
        db.session.query(ReviewQuestionTranslation).filter_by(review_question_id=question_to_delete.id).delete()
        db.session.query(ReviewQuestion).filter_by(id=question_to_delete.id).delete()
        db.session.commit()
    
    @staticmethod
    def delete_review_section(section: ReviewSection):
        db.session.query(ReviewSectionTranslation).filter_by(review_section_id=section.id).delete()

        for question in section.review_questions:
            ReviewRepository.delete_review_question(question)

        db.session.query(ReviewSection).filter_by(id=section.id).delete()
        db.session.commit()

class ReviewConfigurationRepository():

    @staticmethod
    def get_configuration_for_form(review_form_id):
        config = (db.session.query(ReviewConfiguration)
                    .filter_by(review_form_id=review_form_id)
                    .first())
        return config

    @staticmethod
    def get_configuration_for_event(event_id):
        config = (db.session.query(ReviewConfiguration)
                    .join(ReviewForm, ReviewConfiguration.review_form_id == ReviewForm.id)
                    .filter_by(active=True)
                    .join(ApplicationForm, ReviewForm.application_form_id == ApplicationForm.id)
                    .filter(ApplicationForm.event_id == event_id)
                    .first())
        return config

