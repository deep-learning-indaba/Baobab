from flask_restful import reqparse

class ReviewMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('skip', type=int, required=False)
    req_parser.add_argument('language', type=str, required=True)

class GetReviewResponseMixin(object):
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('id', type=int, required=True)
    get_req_parser.add_argument('language', type=str, required=True)

class PostReviewResponseMixin(object):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('review_form_id', type=int, required=True)
    post_req_parser.add_argument('response_id', type=int, required=True)
    post_req_parser.add_argument('scores', type=dict, required=True, action='append')
    post_req_parser.add_argument('language', type=str, required=True)
    post_req_parser.add_argument('is_submitted', type=bool, required=True)

class GetReviewAssignmentMixin(object):
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('event_id', type=int, required=True)
    get_req_parser.add_argument('response_id', type=int, required=True)

class PostReviewAssignmentMixin(object):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('reviewer_user_email', type=str, required=True)
    post_req_parser.add_argument('num_reviews', type=int, required=True)
    post_req_parser.add_argument('tags', type=int, action="append", location='json')

class GetReviewHistoryMixin(object):
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('event_id', type = int, required = True)
    get_req_parser.add_argument('page_number', type = int, required = True)
    get_req_parser.add_argument('limit', type = int, required = True)
    get_req_parser.add_argument('sort_column', type = str, required = True)