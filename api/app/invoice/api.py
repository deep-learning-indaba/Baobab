from datetime import datetime

import flask_restful as restful
from flask_restful import fields, marshal
from flask import g, request
import stripe

from app import LOGGER
from app.events.repository import EventRepository as event_repository
from app.invoice.mixins import InvoiceMixin, InvoiceAdminMixin, PaymentsMixin, PaymentsWebhookMixin
from app.invoice.models import InvoicePaymentStatus, PaymentStatus, StripeWebhookEvent
from app.invoice import service as invoice_service
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.offer.repository import OfferRepository as offer_repository
from app.users.repository import UserRepository as user_repository
from app.offer import api as offer_api

from app.utils.errors import (
    FORBIDDEN,
    OFFER_NOT_FOUND,
    EVENT_FEE_NOT_FOUND,
    EVENT_FEES_MUST_HAVE_SAME_CURRENCY,
    INVOICE_PAID,
    INVOICE_CANCELED,
    INVOICE_NOT_FOUND,
    INVOICE_MUST_HAVE_FUTURE_DATE,
    INVOICE_OVERDUE,
    INVOICE_NEGATIVE)
from app.utils.auth import auth_required
from app.utils.exceptions import BaobabError

invoice_payment_intent_fields = {
    'id': fields.Integer,
    'payment_intent': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'has_session_expired': fields.Boolean
}

invoice_payment_status_fields = {
    'id': fields.Integer,
    'payment_status': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'created_at_unix': fields.Float,
    'created_by_user_id': fields.Integer(default=None),
    'created_by': fields.String(attribute='created_by.full_name', default=None)
}

invoice_line_item_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String(default=None),
    'amount': fields.Float
}

invoice_fields = {
    'id': fields.Integer,
    'invoice_number': fields.String,
    'customer_email': fields.String,
    'customer_name': fields.String,
    'client_reference_id': fields.String,
    'iso_currency_code': fields.String,
    'due_date': fields.DateTime(dt_format='iso8601'),
    'is_overdue': fields.Boolean,
    'created_by_user_id': fields.Integer,
    'created_by_user': fields.String(attribute='created_by.full_name'),
    'created_at': fields.DateTime(dt_format='iso8601'),
    'total_amount': fields.Float,
    'current_payment_status': fields.String(attribute='current_payment_status.payment_status'),
    'offer_id': fields.Integer(default=None),
    'invoice_payment_statuses': fields.List(fields.Nested(invoice_payment_status_fields)),
    'invoice_line_items': fields.List(fields.Nested(invoice_line_item_fields)),
    'invoice_payment_intents': fields.List(fields.Nested(invoice_payment_intent_fields))
}

invoice_list_fields = {
    'id': fields.Integer,
    'invoice_number': fields.String,
    'customer_email': fields.String,
    'customer_name': fields.String,
    'client_reference_id': fields.String,
    'iso_currency_code': fields.String,
    'due_date': fields.DateTime(dt_format='iso8601'),
    'is_overdue': fields.Boolean,
    'created_by_user_id': fields.Integer,
    'created_by_user': fields.String(attribute='created_by.full_name'),
    'created_at': fields.DateTime(dt_format='iso8601'),
    'total_amount': fields.Float,
    'current_payment_status': fields.String(attribute='current_payment_status.payment_status')
}

invoice_payment_status_fields = {
    'id': fields.Integer,
    'payment_status': fields.String,
    'created_at_unix': fields.Integer
}

