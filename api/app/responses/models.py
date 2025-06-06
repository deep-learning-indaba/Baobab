from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import column_property

import re
import enum
from typing import Tuple, Optional
from app import db, LOGGER
from app.applicationModel.models import Question
from app.tags.models import Tag
from app.users.models import AppUser


class ValidationError(str, enum.Enum):
    REQUIRED = 'required'
    INVALID_OPTION = 'invalid_option'
    VALIDATION_REGEX_FAILED = 'validation_regex_failed'


class Response(db.Model):
    __tablename__ = "response"

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey("application_form.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("app_user.id"), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)
    is_withdrawn = db.Column(db.Boolean(), nullable=False)
    withdrawn_timestamp = db.Column(db.DateTime(), nullable=True)
    started_timestamp = db.Column(db.DateTime(), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    parent_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=True)

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    user: AppUser = db.relationship('AppUser', foreign_keys=[user_id])
    answers = db.relationship('Answer', order_by='Answer.order', primaryjoin="and_(Response.id==Answer.response_id, "
                                                                             "Answer.is_active==True)")
    response_tags = db.relationship('ResponseTag')
    reviewers = db.relationship('ResponseReviewer')

    __table_args__ = (
        db.Index("response_application_form_lookup", "application_form_id",
        postgresql_where=is_submitted.is_(True)),
    )

    def __init__(self, application_form_id, user_id, language, parent_id=None):
        self.application_form_id = application_form_id
        self.user_id = user_id
        self.is_submitted = False
        self.submitted_timestamp = None
        self.is_withdrawn = False
        self.withdrawn_timestamp = None
        self.started_timestamp = date.today()
        self.language = language
        self.parent_id = parent_id

    def submit(self):
        self.is_submitted = True
        self.submitted_timestamp = datetime.now()
        self.is_withdrawn = False
        self.withdrawn_timestamp = None

    def withdraw(self):
        self.is_withdrawn = True
        self.withdrawn_timestamp = datetime.now()
        self.is_submitted = False
        self.submitted_timestamp = None


class Answer(db.Model):
    __tablename__ = "answer"
    __table_args__ = tuple([
        db.Index("answer_question_lookup", "question_id", "response_id", "is_active"),
        db.Index("answer_response_lookup", "response_id", "is_active")
    ])

    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=False)
    value = db.Column(db.String(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    question = db.relationship('Question', foreign_keys=[question_id])
    order = column_property(select([Question.order]).where(Question.id == question_id).correlate_except(Question))

    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value
        self.is_active = True
        self.created_on = datetime.now()

    def deactivate(self):
        self.is_active = False

    @property
    def value_display(self):
        question_translation = self.question.get_translation(self.response.language)
        if question_translation is None:
            LOGGER.error('Missing {} translation for question {}'.format(self.response.language, self.question.id))
            question_translation = self.question.get_translation('en')
        if self.question.type == 'multi-choice' and question_translation.options is not None:
            option = [option for option in question_translation.options if option['value'] == self.value]
            if option:
                return option[0]['label']
        return self.value
    
    def is_valid(self, language: str) -> Tuple[bool, Optional[ValidationError]]:
        if self.question.is_required and not self.value:
            return False, ValidationError.REQUIRED
        
        question_translation = self.question.get_translation(language)
        if question_translation is None:
            LOGGER.error('Missing {} translation for question {}'.format(language, self.question.id))
            question_translation = self.question.get_translation('en')

        if question_translation.options:
            if self.question.type == "multi-choice" and self.value not in [option['value'] for option in question_translation.options]:
                return False, ValidationError.INVALID_OPTION
            if self.question.type == 'mutli-checkbox':
                for value in self.value.split(' ; '):
                    if value.strip() not in [option['value'] for option in question_translation.options]:
                        return False, ValidationError.INVALID_OPTION
        
        validation_regex = question_translation.validation_regex
        if validation_regex and not re.match(validation_regex, self.value):
            return False, ValidationError.VALIDATION_REGEX_FAILED

        return True, None


class ResponseReviewer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    reviewer_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    user = db.relationship('AppUser', foreign_keys=[reviewer_user_id])

    def __init__(self, response_id, reviewer_user_id):
        self.response_id = response_id
        self.reviewer_user_id = reviewer_user_id
        self.active = True

    def deactivate(self):
        self.active = False

class ResponseTag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)

    response = db.relationship('Response', foreign_keys=[response_id])
    tag = db.relationship('Tag', foreign_keys=[tag_id])

    def __init__(self, response_id, tag_id):
        self.response_id = response_id
        self.tag_id = tag_id
