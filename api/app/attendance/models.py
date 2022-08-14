from datetime import datetime

from app import db

class Attendance(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    indemnity_signed = db.Column(db.Boolean(), nullable=False)
    confirmed = db.Column(db.Boolean(), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    updated_by_user = db.relationship('AppUser', foreign_keys=[updated_by_user_id])

    def __init__(self,
                 event_id,
                 user_id,
                 updated_by_user_id):
        self.event_id = event_id
        self.user_id = user_id
        self.timestamp = datetime.now()
        self.updated_by_user_id = updated_by_user_id
        self.indemnity_signed = False
        self.confirmed=False

    def sign_indemnity(self):
        self.indemnity_signed = True

    def confirm(self):
        self.confirmed = True


class EventIndemnity(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    indemnity_form = db.Column(db.String(), nullable=False)

    def __init__(self,
                 event_id,
                 indemnity_form):
        self.event_id = event_id
        self.indemnity_form = indemnity_form
