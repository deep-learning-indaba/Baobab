import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with

from app import db
from app.applicationModel.models import ApplicationForm
from app.reviews.mixins import ReviewMixin
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore
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

class ReviewAPI(ReviewMixin, restful.Resource):

    @auth_required
    @marshal_with(review_form_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']

        review_form = db.session.query(ReviewForm)\
                        .join(ApplicationForm, ApplicationForm.id==ReviewForm.application_form_id)\
                        .filter_by(event_id=event_id)\
                        .first()
        if review_form is None:
            return EVENT_NOT_FOUND

        return review_form