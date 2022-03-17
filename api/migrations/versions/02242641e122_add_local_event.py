"""Add a local event, application form, review form, registration form etc for testing.
Revision ID: 02242641e122
Revises: 85d13062a5e7
Create Date: 2020-02-27 21:43:16.303799

"""

# revision identifiers, used by Alembic.
revision = "02242641e122"
down_revision = "85d13062a5e7"

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
    organisation_id = db.Column(db.Integer(), nullable=False)
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

    def __init__(
        self,
        name,
        description,
        start_date,
        end_date,
        key,
        organisation_id,
        email_from,
        url,
        application_open,
        application_close,
        review_open,
        review_close,
        selection_open,
        selection_close,
        offer_open,
        offer_close,
        registration_open,
        registration_close,
        event_type,
    ):

        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.key = key
        self.organisation_id = organisation_id
        self.email_from = email_from
        self.url = url
        self.application_open = application_open
        self.application_close = application_close
        self.review_open = review_open
        self.review_close = review_close
        self.selection_open = selection_open
        self.selection_close = selection_close
        self.offer_open = offer_open
        self.offer_close = offer_close
        self.registration_open = registration_open
        self.registration_close = registration_close
        self.event_type = event_type


class ApplicationForm(Base):
    __tablename__ = "application_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)

    event = db.relationship("Event", foreign_keys=[event_id])
    nominations = db.Column(db.Boolean(), nullable=False)

    def __init__(self, event_id, is_open, nominations):
        self.event_id = event_id
        self.is_open = is_open
        self.nominations = nominations


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


class RegistrationForm(Base):

    __tablename__ = "registration_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)

    def __init__(self, event_id):
        self.event_id = event_id


