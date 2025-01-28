from datetime import datetime
from app import db
from enum import Enum

class Status(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLIST = "waitlist"
    REVIEW = "in review"
    ACCEPT_W_REVISION = "accept with minor revision"
    REJECT_W_ENCOURAGEMENT = "reject with encouragement to resubmit"

class Outcome(db.Model):
    id = db.Column(db.Integer(), primary_key = True, nullable = False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable = False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable = False)
    status = db.Column(db.Enum(Status, name='outcome_status'), nullable = False)
    timestamp = db.Column(db.DateTime(), nullable = False)
    latest = db.Column(db.Boolean(), nullable = False)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    updated_by_user = db.relationship('AppUser', foreign_keys=[updated_by_user_id])

    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=True)
    response = db.relationship('Response', foreign_keys=[response_id])

    def __init__(self,
                 event_id,
                 user_id,
                 status,
                 updated_by_user_id,
                 response_id
                 ):
        self.event_id = event_id
        self.user_id = user_id
        self.status = status
        self.timestamp = datetime.now()
        self.latest = True
        self.updated_by_user_id = updated_by_user_id
        self.response_id = response_id

    def reset_latest(self):
        self.latest = False