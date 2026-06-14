from datetime import datetime

from app import db


class Session(db.Model):
    __tablename__ = 'programme_session'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    session_type_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=True)
    venue = db.Column(db.String(160), nullable=True)
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionTranslation(db.Model):
    __tablename__ = 'programme_session_translation'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(4000), nullable=True)
    __table_args__ = (db.UniqueConstraint('session_id', 'language', name='uq_session_lang'),)


class Speaker(db.Model):
    __tablename__ = 'programme_speaker'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.String(512), nullable=True)
    bio = db.Column(db.String(2000), nullable=True)
    linked_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)


class SessionSpeaker(db.Model):
    __tablename__ = 'programme_session_speaker'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    speaker_id = db.Column(db.Integer(), db.ForeignKey('programme_speaker.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('session_id', 'speaker_id', name='uq_session_speaker'),)


class SessionTag(db.Model):
    __tablename__ = 'programme_session_tag'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('session_id', 'tag_id', name='uq_session_tag'),)
