from app import db

class Offer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),  db.ForeignKey("user_id"), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey("event_id"), nullable=False)
    offer_date = db.Column(db.DateTime(), nullable=False)
    expiry_date = db.Column(db.DateTime(), nullable=False)
    payment_required = db.Column(db.String(50), nullable=False)
    travel_award = db.Column(db.String(50), nullable=False)
    accommodation_award = db.Column(db.String(50), nullable=False)
    accepted = db.Column(db.String(50), nullable=False)
    rejected = db.Column(db.String(50), nullable=False)
    rejected_reason = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

