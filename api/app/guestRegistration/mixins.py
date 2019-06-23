from flask_restful import reqparse


class GuestRegistrationMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('registration_id', type=int, required=False)
    req_parser.add_argument('registration_form_id', type=int, required=True)
    req_parser.add_argument('answers', type=list, required=True, location='json')