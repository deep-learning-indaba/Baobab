from flask_restful import reqparse


class InvitationMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('registration_id', type=int, required=False)
    req_parser.add_argument('event_id', type=int, required=False)
    req_parser.add_argument('work_address', type=str, required=False)
    req_parser.add_argument('addressed_to', type=str, required=False)
    req_parser.add_argument('residential_address', type=str, required=False)
    req_parser.add_argument('passport_name', type=str, required=False)
    req_parser.add_argument('passport_no', type=str, required=False)
    req_parser.add_argument('passport_issued_by', type=str, required=False)
    req_parser.add_argument('passport_expiry_date', type=str, required=False)
    req_parser.add_argument('to_date', type=str, required=False)
    req_parser.add_argument('from_date', type=str, required=False)
    req_parser.add_argument('date_of_birth', type=str, required=False)
    req_parser.add_argument('country_of_residence', type=str, required=False)
    req_parser.add_argument('country_of_nationality', type=str, required=False)
