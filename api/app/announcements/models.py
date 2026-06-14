from datetime import datetime

from app import db


class Announcement(db.Model):
    __tablename__ = 'announcement'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime(), nullable=True)
    send_at = db.Column(db.DateTime(), nullable=True)
    expiry_at = db.Column(db.DateTime(), nullable=True)


class AnnouncementTranslation(db.Model):
    __tablename__ = 'announcement_translation'
    id = db.Column(db.Integer(), primary_key=True)
    announcement_id = db.Column(db.Integer(), db.ForeignKey('announcement.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body_markdown = db.Column(db.Text(), nullable=False)
    __table_args__ = (db.UniqueConstraint('announcement_id', 'language', name='uq_announcement_lang'),)


class AnnouncementReceipt(db.Model):
    __tablename__ = 'announcement_receipt'
    id = db.Column(db.Integer(), primary_key=True)
    announcement_id = db.Column(db.Integer(), db.ForeignKey('announcement.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    delivered_at = db.Column(db.DateTime(), nullable=True)
    opened_at = db.Column(db.DateTime(), nullable=True)
    channel = db.Column(db.String(16), nullable=True)
    __table_args__ = (db.UniqueConstraint('announcement_id', 'user_id', name='uq_receipt_announcement_user'),)


class PushSubscription(db.Model):
    __tablename__ = 'push_subscription'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    endpoint = db.Column(db.String(1024), nullable=False, unique=True)
    p256dh = db.Column(db.String(256), nullable=False)
    auth = db.Column(db.String(256), nullable=False)
    user_agent = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
