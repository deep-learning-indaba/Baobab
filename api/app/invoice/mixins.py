from flask_restful import reqparse

class InvoiceMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=True)

class InvoiceAdminMixin(object):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('event_id', type=int, required=True)