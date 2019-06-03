from flask_restful import reqparse


class RegistrationFormMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('offer_id', type=int, required=False)


class RegistrationSectionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('registration_form_id', type=int, required=True)
    req_parser.add_argument('name', type=int, required=True)
    req_parser.add_argument('description', type=int, required=True)
    req_parser.add_argument('order', type=int, required=True)
    req_parser.add_argument('show_for_travel_award', type=int, required=True)
    req_parser.add_argument('show_for_accommodation_award', type=int, required=True)
    req_parser.add_argument('show_for_payment_required', type=int, required=True)


class RegistrationQuestionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('registration_form_id', type=int, required=True)
    req_parser.add_argument('section_id', type=int, required=True)
    req_parser.add_argument('description', type=int, required=True)
    req_parser.add_argument('headline', type=int, required=True)
    req_parser.add_argument('placeholder', type=int, required=True)
    req_parser.add_argument('validation_regex', type=int, required=False)
    req_parser.add_argument('validation_text', type=int, required=False)
    req_parser.add_argument('order', type=int, required=True)
    req_parser.add_argument('options', type=int, required=False)
    req_parser.add_argument('is_required', type=int, required=True)
