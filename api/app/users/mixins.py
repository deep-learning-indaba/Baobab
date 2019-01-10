from flask.ext.restful import reqparse


class SignupLoginMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('email', type=str, required=True)
    req_parser.add_argument('password', type=str, required=True)
