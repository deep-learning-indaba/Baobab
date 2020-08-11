from app import db, bcrypt
import app


class ApplicationForm(db.Model):
    __tablename__ = 'application_form'

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    nominations = db.Column(db.Boolean(), nullable=False)

    def __init__(self, event_id, is_open, nominations):
        self.event_id = event_id
        self.is_open = is_open
        self.nominations = nominations


class Section(db.Model):
    __tablename__ = 'section'

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id', use_alter=True), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)
    key = db.Column(db.String(255), nullable=True)

    section_translations = db.relationship('SectionTranslation', lazy='dynamic')

    def __init__(self, application_form_id, name, description, order):
        self.application_form_id = application_form_id
        self.name = name
        self.description = description
        self.order = order


class SectionTranslation(db.Model):
    __tablename__ = 'section_translation'
    __table_args__ = tuple([db.UniqueConstraint('section_id', 'language', name='uq_section_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
    language = db.Column(db.String(2))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    section = db.relationship('Section', foreign_keys=[section_id])

    def __init__(self, name, description, language):
        self.name = name
        self.description = description
        self.language = language


class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
    type = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    key = db.Column(db.String(255), nullable=True)

    question_translations = db.relationship('QuestionTranslation', lazy='dynamic')

    def __init__(self, application_form_id, section_id, headline, placeholder, order, questionType, validation_regex, validation_text=None, is_required = True, description = None, options = None):
        self.application_form_id = application_form_id
        self.section_id = section_id
        self.headline = headline
        self.placeholder = placeholder
        self.order = order
        self.type = questionType
        self.description = description
        self.options = options
        self.is_required = is_required
        self.validation_regex = validation_regex
        self.validation_text = validation_text


class QuestionTranslation(db.Model):
    __tablename__ = 'question_translation'
    __table_args__ = tuple([db.UniqueConstraint('question_id', 'language', name='uq_question_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=False)
    language = db.Column(db.String(2))
    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

    question = db.relationship('Question', foreign_keys=[question_id])