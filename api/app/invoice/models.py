from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property

from app import db

class Invoice(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    customer_email = db.Column(db.String(255), nullable=False)
    client_reference_id = db.Column(db.String(255), nullable=True)
    iso_currency_code = db.Column(db.String(3), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)

    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    invoice_line_items = db.relationship('InvoiceLineItem')
    invoice_payment_statuses = db.relationship('InvoicePaymentStatus')

    def __init__(
        self,
        customer_email,
        iso_currency_code,
        line_items,
        user_id,
        client_reference_id=None
    ):
        self.customer_email = customer_email
        self.client_reference_id = client_reference_id
        self.iso_currency_code = iso_currency_code
        self.created_by_user_id = user_id
        self.created_at = datetime.now()
        
        self.invoice_line_items = line_items
        self.invoice_payment_statuses = [InvoicePaymentStatus("unpaid", user_id)]
    
    @hybrid_property
    def total_amount(self):
        return sum(ili.amount for ili in self.invoice_line_items)


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


class InvoicePaymentStatus(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    invoice_id = db.Column(db.Integer(), db.ForeignKey('invoice.id'), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    created_by_user_id = db.Column(db.DateTime(), db.ForeignKey('app_user.id'), nullable=False)
    
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    invoice = db.relationship('Invoice', foreign_keys=[invoice_id])

    def __init__(self, payment_status, user_id):
        self.payment_status = payment_status
        self.created_at = datetime.now()
        self.created_by_user_id = user_id        
