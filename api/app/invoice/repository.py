from api.app.registration.models import Offer
from app import db
from app.invoice.models import Invoice, OfferInvoice

class InvoiceRepository():
    @staticmethod
    def get_by_id(invoice_id):
        return db.session.query(Invoice).get(invoice_id)

    def get_all_for_customer(customer_email):
        return (
            db.session.query(Invoice)
            .filter_by(customer_email=customer_email)
            .all()
        )
    
    def get_one_for_customer(invoice_id, customer_email):
        return (
            db.session.query(Invoice)
            .filter_by(invoice_id=invoice_id, customer_email=customer_email)
            .first()
        )
    
    def get_for_event(event_id):
        return (
            db.session.query(Invoice)
            .join(OfferInvoice, OfferInvoice.invoice_id == Invoice.id)
            .join(Offer, Offer.id == OfferInvoice.offer_id)
            .filter_by(event_id=event_id)
            .all()
        )
    
    def save(invoice):
        db.session.merge(invoice)