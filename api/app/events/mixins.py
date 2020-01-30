from flask_restful import reqparse


class EventMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('name', type=str, required=True)
    req_parser.add_argument('description', type=str, required=True)
    req_parser.add_argument('start_date', type=str, required=True)
    req_parser.add_argument('end_date', type=str, required=True)
    req_parser.add_argument('key', type=str, required=True)
    req_parser.add_argument('organisation_id', type=int, required=False)
    req_parser.add_argument('email_from', type=str, required=True)
    req_parser.add_argument('url', type=str, required=True)
    req_parser.add_argument('application_open', type=str, required=True)
    req_parser.add_argument('application_close', type=str, required=True)
    req_parser.add_argument('review_open', type=str, required=True)
    req_parser.add_argument('review_close', type=str, required=True)
    req_parser.add_argument('selection_open', type=str, required=True)
    req_parser.add_argument('selection_close', type=str, required=True)
    req_parser.add_argument('offer_open', type=str, required=True)
    req_parser.add_argument('offer_close', type=str, required=True)
    req_parser.add_argument('registration_open', type=str, required=True)
    req_parser.add_argument('registration_close', type=str, required=True)


class EventsMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)


class EventsKeyMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_key', type=str, required=True)