class InvoiceAPI(InvoiceMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        invoice_id = args['invoice_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        invoice = invoice_repository.get_one_for_customer(invoice_id, current_user.email)
        if invoice is None:
            return INVOICE_NOT_FOUND

        return marshal(invoice, invoice_fields), 200

class InvoicePaymentStatusApi(restful.Resource, InvoiceMixin):
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()

        payment_status = invoice_repository.get_latest_payment_status(
            args['invoice_id'],
            g.current_user['email']
        )

        if not payment_status:
            return INVOICE_NOT_FOUND

        return marshal(payment_status, invoice_payment_status_fields), 200

class InvoiceListAPI(restful.Resource):
    @auth_required
    def get(self):
        invoices = invoice_repository.get_all_for_user(g.current_user["id"])
        return marshal(invoices, invoice_list_fields), 200


class InvoiceAdminListAPI(InvoiceAdminMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.get_parser.parse_args()
        event_id = args['event_id']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN

        invoices = invoice_repository.get_for_event(event_id)
        invoices = [i for i in invoices if not i.is_canceled]
        return marshal(invoices,invoice_list_fields), 200


class InvoiceAdminAPI(InvoiceAdminMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.post_parser.parse_args()
        event_id = args['event_id']
        due_date = args['due_date']
        offer_ids = args['offer_ids']
        event_fee_ids = args['event_fee_ids']

        user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(user_id)
        event = event_repository.get_by_id(event_id)

        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN
        
        if due_date < datetime.now():
            return INVOICE_MUST_HAVE_FUTURE_DATE

        offers = offer_repository.get_offers_for_event(event_id, offer_ids)
        if not offers or (len(offer_ids) > len(offers)):
            return OFFER_NOT_FOUND

        event_fees = event_repository.get_event_fees(event_id, event_fee_ids)
        if not event_fees or (len(event_fee_ids) > len(event_fees)):
            return EVENT_FEE_NOT_FOUND

        iso_currency_codes = set([event_fee.iso_currency_code for event_fee in event_fees])
        if len(iso_currency_codes) > 1:
            return EVENT_FEES_MUST_HAVE_SAME_CURRENCY

        total_amount = sum([event_fee.amount for event_fee in event_fees])
        if total_amount < 0:
            return INVOICE_NEGATIVE

        invalid_offer_ids = []
        for offer in offers:
            if offer.has_valid_invoice() or offer.is_accepted():
                invalid_offer_ids.append(offer.id)
        
        if invalid_offer_ids:
            error_message = f"Offers {','.join(str(id) for id in invalid_offer_ids)} already have an invoice or are already accepted."
            return {'message': error_message}, 400

        invoices = []

        for offer in offers:
            invoice = invoice_service.issue_invoice_for_offer(offer, event_fees, due_date, user_id)
            invoices.append(invoice)

        return marshal(invoices, invoice_list_fields), 201

    @auth_required
    def put(self):
        args = self.put_parser.parse_args()
        event_id = args['event_id']
        invoice_id = args['invoice_id']
        action = args['action']

        current_user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(current_user_id)
        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN
        
        invoice = invoice_repository.get_one_from_event(event_id, invoice_id)
        if invoice is None:
            return INVOICE_NOT_FOUND
        
        try:
            if action == 'cancel':
                invoice.cancel(current_user_id)
                invoice_repository.save()
            elif action == 'mark_as_paid':
                invoice.mark_as_paid(current_user_id)
                if invoice.offer_id:
                    LOGGER.info(f"Invoice offer ID is {invoice.offer_id}")
                    offer = offer_repository.get_by_id(invoice.offer_id)
                    offer_api.confirm_offer_payment(offer)
                invoice_repository.save()
            else:
                return {'message': 'Invalid action'}, 400
        except BaobabError as be:
            return {'message': be.message}, 400  
        
        return marshal(invoice, invoice_fields), 200

    @auth_required
    def delete(self):
        args = self.delete_parser.parse_args()
        event_id = args['event_id']
        invoice_id = args['invoice_id']

        current_user_id = g.current_user["id"]
        current_user = user_repository.get_by_id(current_user_id)
        if not current_user.is_event_treasurer(event_id):
            return FORBIDDEN

        invoice = invoice_repository.get_one_from_event(event_id, invoice_id)
        if invoice is None:
            return INVOICE_NOT_FOUND

        try:
            invoice.cancel(current_user_id)
            invoice_repository.save()
        except BaobabError as be:
            return {'message': be.message}, 400

        return 200

payment_fields = {
    'url': fields.String,
    'payment_intent': fields.String,
    'amount_total': fields.Float
}
class PaymentsAPI(PaymentsMixin, restful.Resource):
    @auth_required
    def post(self):
        args = self.post_parser.parse_args()
        invoice_id = args['invoice_id']

        user_id = g.current_user["id"]
        invoice = invoice_repository.get_by_id(invoice_id)

        if not invoice:
            return INVOICE_NOT_FOUND

        if invoice.is_paid:
            return INVOICE_PAID

        if invoice.is_canceled:
            return INVOICE_CANCELED
        
        if invoice.is_overdue:
            return INVOICE_OVERDUE

        stripe.api_key = g.organisation.stripe_api_secret_key

        stripe_line_items = []
        for invoice_line_item in invoice.invoice_line_items:
            stripe_line_item = {
                'price_data': {
                    'currency': invoice.iso_currency_code,
                    'product_data': {
                        'name': invoice_line_item.name,
                        'description': invoice_line_item.description
                    },
                    'unit_amount': invoice_line_item.amount * 100  # Must be in cents
                },
                'quantity': 1,
            }
            stripe_line_items.append(stripe_line_item)
        
        session = stripe.checkout.Session.create(
            line_items=stripe_line_items,
            mode='payment',
            client_reference_id=invoice.client_reference_id,
            customer_email=invoice.customer_email,
            metadata={
                "invoice_id": invoice.id,
                "user_id": user_id
            },
            success_url=f'{g.organisation.system_url}/payment-success',
            cancel_url=f'{g.organisation.system_url}/payment-cancel',
        )

        invoice.add_payment_intent(session.payment_intent)
        invoice_repository.save()

        return marshal(session, payment_fields), 200

class PaymentsWebhookAPI(PaymentsWebhookMixin, restful.Resource):
    def post(self):
        args = self.post_parser.parse_args()

        event = None
        payload = request.data
        sig_header = args['Stripe-Signature']

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                g.organisation.stripe_webhook_secret_key
            )
        except ValueError as e:
            raise e
        except stripe.error.SignatureVerificationError as e:
            raise e
        
        idempotency_key = event['request']['idempotency_key']
        if invoice_repository.has_processed_stripe_webhook_event(idempotency_key):
            return 200

        accepted_events = [
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'payment_intent.canceled'
        ]

        if event['type'] in accepted_events:
            created_at_unix = event['created']
            LOGGER.info(f"Handling {event['type']} event")

            invoice_payment_status = None
            if event['type'] == 'payment_intent.succeeded':
                invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(
                    PaymentStatus.PAID,
                    created_at_unix
                )
            
            if event['type'] == 'payment_intent.payment_failed' or event['type'] == 'payment_intent.payment_canceled':
                invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(
                    PaymentStatus.FAILED,
                    created_at_unix
                )
            
            payment_intent = event['data']['object']['id']
            invoice = invoice_repository.get_from_payment_intent(payment_intent)
            invoice.add_invoice_payment_status(invoice_payment_status)
            invoice_repository.save()

            stripe_webhook_event = StripeWebhookEvent(event)
            invoice_repository.add(stripe_webhook_event)

            if invoice.is_paid and invoice.offer_id:
                LOGGER.info(f"Invoice offer ID is {invoice.offer_id}")
                offer = offer_repository.get_by_id(invoice.offer_id)
                offer_api.confirm_offer_payment(offer)

            invoice_repository.save()
        else:
            LOGGER.warn(f"Received an unexpected event: {event['type']}")

        return 200
