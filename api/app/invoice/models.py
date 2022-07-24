from datetime import datetime
from enum import Enum
import time

from app import db
from app.utils.exceptions import BaobabError

class PaymentStatus(Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"

    def __repr__(self):
        return f"{self.value}"

class InvoicePaymentStatus(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    invoice_id = db.Column(db.Integer(), db.ForeignKey('invoice.id'), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    created_at_unix = db.Column(db.Float(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    invoice = db.relationship('Invoice', foreign_keys=[invoice_id])

    @classmethod
    def from_baobab(cls, payment_status, user_id):
        return cls(
            payment_status=payment_status.value,
            created_at=datetime.now(),
            created_at_unix=time.time(),
            created_by_user_id=user_id
        )

    @classmethod
    def from_stripe_webhook(cls, payment_status, created_at_unix):
        return cls(
            payment_status=payment_status.value,
            created_at=datetime.now(),
            created_at_unix=created_at_unix,
            created_by_user_id=None 
        )


class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    invoice_id = db.Column(db.Integer(), db.ForeignKey('invoice.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=True)
    amount = db.Column(db.Numeric(scale=2), nullable=False)

    invoice = db.relationship('Invoice', foreign_keys=[invoice_id])

    def __init__(self, name, description, amount):
        self.name = name
        self.description = description
        self.amount = amount

    @property
    def amount_float(self):
        return float(self.amount)

class InvoicePaymentIntent(db.Model):
    __table_args__ = tuple([db.UniqueConstraint('payment_intent', name='uq_invoice_payment_intent_payment_intent')])    

    id = db.Column(db.Integer(), primary_key=True)
    invoice_id = db.Column(db.Integer(), db.ForeignKey('invoice.id'), nullable=False)
    payment_intent = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)

    invoice = db.relationship('Invoice', foreign_keys=[invoice_id])

    def __init__(self, payment_intent):
        self.payment_intent = payment_intent
        self.created_at = datetime.now()

    @property
    def has_session_expired(self):
        hours_since_creation = (datetime.now() - self.created_at).total_seconds() / 3600
        return hours_since_creation > 24

class Invoice(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    customer_email = db.Column(db.String(255), nullable=False, index=True)
    customer_name = db.Column(db.String(200), nullable=False)
    client_reference_id = db.Column(db.String(255), nullable=True, index=True)
    iso_currency_code = db.Column(db.String(3), nullable=False)
    due_date = db.Column(db.DateTime(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)

    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    invoice_line_items = db.relationship('InvoiceLineItem')
    invoice_payment_statuses = db.relationship('InvoicePaymentStatus', order_by='desc(InvoicePaymentStatus.created_at_unix)')
    invoice_payment_intents = db.relationship('InvoicePaymentIntent')
    offer_invoices = db.relationship('OfferInvoice')

    def __init__(
        self,
        customer_email,
        customer_name,
        iso_currency_code,
        due_date,
        line_items,
        user_id,
        client_reference_id=None
    ):
        self.customer_email = customer_email
        self.customer_name = customer_name
        self.client_reference_id = client_reference_id
        self.iso_currency_code = iso_currency_code
        self.due_date = due_date
        self.created_by_user_id = user_id
        self.created_at = datetime.now()
        
        self.invoice_line_items = line_items
        self.invoice_payment_statuses = [InvoicePaymentStatus.from_baobab(PaymentStatus.UNPAID, user_id)]
        self.invoice_payment_intents = []
        self.offer_invoices = []
    
    @property
    def total_amount(self):
        return sum(ili.amount for ili in self.invoice_line_items)
    
    @property
    def current_payment_status(self):
        return self.invoice_payment_statuses[0]
    
    @property
    def is_paid(self):
        return self.current_payment_status.payment_status == PaymentStatus.PAID.value
    
    @property
    def is_canceled(self):
        return self.current_payment_status.payment_status == PaymentStatus.CANCELED.value

    @property
    def is_overdue(self):
        return self.due_date < datetime.now()
    
    @property
    def offer_id(self):
        return self.offer_invoices[0].offer_id if self.offer_invoices else None

    def cancel(self, user_id):
        if self.current_payment_status.payment_status == PaymentStatus.CANCELED.value:
            raise BaobabError("Invoice has already been canceled.")
        
        if self.current_payment_status.payment_status == PaymentStatus.PAID.value:
            raise BaobabError("Cannot cancel an invoice that's already been paid.")

        canceled_status = InvoicePaymentStatus.from_baobab(PaymentStatus.CANCELED, user_id)
        self.add_invoice_payment_status(canceled_status)
    
    def link_offer(self, offer_id):
        offer_invoice = OfferInvoice(offer_id=offer_id)
        self.offer_invoices.append(offer_invoice)
    
    def add_payment_intent(self, payment_intent):
        payment_intent = InvoicePaymentIntent(payment_intent)
        self.invoice_payment_intents.append(payment_intent)

    def add_invoice_payment_status(self, invoice_payment_status):
        self.invoice_payment_statuses.append(invoice_payment_status)

class OfferInvoice(db.Model):
    __table_args__ = tuple([db.UniqueConstraint('invoice_id', name='uq_offer_invoice_invoice_id')])

    id = db.Column(db.Integer(), primary_key=True)
    offer_id = db.Column(db.Integer(), db.ForeignKey('offer.id'), nullable=False)
    invoice_id = db.Column(db.Integer(), db.ForeignKey('invoice.id'), nullable=False)

    offer = db.relationship('Offer', foreign_keys=[offer_id])
    invoice = db.relationship('Invoice', foreign_keys=[invoice_id])
class StripeWebhookEvent(db.Model):
    __table_args__ = tuple([db.UniqueConstraint('idempotency_key', name='uq_stripe_webhook_events_idempotency_key')])

    id = db.Column(db.Integer(), primary_key=True)
    idempotency_key = db.Column(db.String(50), nullable=False)
    payment_intent = db.Column(db.String(50), nullable=False)
    event = db.Column(db.JSON(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, event):
        self.idempotency_key = event['request']['idempotency_key']
        self.payment_intent = event['data']['object']['id']
        self.event = event
        self.created_at = datetime.now()