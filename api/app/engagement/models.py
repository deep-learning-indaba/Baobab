from datetime import datetime

from app import db


class EngagementEvent(db.Model):
    __tablename__ = 'engagement_event'
    id = db.Column(db.Integer(), primary_key=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    event_type = db.Column(db.String(40), nullable=False)
    event_metadata = db.Column(db.JSON(), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (db.Index('ix_engagement_event_type_event', 'event_id', 'event_type'),)
