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

    translations = db.relationship('SessionTranslation', cascade='all, delete-orphan', lazy='selectin')
    session_speakers = db.relationship('SessionSpeaker', cascade='all, delete-orphan', lazy='selectin')
    session_tags = db.relationship('SessionTag', cascade='all, delete-orphan', lazy='selectin')


class SessionTranslation(db.Model):
    __tablename__ = 'programme_session_translation'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(4000), nullable=True)
    __table_args__ = (db.UniqueConstraint('session_id', 'language', name='uq_session_lang'),)

    def __init__(self, session_id, language, title, description=None):
        self.session_id = session_id
        self.language = language
        self.title = title
        self.description = description


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

    def __init__(self, event_id, name, email=None, photo_url=None, bio=None, linked_user_id=None):
        self.event_id = event_id
        self.name = name
        self.email = email
        self.photo_url = photo_url
        self.bio = bio
        self.linked_user_id = linked_user_id


class SessionSpeaker(db.Model):
    __tablename__ = 'programme_session_speaker'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    speaker_id = db.Column(db.Integer(), db.ForeignKey('programme_speaker.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('session_id', 'speaker_id', name='uq_session_speaker'),)

    def __init__(self, session_id, speaker_id):
        self.session_id = session_id
        self.speaker_id = speaker_id


class SessionTag(db.Model):
    __tablename__ = 'programme_session_tag'
    id = db.Column(db.Integer(), primary_key=True)
    session_id = db.Column(db.Integer(), db.ForeignKey('programme_session.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('session_id', 'tag_id', name='uq_session_tag'),)

    def __init__(self, session_id, tag_id):
        self.session_id = session_id
        self.tag_id = tag_id
