from datetime import datetime

from flask_restful import reqparse


class EventMixin(object):
    dt_format = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('name', type=dict, required=True, location='json')
    req_parser.add_argument('description', type=dict, required=True, location='json')
    req_parser.add_argument('start_date', type=dt_format, required=True)
    req_parser.add_argument('end_date', type=dt_format, required=True)
    req_parser.add_argument('key', type=str, required=True)
    req_parser.add_argument('organisation_id', type=int, required=True)
    req_parser.add_argument('email_from', type=str, required=True)
    req_parser.add_argument('url', type=str, required=True)
    req_parser.add_argument('application_open', type=dt_format, required=True)
    req_parser.add_argument('application_close', type=dt_format, required=True)
    req_parser.add_argument('review_open', type=dt_format, required=True)
    req_parser.add_argument('review_close', type=dt_format, required=True)
    req_parser.add_argument('selection_open', type=dt_format, required=True)
    req_parser.add_argument('selection_close', type=dt_format, required=True)
    req_parser.add_argument('offer_open', type=dt_format, required=True)
    req_parser.add_argument('offer_close', type=dt_format, required=True)
    req_parser.add_argument('registration_open', type=dt_format, required=True)
    req_parser.add_argument('registration_close', type=dt_format, required=True)
    req_parser.add_argument('event_type', type=str, required=True)
    req_parser.add_argument('travel_grant', type=bool, required=True)


class EventsMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)


class EventsKeyMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_key', type=str, required=True)
    req_parser.add_argument('language', type=str, required=False)
