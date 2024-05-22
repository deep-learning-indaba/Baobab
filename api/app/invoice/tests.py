import json
from datetime import datetime, timedelta
from time import time
from unittest.mock import patch
import warnings
import os

from app import db
from app.invoice.models import PaymentStatus, InvoicePaymentStatus, StripeWebhookEvent
from app.invoice.repository import InvoiceRepository as invoice_repository
from app.utils.auth import sign_payload
from app.utils.testing import ApiTestCase
from app.utils.errors import (
    INVOICE_NOT_FOUND,
    FORBIDDEN,
    OFFER_NOT_FOUND,
    EVENT_FEE_NOT_FOUND,
    EVENT_FEES_MUST_HAVE_SAME_CURRENCY,
    INVOICE_PAID,
    INVOICE_CANCELED,
    INVOICE_MUST_HAVE_FUTURE_DATE,
    INVOICE_OVERDUE
)

class BaseInvoiceApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()

        event = self.add_event()
        self.event_id = event.id
        
        self.treasurer_email = "treasurer@user.com"
        treasurer = self.add_user(self.treasurer_email)
        self.treasurer_id = treasurer.id
        self.treasurer_name = treasurer.full_name
        self.add_event_role("treasurer", self.treasurer_id, event.id)

        self.applicant_email = "applicant@user.com"
        self.applicant = self.add_user(self.applicant_email)
        self.applicant_id = self.applicant.id
        self.applicant_name = self.applicant.full_name

        self.add_email_template("invoice")

        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")


class InvoiceApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice"
    
    def setUp(self):
        super().setUp()

    def test_get_invoice_success(self):
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        self.add_invoice_payment_intent(invoice_id)
        self.add_offer_invoice(invoice_id, offer.id)
        header = self.get_auth_header_for(self.applicant_email)

        params = {'invoice_id': invoice_id}
        response = self.app.get(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(data["customer_email"], self.applicant_email)
        self.assertEqual(data["customer_name"], self.applicant_name)
        self.assertEqual(data["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data["iso_currency_code"], 'usd')
        self.assertIsNotNone(data["due_date"])
        self.assertEqual(data["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data["created_at"])
        self.assertEqual(data["total_amount"], 299.98)
        self.assertEqual(data["offer_id"], offer_id)

        self.assertEqual(len(data["invoice_payment_statuses"]), 1)
        self.assertEqual(data["invoice_payment_statuses"][0]["payment_status"], PaymentStatus.UNPAID.value)
        self.assertIsNotNone(data["invoice_payment_statuses"][0]["created_at"])
        self.assertIsNotNone(data["invoice_payment_statuses"][0]["created_at_unix"])
        self.assertEqual(data["invoice_payment_statuses"][0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data["invoice_payment_statuses"][0]["created_by"], self.treasurer_name)

        self.assertEqual(len(data["invoice_line_items"]), 2)
        self.assertEqual(data["invoice_line_items"][0]["name"], 'registration')
        self.assertEqual(data["invoice_line_items"][0]["description"], 'registration desc')
        self.assertEqual(data["invoice_line_items"][0]["amount"], 99.99)
        self.assertEqual(data["invoice_line_items"][1]["name"], 'accommodation')
        self.assertEqual(data["invoice_line_items"][1]["description"], 'accommodation desc')
        self.assertEqual(data["invoice_line_items"][1]["amount"], 199.99)

        self.assertEqual(len(data["invoice_payment_intents"]), 1)
        self.assertEqual(data["invoice_payment_intents"][0]["payment_intent"], 'pi_3L7GhOEpDzoopUbL0jGJhE2i')
        self.assertIsNotNone(data["invoice_payment_intents"][0]["created_at"])
        self.assertEqual(data["invoice_payment_intents"][0]["has_session_expired"], False)

    def test_prevent_get_of_someone_elses_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        another_applicant_email = "another_applicant@user.com"
        self.add_user(another_applicant_email)
        
        header = self.get_auth_header_for(another_applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.get(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])

class InvoicePaymentStatusApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = '/api/v1/invoice-payment-status'
    
    def setUp(self):
        super().setUp()

    def test_invoice_not_found(self):
        params = {'invoice_id': 12}
        header = self.get_auth_header_for(self.applicant_email)
        response = self.app.get(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])
    
    def test_get_latest_payment_status(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, int(time()) + 1)
        invoice.add_invoice_payment_status(payment_status)
        invoice_repository.save()

        params = {'invoice_id': invoice_id}
        header = self.get_auth_header_for(self.applicant_email)
        response = self.app.get(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['payment_status'], PaymentStatus.PAID.value)
        self.assertIsNotNone(data['created_at_unix'])

class InvoiceListApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice-list"
    
    def setUp(self):
        super().setUp()
    
    def test_get_with_no_invoices_for_user(self):
        another_applicant_email = "another_applicant@user.com"
        another_applicant = self.add_user(another_applicant_email)
        line_items = self.get_default_line_items()
        self.add_invoice(self.treasurer_id, another_applicant.id, line_items, another_applicant_email)

        header = self.get_auth_header_for(self.applicant_email)
        response = self.app.get(self.url, headers=header)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [])

    def test_get_with_multiple_invoices(self):
        line_items_1 = self.get_default_line_items()
        invoice_1 = self.add_invoice(self.treasurer_id, self.applicant_id, line_items_1, self.applicant_email)
        invoice_payment_status_1 = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, time())
        invoice_1.add_invoice_payment_status(invoice_payment_status_1)
        line_items_2 = self.get_default_line_items()
        line_items_2[0].amount = 49.99
        line_items_2[1].amount = 39.99
        self.add_invoice(self.treasurer_id, self.applicant_id, line_items_2, self.applicant_email)
        db.session.commit()

        header = self.get_auth_header_for(self.applicant_email)
        response = self.app.get(self.url, headers=header)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["customer_email"], self.applicant_email)
        self.assertEqual(data[0]["customer_name"], self.applicant_name)
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[0]["due_date"])
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 299.98)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.PAID.value)

        self.assertEqual(data[1]["customer_email"], self.applicant_email)
        self.assertEqual(data[1]["customer_name"], self.applicant_name)
        self.assertEqual(data[1]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[1]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[1]["due_date"])
        self.assertEqual(data[1]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[1]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[1]["created_at"])
        self.assertEqual(data[1]["total_amount"], 89.98)
        self.assertEqual(data[1]["current_payment_status"], PaymentStatus.UNPAID.value)
    
class InvoiceAdminApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice-admin"

    def setUp(self):
        super().setUp()
    
    def test_get_invoices_for_event(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.FAILED, time())
        invoice.add_invoice_payment_status(invoice_payment_status)
        offer_1 = self.add_offer(self.applicant_id, self.event_id)
        invoice.link_offer(offer_1.id)

        another_applicant_email = "another_applicant@user.com"
        another_applicant = self.add_user(another_applicant_email)
        another_applicant_id = another_applicant.id
        another_applicant_name = another_applicant.full_name
        line_items = self.get_default_line_items()
        line_items[0].amount = 3.14
        line_items[1].amount = 2.71
        invoice_2 = self.add_invoice(self.treasurer_id, another_applicant.id, line_items, another_applicant_email)
        offer_2 = self.add_offer(another_applicant.id, self.event_id)
        invoice_2.link_offer(offer_2.id)
        db.session.commit()

        params = {'event_id': self.event_id}
        header = self.get_auth_header_for(self.treasurer_email)
        response = self.app.get("/api/v1/invoice-admin", headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["customer_email"], self.applicant_email)
        self.assertEqual(data[0]["customer_name"], self.applicant_name)
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[0]["due_date"])
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 299.98)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.FAILED.value)

        self.assertEqual(data[1]["customer_email"], another_applicant_email)
        self.assertEqual(data[1]["customer_name"], another_applicant_name)
        self.assertEqual(data[1]["client_reference_id"], str(another_applicant_id))
        self.assertEqual(data[1]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[1]["due_date"])
        self.assertEqual(data[1]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[1]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[1]["created_at"])
        self.assertEqual(data[1]["total_amount"], 5.85)
        self.assertEqual(data[1]["current_payment_status"], PaymentStatus.UNPAID.value)
    
    def test_prevent_invoice_creation_from_non_treasurer(self):
        header = self.get_auth_header_for(self.applicant_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [1],
            'event_fee_ids': [1],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])
    
    def test_prevent_invoice_creation_with_due_date_in_past(self):
        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [1],
            'event_fee_ids': [1],
            'due_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_MUST_HAVE_FUTURE_DATE[1])

    def test_prevent_invoice_creation_with_non_existent_offer(self):
        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [1],
            'event_fee_ids': [1],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, OFFER_NOT_FOUND[1])

    def test_prevent_invoice_creation_with_deactivated_event_fees(self):
        event_fee = self.add_event_fee(self.event_id, self.treasurer_id, iso_currency_code='usd')
        event_fee_id = event_fee.id
        event_fee.deactivate(self.treasurer_id)
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id

        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id],
            'event_fee_ids': [event_fee_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, EVENT_FEE_NOT_FOUND[1])

    def test_prevent_invoice_creation_with_event_fees_with_different_currencies(self):
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        event_fee_1 = self.add_event_fee(self.event_id, self.treasurer_id, iso_currency_code='usd')
        event_fee_1_id = event_fee_1.id
        event_fee_2 = self.add_event_fee(self.event_id, self.treasurer_id, iso_currency_code='gbp')
        event_fee_2_id = event_fee_2.id

        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id],
            'event_fee_ids': [event_fee_1_id, event_fee_2_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, EVENT_FEES_MUST_HAVE_SAME_CURRENCY[1])   

    def test_prevent_invoice_creation_when_valid_invoice_already_exists(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        invoice.link_offer(offer.id)
        event_fee_1 = self.add_event_fee(self.event_id, self.treasurer_id)
        event_fee_1_id = event_fee_1.id
        event_fee_2 = self.add_event_fee(self.event_id, self.treasurer_id)
        event_fee_2_id = event_fee_2.id

        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id],
            'event_fee_ids': [event_fee_1_id, event_fee_2_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 400)

    def test_prevent_invoice_creation_with_negative_total(self):
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        event_fee_1 = self.add_event_fee(self.event_id, self.treasurer_id, name='Registration', amount=199.99)
        event_fee_1_id = event_fee_1.id
        event_fee_2 = self.add_event_fee(self.event_id, self.treasurer_id, name='Registration credit', amount=-199.99)
        event_fee_2_id = event_fee_2.id
        event_fee_3 = self.add_event_fee(self.event_id, self.treasurer_id, name='Misc credit', amount=-0.01)
        event_fee_3_id = event_fee_3.id

        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id],
            'event_fee_ids': [event_fee_1_id, event_fee_2_id, event_fee_3_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 400)        

    def test_invoice_creation(self):
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        another_applicant_email = "another_applicant@user.com"
        another_applicant = self.add_user(another_applicant_email)
        another_applicant_id = another_applicant.id
        another_applicant_name = another_applicant.full_name
        another_offer = self.add_offer(another_applicant.id, self.event_id)
        another_offer_id = another_offer.id
        event_fee_1 = self.add_event_fee(self.event_id, self.treasurer_id, amount=1.41)
        event_fee_1_id = event_fee_1.id
        event_fee_2 = self.add_event_fee(self.event_id, self.treasurer_id, amount=1.61)
        event_fee_2_id = event_fee_2.id
    
        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id, another_offer_id],
            'event_fee_ids': [event_fee_1_id, event_fee_2_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["customer_email"], self.applicant_email)
        self.assertEqual(data[0]["customer_name"], self.applicant_name)
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[0]["due_date"])
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 3.02)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.UNPAID.value)

        self.assertEqual(data[1]["customer_email"], another_applicant_email)
        self.assertEqual(data[1]["customer_name"], another_applicant_name)
        self.assertEqual(data[1]["client_reference_id"], str(another_applicant_id))
        self.assertEqual(data[1]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[1]["due_date"])
        self.assertEqual(data[1]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[1]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[1]["created_at"])
        self.assertEqual(data[1]["total_amount"], 3.02)
        self.assertEqual(data[1]["current_payment_status"], PaymentStatus.UNPAID.value)

    def test_invoice_creation_with_zero_total(self):
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        event_fee_1 = self.add_event_fee(self.event_id, self.treasurer_id, name='Registration', amount=99.99)
        event_fee_1_id = event_fee_1.id
        event_fee_2 = self.add_event_fee(self.event_id, self.treasurer_id, name='Registration credit', amount=-99.99)
        event_fee_2_id = event_fee_2.id
    
        header = self.get_auth_header_for(self.treasurer_email)
        params = {
            'event_id': self.event_id,
            'offer_ids': [offer_id],
            'event_fee_ids': [event_fee_1_id, event_fee_2_id],
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        response = self.app.post(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data), 1)

        self.assertEqual(data[0]["customer_email"], self.applicant_email)
        self.assertEqual(data[0]["customer_name"], self.applicant_name)
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertIsNotNone(data[0]["due_date"])
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 0.0)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.PAID.value)
    
    def test_cancel_invoice_from_event(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        self.add_offer_invoice(invoice_id, offer_id)

        header = self.get_auth_header_for(self.treasurer_email)
        params = {'invoice_id': invoice_id, 'event_id': self.event_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 200)

    def test_prevent_cancel_when_not_treasurer(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id, 'event_id': self.event_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])
    
    def test_prevent_canceling_invoice_from_another_event(self):
        another_event = self.add_event(key='ANOTHERINDABA')
        another_event_id = another_event.id
        self.add_event_role('treasurer', self.treasurer_id, another_event_id)
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        offer = self.add_offer(self.applicant_id, another_event_id)
        offer_id = offer.id
        self.add_offer_invoice(invoice_id, offer_id)
        
        header = self.get_auth_header_for(self.treasurer_email)
        params = {'invoice_id': invoice_id, 'event_id': self.event_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])

    def test_prevent_cancel_of_already_canceled_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        invoice.cancel(self.applicant_id)
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        self.add_offer_invoice(invoice_id, offer_id)
        db.session.commit()

        header = self.get_auth_header_for(self.treasurer_email)
        params = {'invoice_id': invoice_id, 'event_id': self.event_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Invoice has already been canceled.")

    def test_prevent_cancel_of_already_paid_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, time())
        invoice.add_invoice_payment_status(invoice_payment_status)
        offer = self.add_offer(self.applicant_id, self.event_id)
        offer_id = offer.id
        self.add_offer_invoice(invoice_id, offer_id)
        db.session.commit()

        header = self.get_auth_header_for(self.treasurer_email)
        params = {'invoice_id': invoice_id, 'event_id': self.event_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Cannot cancel an invoice that's already been paid.")

class PaymentsApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/payment"

    def setUp(self):
        super().setUp()
    
    def test_prevent_pay_invoice_again(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        payment_status = InvoicePaymentStatus.from_baobab(PaymentStatus.PAID, self.treasurer_id)
        invoice.add_invoice_payment_status(payment_status)
        db.session.commit()

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_PAID[1])
    
    def test_prevent_pay_overdue_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email, due_date=datetime.now()-timedelta(days=7))
        invoice_id = invoice.id

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_OVERDUE[1])

    def test_prevent_pay_canceled_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        payment_status = InvoicePaymentStatus.from_baobab(PaymentStatus.CANCELED, self.treasurer_id)
        invoice.add_invoice_payment_status(payment_status)
        db.session.commit()

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_CANCELED[1])

    @patch('app.invoice.api.stripe')
    def test_make_payment(self, mock_stripe):
        class TestSession:
            def __init__(self, amount_total):
                self.payment_intent = 'pi_3L7GhOEpDzoopUbL0jGJhE2i'
                self.url = 'https://checkout.stripe.com/pay/cs_test_a1gR3cbI'
                self.amount_total = amount_total

        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        total_amount = invoice.total_amount
        mock_stripe.checkout.Session.create.side_effect = [TestSession(total_amount)]

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.post(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['payment_intent'], 'pi_3L7GhOEpDzoopUbL0jGJhE2i')
        self.assertEqual(data['url'], 'https://checkout.stripe.com/pay/cs_test_a1gR3cbI')
        self.assertEqual(data['amount_total'], float(total_amount))

class PaymentsWebhookApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/stripe-webhook"

    def setUp(self):
        super().setUp()
        self.stripe_user_agent = 'Stripe/1.0 (+https://stripe.com/docs/webhooks)'
        path = f"{os.path.dirname(__file__)}/test_event_payload.json"
        f = open(path, 'r')
        self.data = json.loads(f.read())
        f.close()
    
    def test_signature_verification_fails(self):
        unix_timestamp = int(time())
        payload = f"{unix_timestamp}.{json.dumps(self.data)}"
        payload_signature = sign_payload(payload, 'wrong_secret')
        stripe_signature = f"t={unix_timestamp},v1={payload_signature},v0=doesntmatter"

        headers = {
            'User-Agent': self.stripe_user_agent,
            'Stripe-Signature': stripe_signature,
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = self.app.post(self.url, headers=headers, data=json.dumps(self.data))

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['message'], 'Could not resolve organisation from stripe signature')
        
    
    def test_payment_webhook_success_payment(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items)
        invoice_id = invoice.id
        invoice.add_payment_intent('pi_3L7GhOEpDzoopUbL0jGJhE2i')
        db.session.commit()

        unix_timestamp = int(time()) + 1
        self.data['created'] = unix_timestamp
        payload = f"{unix_timestamp}.{json.dumps(self.data)}"
        payload_signature = sign_payload(payload, self.dummy_org_webhook_secret)
        stripe_signature = f"t={unix_timestamp},v1={payload_signature},v0=doesntmatter"

        headers = {
            'User-Agent': self.stripe_user_agent,
            'Stripe-Signature': stripe_signature,
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = self.app.post(self.url, headers=headers, data=json.dumps(self.data))
        
        invoice = invoice_repository.get_by_id(invoice_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(invoice.current_payment_status.payment_status, PaymentStatus.PAID.value)


    def test_payment_webhook_fail_payment(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items)
        invoice_id = invoice.id
        invoice.add_payment_intent('pi_3L7GhOEpDzoopUbL0jGJhE2i')
        db.session.commit()

        unix_timestamp = int(time()) + 1
        self.data['created'] = unix_timestamp
        self.data['type'] = 'payment_intent.payment_failed'
        payload = f"{unix_timestamp}.{json.dumps(self.data)}"
        payload_signature = sign_payload(payload, self.dummy_org_webhook_secret)
        stripe_signature = f"t={unix_timestamp},v1={payload_signature},v0=doesntmatter"

        headers = {
            'User-Agent': self.stripe_user_agent,
            'Stripe-Signature': stripe_signature,
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = self.app.post(self.url, headers=headers, data=json.dumps(self.data))
        
        invoice = invoice_repository.get_by_id(invoice_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(invoice.current_payment_status.payment_status, PaymentStatus.FAILED.value)
    
    def test_payment_receive_events_out_of_order(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items)
        invoice_id = invoice.id
        invoice.add_payment_intent('pi_3L7GhOEpDzoopUbL0jGJhE2i')
        unix_timestamp = int(time()) + 10
        payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, unix_timestamp)
        invoice.add_invoice_payment_status(payment_status)
        db.session.commit()

        unix_timestamp = int(time()) + 5
        self.data['created'] = unix_timestamp
        self.data['type'] = 'payment_intent.payment_failed'
        payload = f"{unix_timestamp}.{json.dumps(self.data)}"
        payload_signature = sign_payload(payload, self.dummy_org_webhook_secret)
        stripe_signature = f"t={unix_timestamp},v1={payload_signature},v0=doesntmatter"

        headers = {
            'User-Agent': self.stripe_user_agent,
            'Stripe-Signature': stripe_signature,
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = self.app.post(self.url, headers=headers, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 200)

        invoice = invoice_repository.get_by_id(invoice_id)
        self.assertEqual(len(invoice.invoice_payment_statuses), 3)
        self.assertEqual(invoice.current_payment_status.payment_status, PaymentStatus.PAID.value)
    
    def test_payment_receive_duplicated_event(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items)
        invoice_id = invoice.id
        invoice.add_payment_intent('pi_3L7GhOEpDzoopUbL0jGJhE2i')
        stripe_webhook_event = StripeWebhookEvent(self.data)
        invoice_repository.add(stripe_webhook_event)
        db.session.commit()

        unix_timestamp = int(time()) + 1
        self.data['created'] = unix_timestamp
        payload = f"{unix_timestamp}.{json.dumps(self.data)}"
        payload_signature = sign_payload(payload, self.dummy_org_webhook_secret)
        stripe_signature = f"t={unix_timestamp},v1={payload_signature},v0=doesntmatter"

        headers = {
            'User-Agent': self.stripe_user_agent,
            'Stripe-Signature': stripe_signature,
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = self.app.post(self.url, headers=headers, data=json.dumps(self.data))
        self.assertEqual(response.status_code, 200)

        invoice = invoice_repository.get_by_id(invoice_id)
        self.assertEqual(len(invoice.invoice_payment_statuses), 1)
        self.assertEqual(invoice.current_payment_status.payment_status, PaymentStatus.UNPAID.value)