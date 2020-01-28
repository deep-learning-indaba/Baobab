from flask_restful import reqparse


class ReferenceRequestsFormMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('response_id', type=int, required=True)
    req_parser.add_argument('title', type=str, required=True)
    req_parser.add_argument('firstname', type=str, required=True)
    req_parser.add_argument('lastname', type=str, required=True)
    req_parser.add_argument('relation', type=str, required=True)
    req_parser.add_argument('email', type=str, required=True)

class ReferenceRequestsMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=True)

class ReferenceRequestsListMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('response_id', type=int, required=True)
