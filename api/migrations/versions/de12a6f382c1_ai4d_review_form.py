"""Add Review Form for AI4D Innovation Grant

Revision ID: de12a6f382c1
Revises: 964ead196cb9
Create Date: 2020-07-07 20:25:17.960122

"""

# revision identifiers, used by Alembic.
revision = 'de12a6f382c1'
down_revision = '964ead196cb9'

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


def find_question(session, headline, application_form_id):
    return session.query(Question).filter_by(headline=headline, application_form_id=application_form_id).first()


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='ai4d2020').first()
    application_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    form = ReviewForm(application_form.id, datetime.datetime(2020, 7, 31))
    session.add(form)
    session.commit()

    config = ReviewConfiguration(form.id, 2)
    session.add(config)
    session.commit()

    project_name_question = find_question(session, 'Project Name', application_form.id)
    project_name_info = ReviewQuestion(form.id, 'information', False, 1, question_id=project_name_question.id, headline='Project Name')

    proposal_question = find_question(session, 'Your Proposal', application_form.id)
    proposal_info = ReviewQuestion(form.id, 'file', False, 2, question_id=proposal_question.id, headline='Proposal')

    clarity = ReviewQuestion(form.id, 'multi-choice', True, 3, description="""
4: very clear and novel hypothesis, includes ML/AI/DS component
3: research hypothesis clear, not necessarily novel, includes ML/AI/DS component
2: research hypothesis clear but marginal use of ML/AI/DS
1: research hypothesis is unclear""", headline='Clarity and novelty of research hypothesis applying ML/AI/DS', 
    options=[
        {'value': 4, 'label': '4'},
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}
        ])

    ethical = ReviewQuestion(form.id, 'multi-choice', True, 4, description="""
3: thorough legal, ethical and social analysis done, if research involves human participants, ethical research approval has been obtained
2: legal, ethical and social analysis is wanting, if research involves human participants, ethical research approval has been obtained
1: research involves human participants, no ethical research approval obtained
""", headline='Ethical review', 
    options=[
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    feasibility = ReviewQuestion(form.id, 'multi-choice', True, 5, description="""
4: objectives and outcomes are clearly stated and feasible
3: some objectives and outcomes not clear or not feasible
2: unclear objectives and/or outcomes
1: no objectives and/or outcomes stated
""", headline='Feasibility of objectives and outcomes', 
    options=[
        {'value': 4, 'label': '4'},
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    attainability = ReviewQuestion(form.id, 'multi-choice', True, 6, description="""
4: Activity timelines are clearly stated, reasonable and attainable within the stipulated 6 month period
3: clear activity timelines but may require more than 6 months to execute and complete
2: Timelines given but not clear, make little sense
1: no activity timelines given
""", headline='Attainability of activity timelines', 
    options=[
        {'value': 4, 'label': '4'},
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    challenging = ReviewQuestion(form.id, 'multi-choice', True, 7, description="""
3: task at hand is challenging and provides room for subsequent iterations beyond the funded 6 months phase
2: task at hand is challenging, but no evidence of potential long-term ambitions for future work
1: task at hand is not challenging, will not grow/stretch the team
""", headline='Challenging task with long term goal', 
    options=[
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    budget = ReviewQuestion(form.id, 'multi-choice', True, 8, description="""
2: amount of funding requested is clearly stated, is tied in with activity timelines and schedule is feasible
1: unclear budget allocation, not tied in with activity timeline
""", headline='Budget allocation', 
    options=[
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    team = ReviewQuestion(form.id, 'multi-choice', True, 9, description="""
3: details of the team/leads are given and they demonstrate a strong ability to undertake and complete the project/research at hand
2: details of the team given but they lack foundational capability to undertake and complete the work, even with mentorship support
1: little information given about the team, no demonstration of ability to undertake the research/task
""", headline='Quality of team', 
    options=[
        {'value': 3, 'label': '3'},
        {'value': 2, 'label': '2'},
        {'value': 1, 'label': '1'}])

    overall = ReviewQuestion(form.id, 'multi-choice', True, 10, description="""Overall evaluation - Do you recommend this proposal for funding?""", headline='Overall evaluation', 
    options=[
        {'value': 3, 'label': 'Strong Recommend'},
        {'value': 2, 'label': 'Recommend'},
        {'value': 1, 'label': 'Weak Recommend'},
        {'value': 0, 'label': 'Borderline Submission'},
        {'value': -1, 'label': 'Weak Reject'},
        {'value': -2, 'label': 'Reject'},
        {'value': -3, 'label': 'Strong Reject'}])

    confidence = ReviewQuestion(form.id, 'multi-choice', True, 11, description="""Your confidence in your assessment""", headline="Reviewer's confidence", 
    options=[
        {'value': 4, 'label': 'Expert'},
        {'value': 3, 'label': 'High'},
        {'value': 2, 'label': 'Medium'},
        {'value': 1, 'label': 'Low'}])

    other = ReviewQuestion(form.id, 'long-text', True, 12, description="""Any other remarks not covered by previous questions?""", headline="Other Remarks")

    session.add_all([
        project_name_info,
        proposal_info,
        clarity,
        ethical,
        feasibility,
        attainability,
        challenging,
        budget,
        team,
        overall,
        confidence,
        other
    ])

    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    
    event = session.query(Event).filter_by(key='ai4d2020').first()
    application_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    form = session.query(ReviewForm).filter_by(application_form_id=application_form.id).first()
    if form:
        session.query(ReviewQuestion).filter_by(review_form_id=form.id).delete()
        session.query(ReviewConfiguration).filter_by(review_form_id=form.id).delete()
    
    form = session.query(ReviewForm).filter_by(application_form_id=application_form.id).delete()
    
    session.commit()
    session.flush()
