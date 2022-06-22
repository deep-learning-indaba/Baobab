from email.charset import add_charset
from flask_restful import reqparse

class InvoiceMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('invoice_id', type=int, required=True)

class InvoiceListMixin(object):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('event_id', type=int, required=True)
    post_parser.add_argument('offer_ids', type=int, required=True, action='append')
    post_parser.add_argument('event_fee_ids', type=int, required=True, action='append')

class InvoiceAdminMixin(object):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('event_id', type=int, required=True)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('event_id', type=int, required=True)
    post_parser.add_argument('user_id', type=int, required=True)
    post_parser.add_argument('event_fee_ids', type=int, required=True, action='append')

class PaymentsMixin(object):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('invoice_id', type=int, required=True)

class PaymentsWebhookMixin(object):
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('Stripe-Signature', type=str, location='headers')
