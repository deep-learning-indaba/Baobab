from datetime import datetime
from enum import Enum

from app import db


class ConnectionStatus(Enum):
    SCANNED = 'scanned'
    PENDING = 'pending'
    CONNECTED = 'connected'
    REJECTED = 'rejected'
    BLOCKED = 'blocked'
    WITHDRAWN = 'withdrawn'


class Connection(db.Model):
    __tablename__ = 'connection'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    from_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    to_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    method = db.Column(db.String(16), nullable=False, default='scan')
    status = db.Column(db.Enum(ConnectionStatus, name='connection_status'), nullable=False, default=ConnectionStatus.PENDING)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    from_user = db.relationship('AppUser', foreign_keys=[from_user_id])
    to_user = db.relationship('AppUser', foreign_keys=[to_user_id])
    __table_args__ = (db.UniqueConstraint('event_id', 'from_user_id', 'to_user_id', name='uq_connection_edge'),)


class ConnectionReport(db.Model):
    __tablename__ = 'connection_report'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    reporter_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    reason = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
