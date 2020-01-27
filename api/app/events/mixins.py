from flask_restful import reqparse


class EventsMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)

class EventsKeyMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_key', type=str, required=True)
