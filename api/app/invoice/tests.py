import json
import warnings

from app.utils.testing import ApiTestCase
from app import db, LOGGER
from app.invoice.models import Invoice, PaymentStatus


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
        invoice = self.add_invoice(self.treasurer_id, applicant.id, applicant_email)
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

    def test_get_invoice_not_found(self):
        pass