from flask_restful import reqparse


class SignupMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('firstname', type=str, required=True)
    req_parser.add_argument('lastname', type=str, required=True)
    req_parser.add_argument('user_title', type=str, required=True)
    req_parser.add_argument('nationality_country_id', type=int, required=True)
    req_parser.add_argument('residence_country_id', type=int, required=True)
    req_parser.add_argument('user_ethnicity', type=str, required=True)
    req_parser.add_argument('user_gender', type=str, required=True)
    req_parser.add_argument('affiliation', type=str, required=True)
    req_parser.add_argument('department', type=str, required=True)
    req_parser.add_argument('user_disability', type=str, required=True)
    req_parser.add_argument('user_category_id', type=int, required=True)
    req_parser.add_argument('user_primaryLanguage', type=str, required=True)
    req_parser.add_argument('user_dateOfBirth', type=datetime, required=True)
    req_parser.add_argument('password', type=str, required=True)

class AuthenticateMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('password', type=str, required=True)