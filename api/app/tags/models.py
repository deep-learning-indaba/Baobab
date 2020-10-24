from datetime import datetime
from app import db
from app.events.models import Event

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)

    translations = db.relationship('TagTranslation', lazy='dynamic')

    def __init__(self, event_id):
        self.event_id = event_id
    
    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation


class TagTranslation(db.Model):
    __tablename__ = 'tag_translation'
    __table_args__ = tuple([db.UniqueConstraint('tag_id', 'language', name='uq_tag_id_language')])
    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(), nullable=False)

    def __init__(self, tag_id, language, name):
        self.tag_id = tag_id
        self.language = language
        self.name = name
