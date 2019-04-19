from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from math import ceil

from app import db, LOGGER
from app.applicationModel.models import ApplicationForm
from app.events.models import EventRole
from app.responses.models import Response, ResponseReviewer
from app.reviews.mixins import ReviewMixin, GetReviewResponseMixin, PostReviewResponseMixin, PostReviewAssignmentMixin, GetReviewAssignmentMixin, GetReviewHistoryMixin, GetReviewSummaryMixin
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore, ReviewQuestion
from app.reviews.repository import ReviewRepository as review_repository
from app.users.models import AppUser, Country, UserCategory
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

review_fields = {
    'review_form': fields.Nested(review_form_fields),
    'response': fields.Nested(response_fields),
    'user': fields.Nested(user_fields),
    'reviews_remaining_count': fields.Integer,
    'review_response': fields.Nested(review_response_fields)
}

REVIEWS_PER_SUBMISSION = 3

class ReviewResponseUser():
    def __init__(self, review_form, response, reviews_remaining_count, review_response=None):
        self.review_form = review_form
        self.response = response
        self.user = None if response is None else response.user
        self.reviews_remaining_count = reviews_remaining_count
        self.review_response = review_response

class ReviewAPI(ReviewMixin, restful.Resource):

    @auth_required
    @marshal_with(review_fields)
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


class ReviewResponseAPI(GetReviewResponseMixin, PostReviewResponseMixin, restful.Resource):

    @auth_required
    @marshal_with(review_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        id = args['id']
        reviewer_user_id = g.current_user['id']

        review_form_response = db.session.query(ReviewForm, ReviewResponse)\
                                            .join(ReviewResponse)\
                                            .filter_by(id=id, reviewer_user_id=reviewer_user_id)\
                                            .first()

        if review_form_response is None:
            return REVIEW_RESPONSE_NOT_FOUND


        review_form, review_response = review_form_response

        response = db.session.query(Response)\
                        .filter_by(is_withdrawn=False, application_form_id=review_form.application_form_id, is_submitted=True)\
                        .join(ResponseReviewer)\
                        .filter_by(reviewer_user_id=g.current_user['id'])\
                        .join(ReviewResponse)\
                        .filter_by(id=id)\
                        .first()

        return ReviewResponseUser(review_form, response, 0, review_response)

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
        self.email = count.email
        self.user_title = count.user_title
        self.firstname = count.firstname
        self.lastname = count.lastname
        self.reviews_allocated = count.reviews_allocated
        self.reviews_completed = count.reviews_completed

class ReviewSummaryAPI(GetReviewSummaryMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        return {
            'reviews_unallocated': review_repository.count_unassigned_reviews(event_id, REVIEWS_PER_SUBMISSION)
        }

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
        LOGGER.debug(views)
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
                        .having(func.count(ResponseReviewer.reviewer_user_id) < REVIEWS_PER_SUBMISSION)\
                        .limit(num_reviews)\
                        .all()
        return list(map(lambda response: response[0], responses))

review_fields = {
    'review_response_id' : fields.Integer,
    'submitted_timestamp' : fields.DateTime(dt_format='iso8601'),
    'nationality_country' : fields.String,
    'residence_country' : fields.String, 
    'affiliation' : fields.String, 
    'department' : fields.String,
    'user_category' : fields.String, 
    'final_verdict' : fields.String,
}

review_histroy_fields = {
    'reviews' : fields.List(fields.Nested(review_fields)),
    'num_entries' : fields.Integer,
    'current_pagenumber' : fields.Integer,
    'total_pages' : fields.Integer
}

class ReviewHistoryModel:
    def __init__(self, review):
        self.review_response_id = review.id
        self.submitted_timestamp = review.submitted_timestamp
        self.nationality_country = review.AppUser.nationality_country.name
        self.residence_country = review.AppUser.residence_country.name
        self.affiliation = review.AppUser.affiliation
        self.department = review.AppUser.department
        self.user_category = review.AppUser.user_category.name

        final_verdict = [o for o in review.options if str(o['value']) == review.value]
        final_verdict = final_verdict[0]['label'] if final_verdict else "Unknown"
        self.final_verdict = final_verdict

class ReviewHistoryAPI(GetReviewHistoryMixin, restful.Resource):
    
    @auth_required
    @marshal_with(review_histroy_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        user_id = g.current_user['id']
        event_id =args['event_id']
        page_number = args['page_number']
        limit = args['limit']
        sort_column = args['sort_column']

        reviewer = db.session.query(AppUser).get(user_id).is_reviewer(event_id)
        if not reviewer:
            return FORBIDDEN

        form_id = db.session.query(ApplicationForm.id).filter_by(event_id = event_id).first()[0]

        reviews = (db.session.query(ReviewResponse.id, ReviewResponse.submitted_timestamp, AppUser, ReviewScore.value, ReviewQuestion.options)
                        .filter(ReviewResponse.reviewer_user_id == user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.application_form_id == form_id)
                        .join(Response, ReviewResponse.response_id == Response.id)
                        .join(ReviewQuestion, ReviewForm.id == ReviewQuestion.review_form_id)
                        .filter(ReviewQuestion.headline == 'Final Verdict')
                        .join(ReviewScore, and_(ReviewQuestion.id == ReviewScore.review_question_id, ReviewResponse.id == ReviewScore.review_response_id))
                        .join(AppUser, Response.user_id == AppUser.id))

        if sort_column == 'review_response_id':
            reviews = reviews.order_by(ReviewResponse.id)
        
        if sort_column == 'submitted_timestamp':
            reviews = reviews.order_by(ReviewResponse.submitted_timestamp)
        
        if sort_column == 'nationality_country':
            reviews = reviews.join(Country, AppUser.nationality_country_id == Country.id).order_by(Country.name)

        if sort_column == 'residence_country':
            reviews = reviews.join(Country, AppUser.residence_country_id == Country.id).order_by(Country.name)

        if sort_column == 'affiliation':
            reviews = reviews.order_by(AppUser.affiliation)

        if sort_column == 'department':
            reviews = reviews.order_by(AppUser.department)
        
        if sort_column == 'user_category':
            reviews = reviews.join(UserCategory, AppUser.user_category_id == UserCategory.id).order_by(UserCategory.name)
  
        if sort_column == 'final_verdict':
                reviews = reviews.order_by(ReviewScore.value)

        reviews = reviews.slice(page_number*limit, page_number*limit + limit).all()

        num_entries = (db.session.query(ReviewResponse)
                        .filter(ReviewResponse.reviewer_user_id == user_id)
                        .join(ReviewForm, ReviewForm.id == ReviewResponse.review_form_id)
                        .filter(ReviewForm.application_form_id == form_id)
                        .count())

        total_pages = ceil(float(num_entries)/limit)

        LOGGER.debug(reviews)
        reviews = [ReviewHistoryModel(review) for review in reviews]
        return {'reviews': reviews, 'num_entries': num_entries, 'current_pagenumber': page_number, 'total_pages': total_pages}