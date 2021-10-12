from datetime import datetime
from enum import Enum

from app import db


class Status(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLIST = "waitlist"


class Outcome(db.Model):
    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("app_user.id"), nullable=False)
    status = db.Column(db.Enum(Status, name="outcome_status"), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    latest = db.Column(db.Boolean(), nullable=False)
    updated_by_user_id = db.Column(
        db.Integer(), db.ForeignKey("app_user.id"), nullable=False
    )

    event = db.relationship("Event", foreign_keys=[event_id])
    user = db.relationship("AppUser", foreign_keys=[user_id])
    updated_by_user = db.relationship("AppUser", foreign_keys=[updated_by_user_id])

    def __init__(self, event_id, user_id, status, updated_by_user_id):
        self.event_id = event_id
        self.user_id = user_id
        self.status = status
        self.timestamp = datetime.now()
        self.latest = True
        self.updated_by_user_id = updated_by_user_id

    def reset_latest(self):
        self.latest = False
