from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import column_property
import re
import enum
from typing import Tuple, Optional

from app import db, LOGGER


class ValidationError(str, enum.Enum):
    REQUIRED = 'required'
    INVALID_OPTION = 'invalid_option'
    VALIDATION_REGEX_FAILED = 'validation_regex_failed'


class Form(db.Model):
    """A generic form."""
    __tablename__ = 'form'
    
    id = db.Column(db.Integer(), primary_key=True)
    
    # Basic form properties
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    is_open = db.Column(db.Boolean(), nullable=False, default=True)
    multiple_responses = db.Column(db.Boolean(), nullable=False, default=False)
    linked_form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    
    # Versioning for form changes
    version = db.Column(db.Integer(), nullable=False, default=1)
    parent_form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=True)

    # Relationships
    sections = db.relationship('FormSection', order_by='FormSection.order', 
                              cascade='all, delete-orphan', foreign_keys='FormSection.form_id',
                              back_populates='form')
    questions = db.relationship('FormQuestion', cascade='all, delete-orphan',
                               foreign_keys='FormQuestion.form_id',
                               back_populates='form')
    responses = db.relationship('FormResponse', back_populates='form',
                               foreign_keys='FormResponse.form_id')
    
    # Link to parent/linked forms
    parent_form = db.relationship('Form', remote_side=[id], foreign_keys=[parent_form_id])
    linked_form = db.relationship('Form', remote_side=[id], foreign_keys=[linked_form_id])
    
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    
    def __init__(self, created_by_user_id, is_open=True, is_active=True, 
                 linked_form_id=None, parent_form_id=None, multiple_responses=False):
        self.created_by_user_id = created_by_user_id
        self.is_open = is_open
        self.is_active = is_active
        self.linked_form_id = linked_form_id
        self.parent_form_id = parent_form_id
        self.multiple_responses = multiple_responses
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.version = 1


class FormSection(db.Model):
    """Sections group related questions."""
    __tablename__ = 'form_section'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    key = db.Column(db.String(255), nullable=True)  # Optional identifier
    
    # Conditional visibility
    # use_alter to resolve cycle in dependencies.
    depends_on_question_id = db.Column(db.Integer(), 
                                      db.ForeignKey('form_question.id', use_alter=True), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='sections', foreign_keys=[form_id])
    translations = db.relationship('FormSectionTranslation', lazy='dynamic',
                                   cascade='all, delete-orphan',
                                   back_populates='section')
    questions = db.relationship('FormQuestion', order_by='FormQuestion.order',
                               cascade='all, delete-orphan', 
                               foreign_keys='FormQuestion.section_id',
                               back_populates='section')
    
    def __init__(self, form_id, order, key=None, depends_on_question_id=None):
        self.form_id = form_id
        self.order = order
        self.key = key
        self.depends_on_question_id = depends_on_question_id
    
    def get_translation(self, language: str) -> 'FormSectionTranslation':
        return self.translations.filter_by(language=language).first()


