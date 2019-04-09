from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.sql import func
from sqlalchemy import and_, or_

from app import db, LOGGER
from app.applicationModel.models import ApplicationForm
from app.events.models import EventRole
from app.responses.models import Response, ResponseReviewer
from app.reviews.mixins import ReviewMixin, GetReviewResponseMixin, PostReviewResponseMixin, PostReviewAssignmentMixin, GetReviewAssignmentMixin
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore
from app.reviews.repository import ReviewRepository as review_repository
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND, REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND

option_fields = {
    'value': fields.String,
    'label': fields.String
}

review_question_fields = {
    'id': fields.Integer,
    'question_id': fields.Integer,
    'description': fields.String,
    'headline': fields.String,
    'type': fields.String,
    'placeholder': fields.String,
    'options': fields.List(fields.Nested(option_fields)),
    'is_required': fields.Boolean,
    'order': fields.Integer,
    'validation_regex': fields.String,
    'validation_text': fields.String,
    'weight': fields.Float
}

review_form_fields = {
    'id': fields.Integer,
    'application_form_id': fields.Integer,
    'is_open': fields.Boolean,
    'deadline': fields.DateTime('iso8601'),
    'review_questions': fields.List(fields.Nested(review_question_fields))
}

answer_fields = {
    'id': fields.Integer,
    'question_id': fields.Integer,
    'question': fields.String(attribute='question.headline'),
    'value': fields.String(attribute='value_display')
}

response_fields = {
    'id': fields.Integer,
    'application_form_id': fields.Integer,
    'user_id': fields.Integer,
    'is_submitted': fields.Boolean,
    'submitted_timestamp': fields.DateTime(dt_format='iso8601'),
    'is_withdrawn': fields.Boolean,
    'withdrawn_timestamp': fields.DateTime(dt_format='iso8601'),
    'started_timestamp': fields.DateTime(dt_format='iso8601'),
    'answers': fields.List(fields.Nested(answer_fields))
}

user_fields = {
    'nationality_country': fields.String(attribute='nationality_country.name'),
    'residence_country': fields.String(attribute='residence_country.name'),
    'affiliation': fields.String,
    'department': fields.String,
    'user_category': fields.String(attribute='user_category.name')
}

review_response_fields = {
    'review_form': fields.Nested(review_form_fields),
    'response': fields.Nested(response_fields),
    'user': fields.Nested(user_fields),
    'reviews_remaining_count': fields.Integer
}

class ReviewResponseUser():
    def __init__(self, review_form, response, reviews_remaining_count):
        self.review_form = review_form
        self.response = response
        self.user = None if response is None else response.user
        self.reviews_remaining_count = reviews_remaining_count

class ReviewAPI(ReviewMixin, restful.Resource):

    @auth_required
    @marshal_with(review_response_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        
        review_form = db.session.query(ReviewForm)\
                        .join(ApplicationForm, ApplicationForm.id==ReviewForm.application_form_id)\
                        .filter_by(event_id=event_id)\
                        .first()
        if review_form is None:
            return EVENT_NOT_FOUND

        reviews_remaining_count = db.session.query(func.count(ResponseReviewer.id))\
                        .filter_by(reviewer_user_id=g.current_user['id'])\
                        .join(Response)\
                        .filter_by(is_withdrawn=False, application_form_id=review_form.application_form_id, is_submitted=True)\
                        .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==g.current_user['id']))\
                        .filter_by(id=None)\
                        .all()[0][0]

        skip = self.sanitise_skip(args['skip'], reviews_remaining_count)

        response = db.session.query(Response)\
                        .filter_by(is_withdrawn=False, application_form_id=review_form.application_form_id, is_submitted=True)\
                        .join(ResponseReviewer)\
                        .filter_by(reviewer_user_id=g.current_user['id'])\
                        .outerjoin(ReviewResponse, and_(ReviewResponse.response_id==ResponseReviewer.response_id, ReviewResponse.reviewer_user_id==g.current_user['id']))\
                        .filter_by(id=None)\
                        .order_by(ResponseReviewer.response_id)\
                        .offset(skip)\
                        .first()
        
        return ReviewResponseUser(review_form, response, reviews_remaining_count)

    def sanitise_skip(self, skip, reviews_remaining_count):
        if skip is None:
            skip = 0

        if skip < 0:
            skip = 0

        if reviews_remaining_count == 0:
            skip = 0
        elif skip >= reviews_remaining_count:
            skip = reviews_remaining_count - 1
        
        return skip


review_scores_fields = {
    'review_question_id': fields.Integer,
    'value': fields.String
}

review_response_fields = {
    'id': fields.Integer,
    'review_form_id': fields.Integer,
    'response_id': fields.Integer,
    'reviewer_user_id': fields.Integer,
    'scores': fields.List(fields.Nested(review_scores_fields), attribute='review_scores')
}

