from flask_restful import reqparse


class EventMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('name', type=str, required=True)
    req_parser.add_argument('description', type=str, required=True)
    req_parser.add_argument('start_date', type=str, required=True)
    req_parser.add_argument('end_date', type=str, required=True)


class EventsMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
