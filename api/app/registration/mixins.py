from flask_restful import reqparse


class RegistrationFormMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('offer_id', type=int, required=False)


class RegistrationSectionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('section_id', type=int, required=True)


class RegistrationQuestionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('question_id', type=int, required=True)
