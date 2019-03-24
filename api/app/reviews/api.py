import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with

from app import db
from app.applicationModel.models import ApplicationForm
from app.reviews.mixins import ReviewMixin
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND

review_form_fields = {
    'id': fields.Integer,
    'application_form_id': fields.Integer,
    'is_open': fields.Boolean,
    'deadline': fields.DateTime('iso8601')
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