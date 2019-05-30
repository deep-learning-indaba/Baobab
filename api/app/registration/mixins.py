from flask_restful import reqparse

class RegistrationMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=True)
