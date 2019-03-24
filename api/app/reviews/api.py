from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with

from app import db
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response, ResponseReviewer
from app.reviews.mixins import ReviewMixin
from app.reviews.models import ReviewForm, ReviewResponse
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND

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
    'value': fields.String
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
    'user': fields.Nested(user_fields)
}

class ReviewResponseUser():
    def __init__(self, review_form, response):
        self.review_form = review_form
        self.response = response
        self.user = None if response is None else response.user

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

        skip = 0 if args['skip'] is None else args['skip']
        response = db.session.query(Response)\
                        .filter_by(is_withdrawn=False, application_form_id=review_form.application_form_id)\
                        .join(ResponseReviewer)\
                        .filter_by(user_id=g.current_user['id'])\
                        .outerjoin(ReviewResponse, ReviewResponse.response_id==ResponseReviewer.response_id)\
                        .filter_by(id=None)\
                        .order_by(ResponseReviewer.response_id)\
                        .offset(skip)\
                        .limit(1)\
                        .first()
        
        return ReviewResponseUser(review_form, response)