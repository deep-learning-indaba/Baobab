from flask_restful import reqparse


class ReferenceRequestsMixin(object):
    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('response_id', type=int, required=True)
    post_req_parser.add_argument('title', type=str, required=True)
    post_req_parser.add_argument('firstname', type=str, required=True)
    post_req_parser.add_argument('lastname', type=str, required=True)
    post_req_parser.add_argument('relation', type=str, required=True)
    post_req_parser.add_argument('email', type=str, required=True)
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('id', type=int, required=False)

class ReferenceRequestsListMixin(object):

    req_parser = reqparse.RequestParser()
    req_parser.add_argument('response_id', type=int, required=True)


class ReferenceMixin(object):

    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument('response_id', type=int, required=True)

    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument('token', type=str, required=True)
    post_req_parser.add_argument('uploaded_document', type=str, required=True)
