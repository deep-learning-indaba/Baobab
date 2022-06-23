import json
import warnings
from time import time

from app import db
from app.invoice.models import PaymentStatus, InvoicePaymentStatus, Invoice
from app.registration.models import Offer
from app.utils.testing import ApiTestCase
from app.utils.errors import INVOICE_NOT_FOUND

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


class InvoiceApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice"

        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")
    
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
        self.assertEqual(data["client_reference_id"], str(self.applicant_id))
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
    
    def test_cancel_own_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 200)
    
    def test_prevent_canceling_someone_else_invoices(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        another_applicant_email = "another_applicant@user.com"
        self.add_user(another_applicant_email)
        
        header = self.get_auth_header_for(another_applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, INVOICE_NOT_FOUND[1])

    def test_prevent_cancel_of_already_canceled_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        invoice.cancel(self.applicant_id)
        db.session.commit()

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Invoice has already been canceled.")

    def test_prevent_cancel_of_already_paid_invoice(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_id = invoice.id
        invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.PAID, time())
        invoice.invoice_payment_statuses.append(invoice_payment_status)
        db.session.commit()

        header = self.get_auth_header_for(self.applicant_email)
        params = {'invoice_id': invoice_id}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Cannot cancel an invoice that's already been paid.")

class InvoiceListApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice-list"

        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")
    
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
        invoice_1.invoice_payment_statuses.append(invoice_payment_status_1)
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
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 299.98)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.PAID.value)

        self.assertEqual(data[1]["customer_email"], self.applicant_email)
        self.assertEqual(data[1]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[1]["iso_currency_code"], 'usd')
        self.assertEqual(data[1]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[1]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[1]["created_at"])
        self.assertEqual(data[1]["total_amount"], 89.98)
        self.assertEqual(data[1]["current_payment_status"], PaymentStatus.UNPAID.value)
    
class InvoiceAdminApiTest(BaseInvoiceApiTest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/invoice-admin"

        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")

    def setUp(self):
        super().setUp()
    
    def test_get_invoices_for_event(self):
        line_items = self.get_default_line_items()
        invoice = self.add_invoice(self.treasurer_id, self.applicant_id, line_items, self.applicant_email)
        invoice_payment_status = InvoicePaymentStatus.from_stripe_webhook(PaymentStatus.FAILED, time())
        invoice.invoice_payment_statuses.append(invoice_payment_status)
        offer_1 = self.add_offer(self.applicant_id, self.event_id)
        invoice.link_offer(offer_1.id)

        another_applicant_email = "another_applicant@user.com"
        another_applicant = self.add_user(another_applicant_email)
        another_applicant_id = another_applicant.id
        line_items = self.get_default_line_items()
        line_items[0].amount = 3.14
        line_items[1].amount = 2.71
        invoice_2 = self.add_invoice(self.treasurer_id, another_applicant.id, line_items, another_applicant_email)
        offer_2 = self.add_offer(another_applicant.id, self.event_id)
        invoice_2.link_offer(offer_2.id)
        db.session.commit()

        params = {'event_id': self.event_id}
        header = self.get_auth_header_for(self.treasurer_email)
        response = self.app.get(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]["customer_email"], self.applicant_email)
        self.assertEqual(data[0]["client_reference_id"], str(self.applicant_id))
        self.assertEqual(data[0]["iso_currency_code"], 'usd')
        self.assertEqual(data[0]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[0]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[0]["created_at"])
        self.assertEqual(data[0]["total_amount"], 299.98)
        self.assertEqual(data[0]["current_payment_status"], PaymentStatus.FAILED.value)

        self.assertEqual(data[1]["customer_email"], another_applicant_email)
        self.assertEqual(data[1]["client_reference_id"], str(another_applicant_id))
        self.assertEqual(data[1]["iso_currency_code"], 'usd')
        self.assertEqual(data[1]["created_by_user_id"], self.treasurer_id)
        self.assertEqual(data[1]["created_by_user"], self.treasurer_name)
        self.assertIsNotNone(data[1]["created_at"])
        self.assertEqual(data[1]["total_amount"], 5.85)
        self.assertEqual(data[1]["current_payment_status"], PaymentStatus.UNPAID.value)