class FormSectionTranslation(db.Model):
    """i18n support for sections."""
    __tablename__ = 'form_section_translation'
    __table_args__ = (
        db.UniqueConstraint('form_section_id', 'language'),
    )
    
    id = db.Column(db.Integer(), primary_key=True)
    form_section_id = db.Column(db.Integer(), 
                               db.ForeignKey('form_section.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    
    # Conditional visibility values (JSON array)
    show_for_values = db.Column(db.JSON(), nullable=True)
    
    section = db.relationship('FormSection', back_populates='translations')
    
    def __init__(self, form_section_id, language, name, description=None, show_for_values=None):
        self.form_section_id = form_section_id
        self.language = language
        self.name = name
        self.description = description
        self.show_for_values = show_for_values


class FormQuestion(db.Model):
    """Generic question model supporting multiple types."""
    __tablename__ = 'form_question'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    section_id = db.Column(db.Integer(), 
                          db.ForeignKey('form_section.id'), nullable=False)
    
    # Question type (extensible via QuestionType registry)
    type = db.Column(db.String(50), nullable=False)
    # Types: short-text, long-text, dropdown, checkboxes, 
    #        date, file, multi-file, numeric, single-checkbox, etc.
    
    order = db.Column(db.Integer(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False, default=True)
    key = db.Column(db.String(255), nullable=True)  # Optional identifier
    
    # Conditional visibility
    depends_on_question_id = db.Column(db.Integer(), 
                                      db.ForeignKey('form_question.id'), nullable=True)
    
    # Generic question linking - questions can reference other questions
    # Use case: Review questions can link to application questions to display alongside
    linked_question_id = db.Column(db.Integer(), 
                                   db.ForeignKey('form_question.id'), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='questions', foreign_keys=[form_id])
    section = db.relationship('FormSection', back_populates='questions', foreign_keys=[section_id])
    translations = db.relationship('FormQuestionTranslation', lazy='dynamic',
                                   cascade='all, delete-orphan',
                                   back_populates='question')
    answers = db.relationship('FormAnswer', back_populates='question')
    linked_question = db.relationship('FormQuestion', remote_side=[id], 
                                     foreign_keys=[linked_question_id])
    
    def __init__(self, form_id, section_id, order, question_type, 
                 is_required=True, key=None, depends_on_question_id=None,
                 linked_question_id=None):
        self.form_id = form_id
        self.section_id = section_id
        self.order = order
        self.type = question_type
        self.is_required = is_required
        self.key = key
        self.depends_on_question_id = depends_on_question_id
        self.linked_question_id = linked_question_id
    
    def get_translation(self, language: str) -> 'FormQuestionTranslation':
        return self.translations.filter_by(language=language).first()


class FormQuestionTranslation(db.Model):
    """i18n support for questions."""
    __tablename__ = 'form_question_translation'
    __table_args__ = (
        db.UniqueConstraint('form_question_id', 'language'),
    )
    
    id = db.Column(db.Integer(), primary_key=True)
    form_question_id = db.Column(db.Integer(), 
                                 db.ForeignKey('form_question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    
    headline = db.Column(db.Text(), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    placeholder = db.Column(db.String(255), nullable=True)
    
    # Validation
    validation_regex = db.Column(db.String(500), nullable=True)
    validation_text = db.Column(db.Text(), nullable=True)
    
    # Options for multi-choice questions (JSON array)
    options = db.Column(db.JSON(), nullable=True)
    # Format: [{"value": "opt1", "label": "Option 1"}, ...]
    
    # Conditional visibility values
    show_for_values = db.Column(db.JSON(), nullable=True)
    
    question = db.relationship('FormQuestion', back_populates='translations')
    
    def __init__(self, form_question_id, language, headline, description=None,
                 placeholder=None, validation_regex=None, validation_text=None,
                 options=None, show_for_values=None):
        self.form_question_id = form_question_id
        self.language = language
        self.headline = headline
        self.description = description
        self.placeholder = placeholder
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.options = options
        self.show_for_values = show_for_values


class FormResponse(db.Model):
    """User's response to a form."""
    __tablename__ = 'form_response'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    
    # Lifecycle
    is_submitted = db.Column(db.Boolean(), nullable=False, default=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)
    is_withdrawn = db.Column(db.Boolean(), nullable=False, default=False)
    withdrawn_timestamp = db.Column(db.DateTime(), nullable=True)
    started_timestamp = db.Column(db.DateTime(), nullable=False)
    
    language = db.Column(db.String(2), nullable=False, default='en')
    
    # For multiple submissions.
    parent_response_id = db.Column(db.Integer(), 
                                   db.ForeignKey('form_response.id'), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='responses', foreign_keys=[form_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    answers = db.relationship('FormAnswer',
                             cascade='all, delete-orphan',
                             back_populates='response')
    parent_response = db.relationship('FormResponse', remote_side=[id],
                                     foreign_keys=[parent_response_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_form_response_lookup', 'form_id', 'user_id'),
        db.Index('idx_submitted_responses', 'form_id', 'is_submitted'),
    )
    
    def __init__(self, form_id, user_id, language='en', parent_response_id=None):
        self.form_id = form_id
        self.user_id = user_id
        self.language = language
        self.parent_response_id = parent_response_id
        self.is_submitted = False
        self.is_withdrawn = False
        self.started_timestamp = datetime.now()


class FormAnswer(db.Model):
    """Individual answer to a question."""
    __tablename__ = 'form_answer'
    
    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), 
                           db.ForeignKey('form_response.id'), nullable=False)
    question_id = db.Column(db.Integer(), 
                           db.ForeignKey('form_question.id'), nullable=False)
    
    value = db.Column(db.Text(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    created_on = db.Column(db.DateTime(), nullable=False)
    updated_on = db.Column(db.DateTime(), nullable=False)
    
    # For versioning/audit
    version = db.Column(db.Integer(), nullable=False, default=1)
    
    # Relationships
    response = db.relationship('FormResponse', back_populates='answers')
    question = db.relationship('FormQuestion', back_populates='answers')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_answer_lookup', 'question_id', 'response_id', 'is_active'),
        db.Index('idx_response_answers', 'response_id', 'is_active'),
    )
    
    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value
        self.is_active = True
        self.created_on = datetime.now()
        self.updated_on = datetime.now()
        self.version = 1
    
    def validate(self, language: str) -> Tuple[bool, Optional[ValidationError]]:
        """Validate answer against question rules."""
        question = self.question
        translation = question.get_translation(language)
        
        # Required check
        if question.is_required and not self.value:
            return False, ValidationError.REQUIRED

        if not translation:
            LOGGER.warning(f"No translation found for question {question.id} in language {language}")
            return True, None
        
        # Regex validation
        if translation.validation_regex and self.value:
            if not re.match(translation.validation_regex, self.value):
                return False, ValidationError.VALIDATION_REGEX_FAILED
        
        # Option validation for multi-choice
        if translation.options:
            valid_values = [opt['value'] for opt in translation.options]
            values = self.value.split(' ; ')
            if not all(v.strip() in valid_values for v in values):
                return False, ValidationError.INVALID_OPTION
        
        return True, None
