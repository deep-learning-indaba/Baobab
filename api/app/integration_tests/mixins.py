from flask_restful import reqparse


class IntegratoonTestDelete(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument("email", type=str, required=True)
