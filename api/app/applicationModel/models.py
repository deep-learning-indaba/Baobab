from app import db, bcrypt
import app


class ApplicationForm(db.Model):
    __tablename__ = 'application_form'

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    nominations = db.Column(db.Boolean(), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    sections = db.relationship('Section', order_by='Section.order')

    def __init__(self, event_id, is_open, nominations):
        self.event_id = event_id
        self.is_open = is_open
        self.nominations = nominations

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

    section = db.relationship('Section', foreign_keys=[section_id])
    question_translations = db.relationship('QuestionTranslation', lazy='dynamic')

    def __init__(self, application_form_id, section_id, order, questionType, is_required=True):
        self.application_form_id = application_form_id
        self.section_id = section_id
        self.order = order
        self.type = questionType
        self.is_required = is_required
    
    def get_translation(self, language):
        question_translation = self.question_translations.filter_by(language=language).first()
        return question_translation


class Section(db.Model):
    __tablename__ = 'section'

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id', use_alter=True), nullable=True)
    key = db.Column(db.String(255), nullable=True)

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    section_translations = db.relationship('SectionTranslation', lazy='dynamic')
    questions = db.relationship('Question', primaryjoin=id==Question.section_id, order_by='Question.order')

    def __init__(self, application_form_id, order, depends_on_question_id=None, key=None):
        self.application_form_id = application_form_id
        self.order = order
        self.depends_on_question_id = depends_on_question_id
        self.key = key

    def get_translation(self, language):
        section_translation = self.section_translations.filter_by(language=language).first()
        return section_translation


class SectionTranslation(db.Model):
    __tablename__ = 'section_translation'
    __table_args__ = tuple([db.UniqueConstraint('section_id', 'language', name='uq_section_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=False)
    show_for_values = db.Column(db.JSON(), nullable=True)

    section = db.relationship('Section', foreign_keys=[section_id])

    def __init__(self, section_id, language, name, description, show_for_values=None):
        self.section_id = section_id
        self.language = language
        self.name = name
        self.description = description
        self.show_for_values = show_for_values


class QuestionTranslation(db.Model):
    __tablename__ = 'question_translation'
    __table_args__ = tuple([db.UniqueConstraint('question_id', 'language', name='uq_question_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

    question = db.relationship('Question', foreign_keys=[question_id])

    def __init__(
        self,
        question_id,
        language,
        headline,
        description=None,
        placeholder=None,
        validation_regex=None,
        validation_text=None,
        options=None,
        show_for_values=None
    ):
        self.question_id = question_id
        self.language = language
        self.headline = headline
        self.description = description
        self.placeholder = placeholder
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.options = options
        self.show_for_values = show_for_values