import flask_restful as restful
from flask import g

from app.events.repository import EventRepository as event_repository
from app.invoice.mixins import InvoiceMixin, InvoiceAdminMixin
from app.invoice.models import Invoice, InvoiceLineItem
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.registration.repository import OfferRepository as offer_repository
from app.users.repository import UserRepository as user_repository
from app.utils.errors import FORBIDDEN, OFFER_NOT_FOUND, EVENT_FEE_NOT_FOUND, EVENT_FEES_MUST_HAVE_SAME_CURRENCY
from app.utils.auth import auth_required
from app.utils.exceptions import BaobabError


class InvoiceAPI(InvoiceMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        invoice_id = args['invoice_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        invoice = invoice_repository.get_one_for_customer(invoice_id, current_user.email)
        return invoice, 200

    @auth_required
    def delete(self):
        args = self.req_parser.parse_args()

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)
        invoice = invoice_repository.get_one_for_customer(args['invoice_id'], current_user.email)

        try:
            invoice.cancel(user_id)
            invoice_repository.save(invoice)
        except BaobabError as be:
            return {'message': be.message}, 403

        return 200


class InvoiceListAPI(restful.Resource):
    @auth_required
    def get(self):
        current_user = user_repository.get_by_id(g.current_user["id"])
        invoices = invoice_repository.get_all_for_customer(current_user.email)
        return invoices, 200

    @auth_required
    def post(self):
        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN


class InvoiceAdminAPI(InvoiceAdminMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.get_parser.parse_args()
        event_id = args['event_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN

        invoices = invoice_repository.get_for_event(event_id)
        return invoices, 200

    @auth_required
    def post(self):
        args = self.get_parser.parse_args()
        event_id = args['event_id']
        user_id = args['offer_id']
        event_fee_ids = args['event_fee_ids']

        current_user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(current_user_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN

        offer = offer_repository.get_by_user_id_for_event(user_id, event_id)
        if not offer:
            return OFFER_NOT_FOUND

        event_fees = event_repository.get_event_fees(event_id, event_fee_ids)
        if not event_fees:
            return EVENT_FEE_NOT_FOUND
        
        iso_currency_codes = set([event_fee.iso_currency_code for event_fee in event_fees])
        if len(iso_currency_codes) > 1:
            return EVENT_FEES_MUST_HAVE_SAME_CURRENCY
        iso_currency_code = list(iso_currency_codes)[0]
        
        line_items = []
        for event_fee in event_fees:
            line_item = InvoiceLineItem(event_fee.name, event_fee.description, event_fee.amount)
            line_items.append(line_item)
        
        user = user_repository.get_by_id(user_id)
        
        invoice = Invoice(user.email, iso_currency_code, line_items, current_user_id, user_id)
        invoice_repository.save(invoice)
        return invoice, 201
    
    @auth_required
    def put(self):
        # update success/fail from webhook
        return 200