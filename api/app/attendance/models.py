from datetime import datetime
import uuid

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


class EventQRToken(db.Model):
    __tablename__ = 'event_qr_token'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='uq_qrtoken_event_user'),)

    def __init__(self, event_id, user_id):
        self.event_id = event_id
        self.user_id = user_id
        self.token = uuid.uuid4().hex


class Checkin(db.Model):
    __tablename__ = 'checkin'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    checked_in_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    checked_in_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    method = db.Column(db.String(16), nullable=False, default='scan')
    day = db.Column(db.Date(), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', 'day', name='uq_checkin_event_user_day'),
    )
