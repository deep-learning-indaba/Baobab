from flask_restful import reqparse
from flask_restplus import inputs


class RegistrationResponseMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument("registration_id", type=int, required=False)
    req_parser.add_argument("offer_id", type=int, required=True)
    req_parser.add_argument("registration_form_id", type=int, required=True)
    req_parser.add_argument("answers", type=list, required=True, location="json")


class RegistrationAdminMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument("event_id", type=int, required=True)
    req_parser.add_argument(
        "exclude_already_signed_in", type=inputs.boolean, required=False
    )


class RegistrationConfirmMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument("registration_id", type=int, required=True)
