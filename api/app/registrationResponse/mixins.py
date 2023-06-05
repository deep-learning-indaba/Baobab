from flask_restful import reqparse
from flask_restplus import inputs


class RegistrationAdminMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('exclude_already_signed_in',
                            type=inputs.boolean, required=False)
    req_parser.add_argument('include_guests',
                            type=inputs.boolean, required=False)


class RegistrationConfirmMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('registration_id', type=int, required=True)
