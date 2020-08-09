from flask_restful import reqparse
from flask_restful.inputs import boolean


class SignupMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('firstname', type=str, required=True)
    req_parser.add_argument('lastname', type=str, required=True)
    req_parser.add_argument('user_title', type=str, required=True)
    req_parser.add_argument('password', type=str, required=False)
    req_parser.add_argument('policy_agreed', type=boolean, required=True)
    req_parser.add_argument('language', type=str, required=True)

    put_req_parser = reqparse.RequestParser()
    put_req_parser.add_argument('email', type=str, required=True)
    put_req_parser.add_argument('firstname', type=str, required=True)
    put_req_parser.add_argument('lastname', type=str, required=True)
    put_req_parser.add_argument('user_title', type=str, required=True)
    put_req_parser.add_argument('language', type=str, required=True)
    put_req_parser.add_argument('password', type=str, required=False)


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


class PrivacyPolicyMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('policy_agreed', type=boolean, required=True)

class EventAttendeeMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
