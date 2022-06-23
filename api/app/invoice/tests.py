import json
import warnings
from time import time

from app import db
from app.invoice.models import PaymentStatus, InvoicePaymentStatus, Invoice
from app.utils.testing import ApiTestCase
from app.utils.errors import INVOICE_NOT_FOUND


class InvoiceApiTest(ApiTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice"

        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")
    
    def setUp(self):
        super().setUp()
        event = self.add_event()
        self.event_id = event.id
        self.treasurer_email = "treasurer@user.com"
        treasurer = self.add_user(self.treasurer_email)
        self.treasurer_id = treasurer.id
        self.treasurer_name = treasurer.full_name
        self.add_event_role("treasurer", self.treasurer_id, event.id)

    
    def test_get_invoice_success(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user(applicant_email)
        offer = self.add_offer(applicant.id, self.event_id)
        offer_id = offer.id
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id
        self.add_invoice_payment_intent(invoice_id)
        self.add_offer_invoice(invoice_id, offer.id)
        header = self.get_auth_header_for(applicant_email)

        params = {'invoice_id': invoice_id}
        response = self.app.get(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(data["customer_email"], applicant_email)
        self.assertEqual(data["client_reference_id"], str(applicant.id))
        self.assertEqual(data["iso_currency_code"], 'usd')
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

    def test_prevent_retrieval_of_someone_elses_invoice(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user("applicant@user.com")
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id
        another_applicant_email = "another_applicant@user.com"
        self.add_user(another_applicant_email)
        
        header = self.get_auth_header_for(another_applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.get(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])
    
    def test_cancel_own_invoice(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user(applicant_email)
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id

        header = self.get_auth_header_for(applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 200)
    
    def test_prevent_canceling_someone_else_invoices(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user("applicant@user.com")
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id
        another_applicant_email = "another_applicant@user.com"
        self.add_user(another_applicant_email)
        
        header = self.get_auth_header_for(another_applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])

    def test_prevent_cancel_of_already_canceled_invoice(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user(applicant_email)
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id
        invoice.cancel(applicant.id)
        db.session.commit()

        header = self.get_auth_header_for(applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Invoice has already been canceled.")

    def test_prevent_cancel_of_already_paid_invoice(self):
        applicant_email = "applicant@user.com"
        applicant = self.add_user(applicant_email)
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, applicant.id, line_items, applicant_email)
        invoice_id = invoice.id
        invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, time())
        invoice.invoice_payment_statuses.append(invoice_payment_status)
        db.session.commit()

        header = self.get_auth_header_for(applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Cannot cancel an invoice that's already been paid.")