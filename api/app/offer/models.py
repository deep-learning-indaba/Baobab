from datetime import datetime, date, time

from app import db
from app.invoice.models import PaymentStatus

class Offer(db.Model):

    __tablename__ = "offer"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),  db.ForeignKey(
        "app_user.id"), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)
    offer_date = db.Column(db.DateTime(), nullable=False)
    expiry_date = db.Column(db.DateTime(), nullable=False)
    payment_required = db.Column(db.Boolean(), nullable=False)
    rejected_reason = db.Column(db.String(5000), nullable=True)
    candidate_response = db.Column(db.Boolean(), nullable=True)
    responded_at = db.Column(db.DateTime(), nullable=True)
    payment_amount = db.Column(db.String(), nullable=True)

    user = db.relationship('AppUser', foreign_keys=[user_id])
    offer_tags = db.relationship('OfferTag')
    offer_invoices = db.relationship('OfferInvoice')
    event = db.relationship('Event', foreign_keys=[event_id])

    def is_expired(self):
        end_of_today = datetime.combine(date.today(), time())
        return (self.candidate_response is None) and (self.expiry_date < end_of_today)
    
    def has_valid_invoice(self):
        valid_payment_statuses = [
            PaymentStatus.UNPAID.value,
            PaymentStatus.PAID.value,
            PaymentStatus.FAILED.value
        ]
        for offer_invoice in self.offer_invoices:
            if offer_invoice.invoice.current_payment_status.payment_status in valid_payment_statuses:
                return True
        return False

class OfferTag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    offer_id = db.Column(db.Integer(), db.ForeignKey('offer.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    accepted = db.Column(db.Boolean(), nullable=True)

    offer = db.relationship('Offer', foreign_keys=[offer_id])
    tag = db.relationship('Tag', foreign_keys=[tag_id])

    def __init__(self, offer_id, tag_id, accepted=None):
        self.offer_id = offer_id
        self.tag_id = tag_id
        self.accepted = accepted