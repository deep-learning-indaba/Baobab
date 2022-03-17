"""Update EEML Review Form

Revision ID: 2279e1fa2e49
Revises: eb6f96db82e8
Create Date: 2020-04-30 22:32:09.094600

"""

# revision identifiers, used by Alembic.
revision = "2279e1fa2e49"
down_revision = "eb6f96db82e8"

import datetime
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()


class EventType(Enum):
    EVENT = "event"
    AWARD = "award"


class Event(Base):
    __tablename__ = "event"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    key = db.Column(db.String(255), nullable=False, unique=True)
    organisation_id = db.Column(
        db.Integer(), db.ForeignKey("organisation.id"), nullable=False
    )
    email_from = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)

    application_open = db.Column(db.DateTime(), nullable=False)
    application_close = db.Column(db.DateTime(), nullable=False)
    review_open = db.Column(db.DateTime(), nullable=False)
    review_close = db.Column(db.DateTime(), nullable=False)
    selection_open = db.Column(db.DateTime(), nullable=False)
    selection_close = db.Column(db.DateTime(), nullable=False)
    offer_open = db.Column(db.DateTime(), nullable=False)
    offer_close = db.Column(db.DateTime(), nullable=False)
    registration_open = db.Column(db.DateTime(), nullable=False)
    registration_close = db.Column(db.DateTime(), nullable=False)
    event_type = db.Column(db.Enum(EventType), nullable=False)


class ApplicationForm(Base):
    __tablename__ = "application_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)


class Question(Base):
    __tablename__ = "question"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    section_id = db.Column(db.Integer(), db.ForeignKey("section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(
        db.Integer(), db.ForeignKey("question.id"), nullable=True
    )
    show_for_values = db.Column(db.JSON(), nullable=True)
    key = db.Column(db.String(255), nullable=True)


class ReviewForm(Base):
    __tablename__ = "review_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    def __init__(self, application_form_id, deadline):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline

    def close(self):
        self.is_open = False


class ReviewQuestion(Base):
    __tablename__ = "review_question"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=True)
    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=True)
    type = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    weight = db.Column(db.Float(), nullable=False)

    def __init__(
        self,
        review_form_id,
        type,
        is_required,
        order,
        question_id=None,
        description=None,
        headline=None,
        placeholder=None,
        options=None,
        validation_regex=None,
        validation_text=None,
        weight=0,
    ):
        self.review_form_id = review_form_id
        self.question_id = question_id
        self.description = description
        self.headline = headline
        self.type = type
        self.placeholder = placeholder
        self.options = options
        self.is_required = is_required
        self.order = order
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.weight = weight


class ReviewConfiguration(Base):
    __tablename__ = "review_configuration"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=True
    )
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)

    def __init__(
        self,
        review_form_id,
        num_reviews_required,
        num_optional_reviews=0,
        drop_optional_question_id=None,
        drop_optional_agreement_values=None,
    ):
        self.review_form_id = review_form_id
        self.num_reviews_required = num_reviews_required
        self.num_optional_reviews = num_optional_reviews
        self.drop_optional_question_id = drop_optional_question_id
        self.drop_optional_agreement_values = drop_optional_agreement_values


def find_question(session, headline):
    return session.query(Question).filter_by(headline=headline).first()


def update_review_question_order(session, headline, new_order):
    review_question = session.query(ReviewQuestion).filter_by(headline=headline).first()
    if review_question is None:
        review_question = (
            session.query(ReviewQuestion)
            .join(Question, ReviewQuestion.question_id == Question.id)
            .filter(Question.headline == headline)
            .first()
        )

    review_question.order = new_order


def delete_review_question(session, form_id, headline):
    session.query(ReviewQuestion).filter_by(
        review_form_id=form_id, headline=headline
    ).delete()


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key="eeml2020").first()
    application_form = (
        session.query(ApplicationForm).filter_by(event_id=event.id).first()
    )
    form = (
        session.query(ReviewForm)
        .filter_by(application_form_id=application_form.id)
        .first()
    )

    divider1 = ReviewQuestion(
        form.id, "section-divider", False, 1, headline="Candidate Application"
    )
    session.add(divider1)

    category_question = find_question(session, "I Am:")
    category_info = ReviewQuestion(
        form.id,
        "information",
        False,
        2,
        question_id=category_question.id,
        headline="Applicant Category",
    )
    session.add(category_info)

    update_review_question_order(session, "Affiliation", 3)

    country_question = find_question(session, "Country")
    country_info = ReviewQuestion(
        form.id,
        "information",
        False,
        4,
        question_id=country_question.id,
        headline="Country",
    )
    session.add(country_info)

    research_group_question = find_question(session, "Research Group / Laboratory")
    research_group_info = ReviewQuestion(
        form.id,
        "information",
        False,
        5,
        question_id=research_group_question.id,
        headline="Research Group / Laboratory",
    )
    session.add(research_group_info)

    supervisor_question = find_question(session, "Supervisor")
    supervisor_info = ReviewQuestion(
        form.id,
        "information",
        False,
        6,
        question_id=supervisor_question.id,
        headline="Supervisor",
    )
    session.add(supervisor_info)

    previous_attendance_question = find_question(session, "Previous attendance")
    previous_attendance_info = ReviewQuestion(
        form.id,
        "information",
        False,
        7,
        question_id=previous_attendance_question.id,
        headline="Previous attendance",
    )
    session.add(previous_attendance_info)

    update_review_question_order(session, "Research Interests", 8)
    update_review_question_order(session, "Extended abstract type", 9)
    update_review_question_order(session, "Extended abstract", 10)
    update_review_question_order(session, "CV", 11)

    session.query(ReviewQuestion).filter_by(
        headline="Financial Support Motivation"
    ).delete()

    divider2 = ReviewQuestion(
        form.id, "section-divider", False, 12, headline="Your Review"
    )
    session.add(divider2)

    project = ReviewQuestion(
        form.id,
        "long-text",
        True,
        13,
        description="Please describe in 2-3 sentences what the project is about",
        headline="Project",
    )
    session.add(project)

    update_review_question_order(
        session, "Would this person benefit from attending the school?", 14
    )
    update_review_question_order(
        session, "Would the school benefit from this person" "s participation?", 15
    )
    update_review_question_order(session, "Overall assessment", 16)

    session.commit()
    session.flush()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key="eeml2020").first()
    application_form = (
        session.query(ApplicationForm).filter_by(event_id=event.id).first()
    )
    form = (
        session.query(ReviewForm)
        .filter_by(application_form_id=application_form.id)
        .first()
    )

    to_delete = [
        "Applicant Category",
        "Candidate Application",
        "Research Group / Laboratory",
        "Country",
        "Research Group / Laboratory",
        "Supervisor",
        "Previous attendance",
        "Your Review",
        "Project",
    ]

    for headline in to_delete:
        delete_review_question(session, form.id, headline)

    financial_support_question = find_question(session, "Motivation")
    financial_support_info = ReviewQuestion(
        form.id,
        "information",
        False,
        6,
        question_id=financial_support_question.id,
        headline="Financial Support Motivation",
    )
    session.add(financial_support_info)

    session.commit()
    session.flush()
