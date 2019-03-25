import flask_restful as restful

from app.reviews.models import ReviewForm, ReviewQuestion, ReviewResponse, ReviewScore

class ReviewAPI(restful.Resource):
    def get(self):
        return 200