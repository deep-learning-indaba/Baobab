from flask_restful import reqparse


class ApplicationFormMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True, help = 'Invalid event_id requested. Event_id\'s should be of type int.')
    