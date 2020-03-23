"""empty message

Revision ID: c795c179c2b2
Revises: af9c317d2c92
Create Date: 2020-03-12 19:32:20.943531

"""

# revision identifiers, used by Alembic.
revision = 'c795c179c2b2'
down_revision = 'af9c317d2c92'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from app import db
from enum import Enum
import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Organisation(Base):

    __tablename__ = "organisation"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    system_name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    email_from = db.Column(db.String(100), nullable=True)
    system_url = db.Column(db.String(100), nullable=False)
    privacy_policy = db.Column(db.String(100), nullable=False)

    def __init__(self, name, system_name, small_logo, large_logo, domain, url, email_from, system_url, privacy_policy):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.domain = domain
        self.system_name = system_name
        self.url = url
        self.email_from = email_from
        self.system_url = system_url
        self.privacy_policy = privacy_policy

class Country(Base):

    __tablename__ = "country"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, name):
        self.name = name

class EventType(Enum):
    EVENT = 'event'
    AWARD = 'award'

class Event(Base):

    __tablename__ = "event"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    key = db.Column(db.String(255), nullable=False, unique=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey(
        'organisation.id'), nullable=False)
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

    def __init__(self,
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
                 event_type
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
        self.event_roles = []
        self.event_type = event_type

class ApplicationForm(Base):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    nominations = db.Column(db.Boolean(), nullable=False)

    def __init__(self, event_id, is_open, nominations):
        self.event_id = event_id
        self.is_open = is_open
        self.nominations = nominations

class Question(Base):
    __tablename__ = 'question'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

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


class Section(Base):
    __tablename__ = 'section'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id', use_alter=True), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

    def __init__(self, application_form_id, name, description, order):
        self.application_form_id = application_form_id
        self.name = name
        self.description = description
        self.order = order

def get_country_list(session):
    countries = session.query(Country).all()
    country_list = []
    for country in countries:
        country_list.append({
            'label': country.name,
            'value': country.name
        })
    return country_list

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # pass
    # ### end Alembic commands ###
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Update section title for Kambule Doctoral Dissertation award
    event = session.query(Event).filter_by(key='kambuledoctoral2020').first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    # Updating main section
    section = session.query(Section).filter_by(name='Thamsanqa Kambule Doctoral Dissertation Award 2020').first()
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.headline == 'Nomination Capacity').first()
    question.validation_regex = None

    # Updating nominator section
    section = session.query(Section).filter(Section.application_form_id == app_form.id, Section.order == 2).first()
    section.name = 'Nominator Information'
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 1).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 2).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 3).first()
    question.validation_regex = None

    # Updating candidate section
    section = session.query(Section).filter_by(name='Doctoral Candidate Information').first()
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 1).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 2).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 3).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 4).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 5).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 6).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 7).first()
    question.validation_regex = None

    # Updating dissertation section
    section = session.query(Section).filter_by(name='Doctoral dissertation information').first()
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 1).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 2).first()
    question.validation_regex = r'^\s*(\S+(\s+|$)){0,800}$'
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 3).first()
    question.validation_regex = r'^\s*(\S+(\s+|$)){400,500}$'
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 4).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 5).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 6).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 7).first()
    question.validation_regex = None

    # Updating dissertation section
    section = session.query(Section).filter_by(name='Supporting Documentation').first()
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 1).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 2).first()
    question.validation_regex = None
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 3).first()
    question.validation_regex = None
    question.options = {"min_num_referrals": 1, "max_num_referrals": 1}
    question = session.query(Question).filter(Question.section_id == section.id,
                                              Question.order == 4).first()
    question.validation_regex = None

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
