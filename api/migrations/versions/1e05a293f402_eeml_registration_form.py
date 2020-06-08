"""EEML 2020 Registration Form

Revision ID: 1e05a293f402
Revises: 91a7bc19a5ec
Create Date: 2020-06-07 16:02:52.489825

"""

# revision identifiers, used by Alembic.
revision = '1e05a293f402'
down_revision = '91a7bc19a5ec'

from alembic import op
import sqlalchemy as sa

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
    travel_grant = db.Column(db.Boolean(), nullable=False)

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
                 event_type,
                 travel_grant
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
        self.travel_grant = travel_grant

class RegistrationForm(Base):

    __tablename__ = "registration_form"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)

    def __init__(self, event_id):
        self.event_id = event_id


class RegistrationSection(Base):

    __tablename__ = "registration_section"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    show_for_travel_award = db.Column(db.Boolean(), nullable=True)
    show_for_accommodation_award = db.Column(db.Boolean(), nullable=True)
    show_for_payment_required = db.Column(db.Boolean(), nullable=True)

    def __init__(self, registration_form_id, name, description, order, show_for_travel_award, show_for_accommodation_award, show_for_payment_required):
        self.registration_form_id = registration_form_id
        self.name = name
        self.description = description
        self.order = order
        self.show_for_payment_required = show_for_payment_required
        self.show_for_accommodation_award = show_for_accommodation_award
        self.show_for_travel_award = show_for_travel_award

class RegistrationQuestion(Base):

    __tablename__ = "registration_question"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=False)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    required_value = db.Column(db.String(), nullable=True)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_question.id"), nullable=True)
    hide_for_dependent_value = db.Column(db.String(), nullable=True)

    def __init__(self, registration_form_id, section_id, headline, placeholder, order, type, validation_regex, validation_text=None, is_required=True, description='', options=None):
        self.registration_form_id = registration_form_id
        self.section_id = section_id
        self.headline = headline
        self.placeholder = placeholder
        self.order = order
        self.type = type
        self.description = description
        self.options = options
        self.is_required = is_required
        self.validation_regex = validation_regex
        self.validation_text = validation_text

