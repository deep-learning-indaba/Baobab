from app import db
from app.invoice.models import Invoice, InvoiceLineItem, InvoicePaymentStatus

class InvoiceRepository():
    @staticmethod
    def get_by_id(invoice_id):
        return db.session.query(Invoice).get(invoice_id)