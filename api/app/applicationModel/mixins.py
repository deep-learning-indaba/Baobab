from flask_restful import reqparse


class ApplicationFormMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True, help = 'Invalid event_id requested. Event_id\'s should be of type int.')
    req_parser.add_argument('is_open', type=bool, required=True)
    req_parser.add_argument('nominations', type=bool, required=True)
    req_parser.add_argument('sections', type=dict, required=True, action='append')
    req_parser.add_argument('questions', type=dict, required=True, action='append')