class ReviewResponseAPI(GetReviewResponseMixin, PostReviewResponseMixin, restful.Resource):

    @auth_required
    @marshal_with(review_response_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        review_form_id = args['review_form_id']
        response_id = args['response_id']
        reviewer_user_id = g.current_user['id']

        review_response = db.session.query(ReviewResponse)\
                            .filter_by(review_form_id=review_form_id, response_id=response_id, reviewer_user_id=reviewer_user_id)\
                            .first()
        if review_response is None:
            return REVIEW_RESPONSE_NOT_FOUND

        return review_response

    @auth_required
    def post(self):
        args = self.post_req_parser.parse_args()
        validation_result = self.validate_scores(args['scores'])
        if validation_result is not None:
            return validation_result

        response_id = args['response_id']
        review_form_id = args['review_form_id']
        reviewer_user_id = g.current_user['id']
        scores = args['scores']

        response_reviewer = self.get_response_reviewer(response_id, reviewer_user_id)
        if response_reviewer is None:
            return FORBIDDEN

        review_response = ReviewResponse(review_form_id, reviewer_user_id, response_id)
        review_response.review_scores = self.get_review_scores(scores)
        db.session.add(review_response)
        db.session.commit()

        return {}, 201

    @auth_required
    def put(self):
        args = self.post_req_parser.parse_args()
        validation_result = self.validate_scores(args['scores'])
        if validation_result is not None:
            return validation_result
        
        response_id = args['response_id']
        review_form_id = args['review_form_id']
        reviewer_user_id = g.current_user['id']
        scores = args['scores']

        response_reviewer = self.get_response_reviewer(response_id, reviewer_user_id)
        if response_reviewer is None:
            return FORBIDDEN

        review_response = self.get_review_response(review_form_id, response_id, reviewer_user_id)
        if review_response is None:
            return REVIEW_RESPONSE_NOT_FOUND
        
        db.session.query(ReviewScore).filter(ReviewScore.review_response_id==review_response.id).delete()
        review_response.review_scores = self.get_review_scores(scores)
        db.session.commit()

        return {}, 200
    
    def get_response_reviewer(self, response_id, reviewer_user_id):
        return db.session.query(ResponseReviewer)\
                         .filter_by(response_id=response_id, reviewer_user_id=reviewer_user_id)\
                         .first()

    def get_review_response(self, review_form_id, response_id, reviewer_user_id):
        return db.session.query(ReviewResponse)\
                         .filter_by(review_form_id=review_form_id, response_id=response_id, reviewer_user_id=reviewer_user_id)\
                         .first()
    
    def get_review_scores(self, scores):
        review_scores = []
        for score in scores:
            review_score = ReviewScore(score['review_question_id'], score['value'])
            review_scores.append(review_score)
        return review_scores
    
    def validate_scores(self, scores):
        for score in scores:
            if 'review_question_id' not in score.keys():
                return self.get_error_message('review_question_id')
            if 'value' not in score.keys():
                return self.get_error_message('value')
    
    def get_error_message(self, key):
        return ({'message': {key: 'Missing required parameter in the JSON body or the post body or the query string'}}, 400)


class ReviewCountView():
    def __init__(self, count):
        self.email = count.email.encode('utf-8')
        self.user_title = count.user_title
        self.firstname = count.firstname
        self.lastname = count.lastname
        self.reviews_allocated = count.reviews_allocated
        self.reviews_completed = count.reviews_completed


class ReviewAssignmentAPI(GetReviewAssignmentMixin, PostReviewAssignmentMixin, restful.Resource):
    
    reviews_count_fields = {
        'email': fields.String,
        'user_title': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'reviews_allocated': fields.Integer,
        'reviews_completed': fields.Integer
    }

    @auth_required
    @marshal_with(reviews_count_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        counts = review_repository.count_reviews_allocated_and_completed_per_reviewer(event_id)
        views = [ReviewCountView(count) for count in counts]
        return views
        

    @auth_required
    def post(self):
        args = self.post_req_parser.parse_args()
        user_id = g.current_user['id']
        event_id = args['event_id']
        reviewer_user_email = args['reviewer_user_email']
        num_reviews = args['num_reviews']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN
        
        reviewer_user = user_repository.get_by_email(reviewer_user_email)
        if reviewer_user is None:
            return USER_NOT_FOUND
        
        if not reviewer_user.is_reviewer(event_id):
            self.add_reviewer_role(reviewer_user.id, event_id)

        response_ids = self.get_eligible_response_ids(reviewer_user.id, num_reviews)
        response_reviewers = [ResponseReviewer(response_id, reviewer_user.id) for response_id in response_ids]
        db.session.add_all(response_reviewers)
        db.session.commit()
        
        return {}, 201

    
    def add_reviewer_role(self, user_id, event_id):
        event_role = EventRole('reviewer', user_id, event_id)
        db.session.add(event_role)
        db.session.commit()
    
    def get_eligible_response_ids(self, reviewer_user_id, num_reviews):
        responses = db.session.query(Response.id)\
                         .filter(Response.user_id != reviewer_user_id, Response.is_submitted==True, Response.is_withdrawn==False)\
                         .outerjoin(ResponseReviewer, Response.id==ResponseReviewer.response_id)\
                         .filter(or_(ResponseReviewer.reviewer_user_id != reviewer_user_id, ResponseReviewer.id == None))\
                         .group_by(Response.id)\
                         .having(func.count(ResponseReviewer.reviewer_user_id) < 3)\
                         .limit(num_reviews)\
                         .all()
        
        return list(map(lambda response: response[0], responses))