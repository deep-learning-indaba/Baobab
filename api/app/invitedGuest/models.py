
from app import db


class InvitedGuest(db.Model):
    __tablename__ = "invited_guest"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        "app_user.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)
