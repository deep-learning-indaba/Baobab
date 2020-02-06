from flask_restful import reqparse


class SignupMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('firstname', type=str, required=True)
    req_parser.add_argument('lastname', type=str, required=True)
    req_parser.add_argument('user_title', type=str, required=True)
    req_parser.add_argument('password', type=str, required=False)
    req_parser.add_argument('policy_agreed', type=bool, required=True)


class AuthenticateMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('password', type=str, required=True)


class UserProfileListMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)


class UserProfileMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('user_id', type=int, required=True)
