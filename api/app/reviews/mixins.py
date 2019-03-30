from flask_restful import reqparse

class ReviewMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('skip', type=int, required=False)


class GetReviewResponseMixin(object):
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('review_form_id', type=int, required=True)
    get_req_parser.add_argument('response_id', type=int, required=True)


class PostReviewResponseMixin(object):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('review_form_id', type=int, required=True)
    post_req_parser.add_argument('response_id', type=int, required=True)
    post_req_parser.add_argument('scores', type=dict, required=True, action='append')
