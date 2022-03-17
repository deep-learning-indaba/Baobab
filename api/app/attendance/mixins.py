from flask_restful import reqparse


class AttendanceMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument("event_id", type=int, required=True)
    req_parser.add_argument("user_id", type=int, required=True)
