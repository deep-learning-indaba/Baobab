"""empty message

Revision ID: 14d53fa0c9c8
Revises: ('405d106c8292', 'f4bc3108c330')
Create Date: 2020-03-10 12:29:05.217984

"""

# revision identifiers, used by Alembic.
revision = '14d53fa0c9c8'
down_revision = ('405d106c8292', 'f4bc3108c330')

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime
from enum import Enum

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
    # pass
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    kambuledoctoral2020 = Event('Thamsanqa Kambule Doctoral Dissertation Award 2020',
    'Thamsanqa Kambule Doctoral Dissertation Award 2020',
    datetime.date(2020, 8, 23),datetime.date(2020, 8, 28), 'kambuledoctoral2020',
    1,'baobab@deeplearningindaba.com','http://www.deeplearningindaba.com',
    datetime.date(2020,3,1), datetime.date(2020,4,17),datetime.date(2020,4,25),
    datetime.date(2020,5,15),datetime.date(2020,1,1),datetime.date(2020,1,1),
    datetime.date(2020,1,1), datetime.date(2020,1,1),datetime.date(2020,1,1),
    datetime.date(2020,1,1), EventType.AWARD)

    session.add(kambuledoctoral2020)
    session.commit()

    event_id = kambuledoctoral2020.id

    application_form = ApplicationForm(event_id, True, True)
    session.add(application_form)
    session.commit()

    app_form_id = application_form.id

    main_section = Section(app_form_id,'Thamsanqa Kambule Doctoral Dissertation Award 2020',"""
    This is the official application form for the Thamsanqa Kambule Doctoral Dissertation Award 2020, an award to encourage and recognise excellence in research and writing by Doctoral candidates at African universities, in any area of computational and statistical science. This award will be made at the Deep Learning Indaba at Tunis, Tunisia, in August 2020. 

This application will require:
- Personal details about the nominee,
- Details about the dissertation, including a PDF of the dissertation itself, its abstract and core contributions,
- 1 supporting letter from a person other than the nominator (submitted separately through Baobab)

For eligibility criteria for the Kambule Doctoral Award, please see www.deeplearningindaba.com/awards

For any queries, please email awards@deeplearningindaba.com.
    """,1)

    session.add(main_section)
    session.commit()

    q1_nomination_capacity = Question(
        application_form_id=app_form_id,
        section_id=main_section.id,
        headline='Nomination Capacity',
        placeholder='',
        order=1,
        questionType='multi-choice',
        validation_regex=1,
        is_required=True,
        options=[
            {'label':'Self-nomination', 'value':'self'},
            {'label':'Nomination on behalf of a candidate','value':'other'}
        ]
    )
    session.add(q1_nomination_capacity)
    session.commit()

    nominator_information = Section(app_form_id, 'Nominator Information', """
Details of the person nominating the doctoral candidate.
        """,2)
    nominator_information.depends_on_question_id = q1_nomination_capacity.id
    nominator_information.show_for_values = ['other']
    session.add(nominator_information)
    session.commit()

    nominator_q1 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline='University',
        placeholder='University',
        order=1,
        questionType='short-text',
        validation_regex=1,
        is_required=True,
        description='The university that you (the nominator) are based at.'
    )
    nominator_q2 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline='Department',
        placeholder='Department',
        order=2,
        questionType='short-text',
        validation_regex=1,
        is_required=True,
        description='The department that you (the nominator) are based at.'
    )
    nominator_q3 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline='Describe your relationship to the doctoral candidate',
        placeholder='',
        order=3,
        questionType='long-text',
        validation_regex=1,
        is_required=True
    )
    session.add_all([nominator_q1,nominator_q2,nominator_q3])
    session.commit()

    candidate_information = Section(app_form_id, 'Doctoral Candidate Information', 'Details of the nominated doctoral candidate to be considered for the award.',3)
    session.add(candidate_information)
    session.commit()


    candidate_q1 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Title',
        placeholder='Title',
        order=1,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    candidate_q1.depends_on_question_id=q1_nomination_capacity.id
    candidate_q1.show_for_values=['other']

    candidate_q2 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Firstname',
        placeholder='Firstname',
        order=2,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    candidate_q2.depends_on_question_id=q1_nomination_capacity.id
    candidate_q2.show_for_values=['other']
    
    candidate_q3 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Lastname',
        placeholder='Lastname',
        order=3,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    candidate_q3.depends_on_question_id=q1_nomination_capacity.id
    candidate_q3.show_for_values=['other']
    
    candidate_q4 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Email Address',
        placeholder='Email Address',
        order=4,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    candidate_q4.depends_on_question_id=q1_nomination_capacity.id
    candidate_q4.show_for_values=['other']

    candidate_q5 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='University',
        placeholder='University',
        order=5,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    candidate_q6 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Country of Residence',
        placeholder='Choose an option',
        order=6,
        questionType='multi-choice',
        validation_regex=1,
        is_required=True,
        options=get_country_list(session)
    )
    candidate_q7 = Question(
        application_form_id=app_form_id,
        section_id=candidate_information.id,
        headline='Nationality',
        placeholder='Choose an option',
        order=7,
        questionType='multi-choice',
        validation_regex=1,
        is_required=True,
        options=get_country_list(session)
    )
    session.add_all([candidate_q1, candidate_q2,candidate_q3,candidate_q4,candidate_q5,candidate_q6,candidate_q7])
    session.commit()

    dissertation_information = Section(app_form_id, 'Doctoral dissertation information', 'Details of the Doctoral dissertation of the nominated candidate.', 4)
    session.add(dissertation_information)
    session.commit()

    dissertation_q1 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='Title',
        placeholder='Title',
        order=1,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    dissertation_q2 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='Abstract',
        placeholder='Enter up to 800 words',
        order=2,
        questionType='long-text',
        validation_regex='^\s*(\S+(\s+|$)){0,800}$',
        is_required=True,
        description='Abstract of dissertation (<= 800 words)'
    )
    dissertation_q3 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline="What are the dissertation's primary contributions to its field of research?",
        placeholder='Enter 400-500 words',
        order=3,
        questionType='long-text',
        validation_regex='^\s*(\S+(\s+|$)){400,500}$',
        is_required=True,
        description='Succinctly describe the novel contributions of this work (400-500 words)'
    )
    dissertation_q4 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='Name of Doctoral academic supervisor',
        placeholder='Name of Supervisor',
        order=4,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    dissertation_q5 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='E-mail address of Doctoral academic supervisor',
        placeholder='Supervisor Email Address',
        order=5,
        questionType='short-text',
        validation_regex=1,
        is_required=True
    )
    dissertation_q6 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='Date of submission/defence of dissertation',
        placeholder='Date of submission',
        order=6,
        questionType='date',
        validation_regex=1,
        is_required=True
    )
    dissertation_q7 = Question(
        application_form_id=app_form_id,
        section_id=dissertation_information.id,
        headline='Name(s) of examiner/s',
        placeholder='Name(s) of examiner/s',
        order=7,
        questionType='short-text',
        validation_regex=1,
        is_required=False
    )

    session.add_all([dissertation_q1,dissertation_q2,dissertation_q3,dissertation_q4,dissertation_q5,dissertation_q6,dissertation_q7])
    session.commit()

    supporting_information = Section(app_form_id, 'Supporting Documentation','',5)
    session.add(supporting_information)
    session.commit()

    supporting_q1 = Question(
        application_form_id=app_form_id,
        section_id=supporting_information.id,
        headline='Dissertation',
        placeholder='Dissertation',
        order=1,
        questionType='file',
        validation_regex=1,
        is_required=True,
        description='We require the electronic submission of the dissertation. We recommended that dissertations be written in English (the Awards Committee may require an English translation for full consideration of theses written in other languages).'
    )
    supporting_q2 = Question(
        application_form_id=app_form_id,
        section_id=supporting_information.id,
        headline="Examiners' reports",
        placeholder="Examiners' reports",
        order=2,
        questionType='file',
        validation_regex=1,
        is_required=True,
        description="We require the examiners' report to be submitted. If this is not available, please contact awards@deeplearningindaba.com."
    )
    supporting_q3 = Question(
        application_form_id=app_form_id,
        section_id=supporting_information.id,
        headline='Supporting Letter',
        placeholder='',
        order=3,
        questionType='reference',
        validation_regex=1,
        is_required=True,
        description="""
        A supporting letter that describes the main theoretical, methodological, and/or applied contributions of the thesis should be submitted by an academic who is in a position to comment on the merits of the work and the candidate, e.g., Doctoral supervisor, thesis examiner, academic mentor, collaborators, etc. The letter should be written by someone other than the person who is nominating the candidate.

        Supporting letters should be 600 words at most, written in English, and submitted electronically in PDF format by the closing date, using Baobab
        """,
        options=[
            {"min_num_referrals": 1},
            {"max_num_referrals": 1}
        ]
    )
    supporting_q4 = Question(
        application_form_id=app_form_id,
        section_id=supporting_information.id,
        headline='Additional Comments',
        placeholder='',
        order=4,
        questionType='long-text',
        validation_regex=1,
        is_required=False,
        description='Use this space to provide any additional details which you feel are relevant to this nomination and have not been captured by this form.'
    )

    session.add_all([supporting_q1,supporting_q2,supporting_q3,supporting_q4])
    session.commit()


def downgrade():
    # pass
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='kambuledoctoral2020').first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    session.query(Question).filter_by(application_form_id=app_form.id).delete()
    session.query(Section).filter_by(application_form_id=app_form.id).delete()

    session.query(ApplicationForm).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key='kambuledoctoral2020').delete()

    session.commit()