from flask_restful import reqparse


class SignupLoginMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True, )
    req_parser.add_argument('firstname', type=str, required=True)
    req_parser.add_argument('lastname', type=str, required=True),
    req_parser.add_argument('user_title_id', type=int, required=True)
    req_parser.add_argument('nationality_id', type=int, required=True)
    req_parser.add_argument('residence_id', type=int, required=True)
    req_parser.add_argument('user_ethnicity_id', type=int, required=True)
    req_parser.add_argument('user_gender_id', type=int, required=True)
    req_parser.add_argument('affiliation', type=str, required=True)
    req_parser.add_argument('department', type=str, required=True)
    req_parser.add_argument('user_disability_id', type=int, required=True)
    req_parser.add_argument('user_category_id', type=int, required=True)
    req_parser.add_argument('password', type=str, required=True)
