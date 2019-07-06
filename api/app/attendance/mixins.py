from flask_restful import reqparse

class PostAttendanceMixin(object):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('event_id', type=int, required=True)
    post_req_parser.add_argument('user_id', type=int, required=True)