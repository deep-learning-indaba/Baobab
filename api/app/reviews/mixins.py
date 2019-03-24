from flask_restful import reqparse

class ReviewMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('skip', type=int, required=False)