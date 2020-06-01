"""Add EEML Review form

Revision ID: 6d34d1ab6864
Revises: a4662031beca
Create Date: 2020-04-12 20:59:04.904875

"""

# revision identifiers, used by Alembic.
revision = '6d34d1ab6864'
down_revision = 'a4662031beca'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime
from enum import Enum

Base = declarative_base()

class EventType(Enum):
    EVENT = 'event'
    AWARD = 'award'


class Event(Base):
    __tablename__ = 'event'
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


class ApplicationForm(Base):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)


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
    key = db.Column(db.String(255), nullable=True)


class ReviewForm(Base):
    __tablename__ = 'review_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    def __init__(self, application_form_id, deadline):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline

    def close(self):
        self.is_open = False


class ReviewQuestion(Base):
    __tablename__ = 'review_question'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
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

    def __init__(self,
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
                 weight=0):
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
    __tablename__ = 'review_configuration'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=True)
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)

    def __init__(self, review_form_id, num_reviews_required, num_optional_reviews=0, drop_optional_question_id=None, drop_optional_agreement_values=None):
        self.review_form_id = review_form_id
        self.num_reviews_required = num_reviews_required
        self.num_optional_reviews = num_optional_reviews
        self.drop_optional_question_id = drop_optional_question_id
        self.drop_optional_agreement_values = drop_optional_agreement_values


def find_question(session, headline):
    return session.query(Question).filter_by(headline=headline).first()


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    
    op.get_bind().execute("""SELECT setval('review_form_id_seq', (SELECT max(id) FROM review_form));""")
    op.get_bind().execute("""SELECT setval('review_question_id_seq', (SELECT max(id) FROM review_question));""")

    event = session.query(Event).filter_by(key='eeml2020').first()
    application_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    form = ReviewForm(application_form.id, datetime.datetime(2020, 5, 20))
    session.add(form)
    session.commit()

    affiliation_question = find_question(session, 'Affiliation')
    affiliation_info = ReviewQuestion(form.id, 'information', False, 1, question_id=affiliation_question.id, headline='Affiliation')

    research_interests_question = find_question(session, 'Research Interests')
    research_interests_info = ReviewQuestion(form.id, 'information', False, 2, question_id=research_interests_question.id, headline='Research Interests')

    extended_abstract_type = find_question(session, 'Extended abstract type')
    extended_abstract_type_info = ReviewQuestion(form.id, 'information', False, 3, question_id=extended_abstract_type.id)

    extended_abstract_question = find_question(session, 'Extended abstract')
    extended_abstract_info = ReviewQuestion(form.id, 'information', False, 4, question_id=extended_abstract_question.id)

    cv_question = find_question(session, 'CV')
    cv_info = ReviewQuestion(form.id, 'information', False, 5, question_id=cv_question.id, headline='CV')

    financial_support_question = find_question(session, 'Motivation')
    financial_support_info = ReviewQuestion(form.id, 'information', False, 6, question_id=financial_support_question.id, headline='Financial Support Motivation')

    ten_scale = [
        {'value': 1, 'label': '1'},
        {'value': 2, 'label': '2'},
        {'value': 3, 'label': '3'},
        {'value': 4, 'label': '4'},
        {'value': 5, 'label': '5'},
        {'value': 6, 'label': '6'},
        {'value': 7, 'label': '7'},
        {'value': 8, 'label': '8'},
        {'value': 9, 'label': '9'},
        {'value': 10, 'label': '10'},
    ]

    benefit = ReviewQuestion(form.id, 'multi-choice', True, 7, description="""
1 - 4: the person would not benefit as they lack basic knowledge OR the application is incomplete (e.g. abstract has one short paragraph)
5: borderline, the person has some minimal knowledge and seem keen to learn more
6-7: the person has potential, they are enthusiastic about the field and/or the school, but they are not very strong (e.g. common for a highschool student or beginner) OR the person is good, but they could easily attend a similar event someplace else OR the person is good but have not put a lot of effort in the application
8-10: the person is technically very good and they are very enthusiastic (e.g. put effort in the application), OR the person is good and they would not be able to easily attend summer schools/conferences in the West (eg if they are affiliated to a smaller EE university)
    """, headline='Would this person benefit from attending the school?', 
    options=ten_scale)

    school = ReviewQuestion(form.id, 'multi-choice', True, 8, description="""
1-4: they have poor technical skills
5-7: they have some technical skills, but nothing extraordinary
8-10: they have strong technical skills, they are enthusiastic, good communicators, exposure to different ML topics so could discuss on a variety of topics
""", headline='Would the school benefit from this person''s participation?', options=ten_scale)

    assessment = ReviewQuestion(form.id, 'long-text', True, 9, description="""
Write 2-3 sentences that explain the scores given above; also indicate the topic the person is working on -- this will help us obtain a good coverage of topics.
""", headline='Overall assessment')

    session.add_all([
        affiliation_info,
        research_interests_info,
        extended_abstract_type_info,
        extended_abstract_info,
        cv_info,
        financial_support_info,
        benefit,
        school,
        assessment
    ])
    session.commit()

    config = ReviewConfiguration(form.id, 2)
    session.add(config)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    
    event = session.query(Event).filter_by(key='eeml2020').first()
    application_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    form = session.query(ReviewForm).filter_by(application_form_id=application_form.id).first()
    if form:
        session.query(ReviewQuestion).filter_by(review_form_id=form.id).delete()
        session.query(ReviewConfiguration).filter_by(review_form_id=form.id).delete()
    
    form = session.query(ReviewForm).filter_by(application_form_id=application_form.id).delete()
    
    session.commit()
    session.flush()

    op.get_bind().execute("""SELECT setval('review_form_id_seq', (SELECT max(id) FROM review_form));""")
    op.get_bind().execute("""SELECT setval('review_question_id_seq', (SELECT max(id) FROM review_question));""")