def upgrade():
    local_event = Event(
        "Test Event",
        "Amazing Machine Learning Summer School 2020, 6-11 July 2021, Cape Town, South Africa",
        datetime.date(2021, 7, 6),
        datetime.date(2021, 7, 11),
        "test2021",
        3,
        "contact@testevent.com",
        "http://www.deeplearningindaba.com",
        datetime.date(2020, 2, 2),
        datetime.date(2021, 3, 20),
        datetime.date(2020, 2, 2),
        datetime.date(2021, 4, 20),
        datetime.date(2020, 2, 2),
        datetime.date(2021, 5, 20),
        datetime.date(2020, 2, 2),
        datetime.date(2021, 6, 20),
        datetime.date(2020, 2, 2),
        datetime.date(2021, 6, 30),
        EventType.EVENT,
    )

    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.add(local_event)
    session.commit()

    event_id = local_event.id

    application_form = ApplicationForm(event_id, True, False)
    session.add(application_form)
    session.commit()
    application_form_id = application_form.id

    # Copy application form sections from Indaba 2019
    query = """
    INSERT INTO section(application_form_id, name, description, "order")
    SELECT {}, section.name, section.description, section."order"
    FROM section
    WHERE application_form_id = 1
    """.format(
        application_form_id
    )
    op.get_bind().execute(query)

    # Copy application form questions from Indaba 2019
    query = """
    INSERT INTO question(application_form_id, section_id, type, description, "order", headline, options, is_required, placeholder, validation_regex, validation_text)
    SELECT 
        {application_form_id},
        (select id from section where name = s.name and application_form_id={application_form_id}) as section_id,
        q.type,
        q.description,
        q."order",
        q.headline,
        q.options,
        q.is_required,
        q.placeholder,
        q.validation_regex,
        q.validation_text
    FROM question q
    INNER JOIN section s on q.section_id = s.id
    WHERE q.application_form_id = 1
    """.format(
        application_form_id=application_form_id
    )
    op.get_bind().execute(query)

    # Make file types optional because file uploads don't work locally (yet)
    op.get_bind().execute(
        """UPDATE question SET is_required=False WHERE application_form_id={} AND type='file'""".format(
            application_form_id
        )
    )

    op.get_bind().execute(
        """SELECT setval('review_form_id_seq', (SELECT max(id) FROM review_form));"""
    )
    review_form = ReviewForm(application_form_id, datetime.date(2021, 6, 30))
    session.add(review_form)
    session.commit()
    review_form_id = review_form.id

    op.get_bind().execute(
        """SELECT setval('review_question_id_seq', (SELECT max(id) FROM review_question));"""
    )
    query = """
    INSERT INTO review_question(review_form_id, question_id, description, headline, type, placeholder, options, is_required, "order", validation_regex, validation_text, weight)
    SELECT 
        {review_form_id},
        (select id from question where headline = qq.headline and application_form_id={application_form_id}) as question_id,
        q.description,
        q.headline,
        q.type,
        q.placeholder,
        q.options,
        q.is_required,
        q."order",
        q.validation_regex,
        q.validation_text,
        q.weight
    FROM review_question q
    LEFT JOIN question qq ON q.question_id = qq.id
    WHERE q.review_form_id = 1
    """.format(
        review_form_id=review_form_id, application_form_id=application_form_id
    )
    op.get_bind().execute(query)

    op.get_bind().execute(
        """SELECT setval('registration_form_id_seq', (SELECT max(id) FROM registration_form));"""
    )
    registration_form = RegistrationForm(event_id)
    session.add(registration_form)
    session.commit()
    registration_form_id = registration_form.id

    op.get_bind().execute(
        """SELECT setval('registration_section_id_seq', (SELECT max(id) FROM registration_section));"""
    )

    query = """
    INSERT INTO registration_section(registration_form_id, name, description, "order", show_for_travel_award, show_for_accommodation_award, show_for_payment_required)
    SELECT {}, name, description, "order", show_for_travel_award, show_for_accommodation_award, show_for_payment_required
    FROM registration_section
    WHERE registration_form_id = 1
    """.format(
        registration_form_id
    )
    op.get_bind().execute(query)

    op.get_bind().execute(
        """SELECT setval('registration_question_id_seq', (SELECT max(id) FROM registration_question));"""
    )

    query = """
    INSERT INTO registration_question(registration_form_id, section_id, type, description, headline, placeholder, validation_regex, validation_text, "order", options, is_required, depends_on_question_id, hide_for_dependent_value, required_value)
    SELECT 
        {registration_form_id},
        (
            select id from registration_section 
            where name = s.name 
            and (show_for_payment_required is null or show_for_payment_required = s.show_for_payment_required)
            and registration_form_id={registration_form_id}
        ) as section_id,
        q.type,
        q.description,
        q.headline,
        q.placeholder,
        q.validation_regex,
        q.validation_text,
        q."order",
        q.options,
        q.is_required,
        null,
        null,
        q.required_value
    FROM registration_question q
    INNER JOIN registration_section s on q.section_id = s.id
    WHERE q.registration_form_id = 1
    """.format(
        registration_form_id=registration_form_id
    )
    op.get_bind().execute(query)

    op.get_bind().execute(
        """UPDATE organisation set system_url='http://localhost:8080' where id=3"""
    )


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    query = """
    DELETE FROM registration_question 
    WHERE registration_form_id = (
        select registration_form.id from registration_form
        inner join event on registration_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM registration_section 
    WHERE registration_form_id = (
        select registration_form.id from registration_form
        inner join event on registration_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM registration_form 
    WHERE id = (
        select registration_form.id from registration_form
        inner join event on registration_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM review_question 
    WHERE review_form_id = (
        select review_form.id from review_form
        inner join application_form on review_form.application_form_id = application_form.id
        inner join event on application_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM review_form 
    WHERE id = (
        select review_form.id from review_form
        inner join application_form on review_form.application_form_id = application_form.id
        inner join event on application_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM question 
    WHERE application_form_id = (
        select application_form.id from application_form
        inner join event on application_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM section 
    WHERE application_form_id = (
        select application_form.id from application_form
        inner join event on application_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM application_form 
    WHERE id = (
        select application_form.id from application_form
        inner join event on application_form.event_id = event.id
        where event.organisation_id = 3
    )"""
    op.get_bind().execute(query)

    query = """
    DELETE FROM event 
    WHERE organisation_id = 3
    """
    op.get_bind().execute(query)

    op.get_bind().execute(
        """UPDATE organisation set system_url='http://localhost' where id=3"""
    )
