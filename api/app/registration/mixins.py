from flask_restful import reqparse


class OfferMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('event_id', type=int, required=False)
    req_parser.add_argument('offer_id', type=int, required=False)
    req_parser.add_argument('user_id', type=int, required=False)
    req_parser.add_argument('offer_date', type=str, required=False)
    req_parser.add_argument('expiry_date', type=str, required=False)
    req_parser.add_argument('payment_required', type=bool, required=False)
    req_parser.add_argument('travel_award', type=bool, required=False)
    req_parser.add_argument('accommodation_award', type=bool, required=False)
    req_parser.add_argument('rejected_reason', type=str, required=False)
    req_parser.add_argument('candidate_response', type=bool, required=False)
    req_parser.add_argument('responded_at', type=str, required=False)


class RegistrationFormMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('offer_id', type=int, required=False)


class RegistrationSectionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('section_id', type=int, required=False)
    req_parser.add_argument('registration_form_id', type=str, required=False)
    req_parser.add_argument('name', type=str, required=False)
    req_parser.add_argument('description', type=str, required=False)
    req_parser.add_argument('order', type=int, required=False)
    req_parser.add_argument('show_for_travel_award', type=bool, required=False)
    req_parser.add_argument('show_for_accommodation_award', type=bool, required=False)
    req_parser.add_argument('show_for_payment_required', type=bool, required=False)


class RegistrationQuestionMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('question_id', type=int, required=False, )
    req_parser.add_argument('section_id', type=int, required=False)
    req_parser.add_argument('registration_form_id', type=int, required=False)
    req_parser.add_argument('headline', type=str, required=False)
    req_parser.add_argument('description', type=str, required=False)
    req_parser.add_argument('order', type=int, required=False)
    req_parser.add_argument('validation_regex', type=str, required=False)
    req_parser.add_argument('validation_text', type=str, required=False)
    req_parser.add_argument('options', type=str, required=False)
    req_parser.add_argument('is_required', type=bool, required=False)