def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key='eeml2020').first()

    form = RegistrationForm(event.id)
    session.add(form)
    session.commit()

    mentorship = RegistrationSection(form.id, 'Mentorship', '', 1, None, None, None)
    session.add(mentorship)
    session.commit()
    
    yes_no = [
        {'value': 'yes', 'label': 'Yes'},
        {'value': 'no', 'label': 'No'}
    ]
    mentorship_q1 = RegistrationQuestion(form.id, mentorship.id, 'Would you be interested in a mentorship session?', 'Choose an option', 1, 'multi-choice', None, None, True, 'We have a limited number of spots for 1:1 mentorship sessions (15 minutes by teleconference) with speakers from the school or other ML experts. Would you be interested in such a session?', options=yes_no)
    session.add(mentorship_q1)
    session.commit()

    mentorship_q2 = RegistrationQuestion(form.id, mentorship.id, 'On what topic would you like to ask questions?', 'Choose an option', 2, 'choice-with-other', None, None, True, options=[
        {'value': 'career-advice', 'label': 'Career advice'},
        {'value': 'reinforcement-learning', 'label': 'Reinforcement learning'},
        {'value': 'unsupervised-learning', 'label': 'Unsupervised learning'},
        {'value': 'computer-vision', 'label': 'Computer Vision'},
        {'value': 'nlp', 'label': 'NLP'},
        {'value': 'theory-of-deep-learning', 'label': 'Theory of Deep Learning'},
    ])
    mentorship_q2.depends_on_question_id = mentorship_q1.id
    mentorship_q2.hide_for_dependent_value = 'no'

    mentorship_q3 = RegistrationQuestion(form.id, mentorship.id, 'Any other information we should have when doing the matching?', '', 3, 'long-text', None, is_required=False, description='e.g. expert from academia or industry, preferred gender/race of the expert for you to be more comfortable in the discussion etc.')
    mentorship_q3.depends_on_question_id = mentorship_q1.id
    mentorship_q3.hide_for_dependent_value = 'no'

    mentorship_q4 = RegistrationQuestion(form.id, mentorship.id, 'Mentorship discussions are scheduled normally during lunch time (13:10-15:00 CEST time). If this time does not work for you because of the time zone, please indicate another time (in CEST), and we will do our best to accommodate that.', 'Choose an option', 4, 'choice-with-other', None, None, is_required=True, options=[
        {'value': 'yes', 'label': 'Yes, 13:10-15:00 CEST time works for me'},
    ])
    mentorship_q4.depends_on_question_id = mentorship_q1.id
    mentorship_q4.hide_for_dependent_value = 'no'

    session.add_all([mentorship_q2, mentorship_q3, mentorship_q4])
    session.commit()

    background = RegistrationSection(form.id, 'Your Background', '', 2, None, None, None)
    session.add(background)
    session.commit()

    background_q1 = RegistrationQuestion(form.id, background.id, 'What topic are you most familiar with?', '', 1, 'multi-checkbox-with-other', None, options=[
        {'value': 'reinforcementLearning', 'label': 'Reinforcement learning'},
        {'value': 'unsupervisedAndGenerative', 'label': 'Unsupervised learning & Generative Models'},
        {'value': 'computerVision', 'label': 'Computer Vision'},
        {'value': 'rnnNlp', 'label': 'RNNs & NLP'},
        {'value': 'theoryDeepLearning', 'label': 'Theory of Deep Learning'},
        {'value': 'robotics', 'label': 'Robotics'},
    ])
    background_q2 = RegistrationQuestion(form.id, background.id, 'Please indicate your level of familiarity with Python.', '', 2, 'multi-choice', None, options=[
        {'value': '1', 'label': '1 - never used or used very rarely'},
        {'value': '2', 'label': '2'},
        {'value': '3', 'label': '3'},
        {'value': '4', 'label': '4'},
        {'value': '5', 'label': '5 - very familiar'},
    ])
    background_q3 = RegistrationQuestion(form.id, background.id, 'Which Deep Learning library are you most familiar with?', '', 3, 'multi-checkbox-with-other', None, options=[
        {'value': 'pytorch', 'label': 'Pytorch'},
        {'value': 'tensorflow1', 'label': 'Tensorflow 1'},
        {'value': 'tensorflow2', 'label': 'Tensorflow 2'},
        {'value': 'jax', 'label': 'Jax'},
        {'value': 'none', 'label': """I haven't used a DL library before"""},
    ])
    background_q4 = RegistrationQuestion(form.id, background.id, 'The online school will rely on a number of platforms. Please confirm that you will be able to install and/or use the following:', '', 4, 'multi-checkbox', None, options=[
        {'value': 'gmail', 'label': 'Gmail account (for practical sessions)'},
        {'value': 'chrome', 'label': 'Google Chrome (for practical sessions)'},
        {'value': 'slack', 'label': 'Slack'},
        {'value': 'youtube', 'label': 'Youtube (to watch, upload content)'},
        {'value': 'none', 'label': """I can't access any of the above"""},
    ])
    session.add_all([background_q1, background_q2, background_q3, background_q4])
    session.commit()
    
    poster = RegistrationSection(form.id, 'Poster', 'Only if you were selected to present a poster! If you were, please provide the following (Note: You can make changes to the project / title / authors submitted initially in your application.):', 3, None, None, None)
    session.add(poster)
    session.commit()

    poster_q1 = RegistrationQuestion(form.id, poster.id, 'Title', 'Title', 1, 'short-text', None, is_required=False)
    poster_q2 = RegistrationQuestion(form.id, poster.id, 'Authors', 'Authors', 2, 'short-text', None, is_required=False)
    poster_q3 = RegistrationQuestion(form.id, poster.id, 'Affiliations of authors (in the same order as authors)', 'Affiliation(s)', 3, 'short-text', None, is_required=False)
    poster_q4 = RegistrationQuestion(form.id, poster.id, 'Short abstract', 'Enter up to 100 words', 4, 'long-text', r'^\W*(\w+(\W+|$)){0,150}$', validation_text='Enter less than 100 words', is_required=False, description='Max 100 words')
    poster_q5 = RegistrationQuestion(form.id, poster.id, 'Teaser image', '', 5, 'file', None, is_required=False)
    poster_q6 = RegistrationQuestion(form.id, poster.id, 'Topic', 'Choose an option', 6, 'choice-with-other', None, is_required=False, options=[
        {'value': 'computeVision', 'label': 'Computer Vision'},
        {'value': 'robotics', 'label': 'Robotics'},
        {'value': 'reinforcementLearning', 'label': 'Reinforcement learning'},
        {'value': 'mlMedicalData', 'label': 'ML for medical data'},
        {'value': 'neuroscience', 'label': 'Neuroscience'},
        {'value': 'unsupervisedLearning', 'label': 'Unsupervised learning'},
        {'value': 'nlp', 'label': 'NLP'},
        {'value': 'deepLearning', 'label': 'Deep Learning'},
        {'value': 'optimization', 'label': 'Optimization'},
        {'value': 'theory', 'label': 'Theory'},
        {'value': 'applications', 'label': 'Applications'},    
    ])
    poster_q7 = RegistrationQuestion(form.id, poster.id, 'Youtube link to video presentation', 'Link', 7, 'short-text', None, is_required=False)
    poster_q8 = RegistrationQuestion(form.id, poster.id, 'Please check the following', '', 8, 'multi-checkbox', None, is_required=False, options=[
        {'value': 'less3Minutes', 'label': 'My video is no longer than 3 minutes.'},
        {'value': 'wontAlter', 'label': 'I will not alter the video after submission.'}
    ])
    session.add_all([
        poster_q1, poster_q2, poster_q3, poster_q4, poster_q5, poster_q6, poster_q7, poster_q8
    ])
    session.commit()
    
    other = RegistrationSection(form.id, 'Other', '', 4, None, None, None)
    session.add(other)
    session.commit()

    other_q1 = RegistrationQuestion(form.id, other.id, 'Would you be interested in sharing your CV with EEML2020 sponsors and partners for recruiting purposes?', '', 1, 'multi-choice', None, description='Please check the website https://www.eeml.eu for a complete list of sponsors and partners', options=[
        {'value': 'yes', 'label': 'Yes'},
        {'value': 'no', 'label': 'No or Does not apply (e.g. you represent a sponsor or you did not submit your CV)'}
    ])
    other_q2 = RegistrationQuestion(form.id, other.id, 'For the weekend days during the school period (July 4-5) we plan to organise relaxing/socialising activities. Please indicate below if you would be interested to participate in such sessions and which sessions or suggest ideas for different sessions.', '', 2, 'multi-checkbox-with-other', None, is_required=True, options=[
        {'value': 'notInterested', 'label': 'Not interested'},
        {'value': 'chess', 'label': 'Chess'},
        {'value': 'go', 'label': 'Go'},
        {'value': 'videoGames', 'label': 'Video games'},
        {'value': 'yoga', 'label': 'Yoga'},
    ])
    session.add_all([other_q1, other_q2])
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    event = session.query(Event).filter_by(key='eeml2020').first()
    form = session.query(RegistrationForm).filter_by(event_id=event.id).first()
    if form:
        op.execute("""DELETE FROM registration_question WHERE registration_form_id={}""".format(form.id))
        op.execute("""DELETE FROM registration_section WHERE registration_form_id={}""".format(form.id))
        op.execute("""DELETE FROM registration_form WHERE id={}""".format(form.id))
        session.commit()
