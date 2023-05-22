from datetime import datetime

import flask_restful as restful
from flask_restful import fields, marshal_with, marshal
from flask import g, request
import stripe

from app import LOGGER
from app.events.repository import EventRepository as event_repository
from app.invoice.mixins import InvoiceMixin, InvoiceAdminMixin, PaymentsMixin, PaymentsWebhookMixin
from app.invoice.models import Invoice, InvoiceLineItem, InvoicePaymentIntent, InvoicePaymentStatus, PaymentStatus, StripeWebhookEvent, OfferInvoice
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.registration.repository import OfferRepository as offer_repository
from app.registration.repository import RegistrationRepository as registration_repository
from app.users.repository import UserRepository as user_repository
from app.invoice import generator
from app.utils import emailer
from app.registrationResponse import api as registration_response_api
from app.utils import storage

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
from config import BOABAB_HOST

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
    'customer_email': fields.String,
    'customer_name': fields.String,
    'client_reference_id': fields.String,
    'iso_currency_code': fields.String,
    'due_date': fields.DateTime(dt_format='iso8601'),
    'created_by_user_id': fields.Integer,
    'created_by_user': fields.String(attribute='created_by.full_name'),
    'created_at': fields.DateTime(dt_format='iso8601'),
    'total_amount': fields.Float,
    'offer_id': fields.Integer(default=None),
    'invoice_payment_statuses': fields.List(fields.Nested(invoice_payment_status_fields)),
    'invoice_line_items': fields.List(fields.Nested(invoice_line_item_fields)),
    'invoice_payment_intents': fields.List(fields.Nested(invoice_payment_intent_fields))
}

invoice_list_fields = {
    'id': fields.Integer,
    'customer_email': fields.String,
    'customer_name': fields.String,
    'client_reference_id': fields.String,
    'iso_currency_code': fields.String,
    'due_date': fields.DateTime(dt_format='iso8601'),
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
        return marshal(invoices,invoice_list_fields), 200

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
        iso_currency_code = list(iso_currency_codes)[0]

        total_amount = sum([event_fee.amount for event_fee in event_fees])
        if total_amount < 0:
            return INVOICE_NEGATIVE

        invoices = []
        invalid_offer_ids = []
        for offer in offers:
            if offer.has_valid_invoice():
                invalid_offer_ids.append(offer.id)
            
            line_items = []
            for event_fee in event_fees:
                line_item = InvoiceLineItem(event_fee.name, event_fee.description, event_fee.amount)
                line_items.append(line_item)

            invoice = Invoice(
                offer.user.email,
                offer.user.full_name,
                iso_currency_code,
                due_date,
                line_items,
                user_id,
                str(offer.user_id)
            )
            invoice.link_offer(offer.id)

            if invoice.total_amount == 0:
                paid_status = InvoicePaymentStatus.from_baobab(PaymentStatus.PAID, user_id)
                invoice.add_invoice_payment_status(paid_status)
            
            invoices.append(invoice)
        
        if invalid_offer_ids:
            error_message = f"Offers {','.join(str(id) for id in invalid_offer_ids)} already have an invoice."
            return {'message': error_message}, 400

        invoice_repository.add_all(invoices)

        # Generate PDFs and email them
        for invoice in invoices:
            invoice_pdf, invoice_number = generator.from_invoice_model(invoice, g.organisation)
            filename = f"invoice_{invoice_number}.pdf"
            emailer.email_user(
                'invoice',
                event=event,
                user=offer.user,
                file_name=filename,
                file_path=invoice_pdf,
                template_parameters=dict(
                    system_url=g.organisation.system_url,
                    invoice_id=invoice.id
                )
            )
            LOGGER.debug('successfully sent invoice...')

            # Save invoice to Cloud storage
            try:
                bucket = storage.get_storage_bucket("indaba-invoices")  # TODO: Replace bucket name with config from organisation
                blob = bucket.blob(filename)
                with open(invoice_pdf, 'rb') as file:
                    bytes_file = file.read()
                    blob.upload_from_string(bytes_file, content_type="application/pdf")
            except Exception as e:
                LOGGER.error("Could not upload invoice to cloud storage: " + str(e))

        return marshal(invoices, invoice_list_fields), 201

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
                registration = registration_repository.from_offer(invoice.offer_id)
                if registration:
                    LOGGER.info(f"Confirming Registration ID {registration.id}")
                    registration_response_api.confirm_registration(registration, offer)

            invoice_repository.save()
        else:
            LOGGER.warn(f"Received an unexpected event: {event['type']}")

        return 200