from app import db
from enum import Enum
from app import LOGGER

class TagType(Enum):
    RESPONSE = 'response'
    REGISTRATION = 'registration'
    GRANT = 'grant'
    QUESTION = 'question'

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    tag_type = db.Column(db.Enum(TagType, name="tag_type"), nullable=True)
    active = db.Column(db.Boolean(), nullable=False, default=True)

    translations = db.relationship('TagTranslation', lazy='dynamic')

    def __init__(
            self, 
            event_id,
            tag_type, 
            active=True
        ):
        self.event_id = event_id
        self.tag_type = tag_type
        self.active = active
    
    def update(self, tag_type, active):
        self.tag_type = tag_type
        self.active = active
    
    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation

    def stringify_tag_name_description(self, language='en'):
        translation = self.get_translation(language)
        if translation is None:
            LOGGER.warn('Could not find {} translation for tag id {}'.format(language, self.id))
            translation = self.get_translation('en')
        return '{}: {}'.format(translation.name, translation.description)

    def stringify_tag_name(self, language='en'):
        translation = self.get_translation(language)
        if translation is None:
            LOGGER.warn('Could not find {} translation for tag id {}'.format(language, self.id))
            translation = self.get_translation('en')
        return '{}'.format(translation.name)

class TagTranslation(db.Model):
    __tablename__ = 'tag_translation'
    __table_args__ = tuple([db.UniqueConstraint('tag_id', 'language', name='uq_tag_id_language')])
    id = db.Column(db.Integer(), primary_key=True)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)

    def __init__(self, tag_id, language, name, description=None):
        self.tag_id = tag_id
        self.language = language
        self.name = name
        self.description = description
    
    def update(self, language, name, description=None):
        self.language = language
        self.name = name
        self.description = description
