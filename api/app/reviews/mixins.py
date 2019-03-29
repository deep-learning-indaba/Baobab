from flask_restful import reqparse

class ReviewMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('skip', type=int, required=False)


class ReviewResponseMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('review_form_id', type=int, required=True)
    req_parser.add_argument('response_id', type=int, required=True)