"""Add EEML application form

Revision ID: 87213d612eaf
Revises: b2d1fc607635
Create Date: 2020-02-02 22:19:25.912046

"""

# revision identifiers, used by Alembic.
revision = '87213d612eaf'
down_revision = 'b2d1fc607635'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime

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

    def __init__(self, name, system_name, small_logo, large_logo, domain, url, email_from, system_url):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.domain = domain
        self.system_name = system_name
        self.url = url
        self.email_from = email_from
        self.system_url = system_url

class Country(Base):
    __tablename__ = "country"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, name):
        self.name = name

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
                 registration_close
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

class ApplicationForm(Base):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)    

    def __init__(self, event_id, is_open, deadline):
        self.event_id = event_id
        self.is_open = is_open
        self.deadline = deadline


class Section(Base):
    __tablename__ = 'section'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer(), nullable=False)

    def __init__(self, application_form_id, name, description, order):
        self.application_form_id = application_form_id
        self.name = name
        self.description = description
        self.order = order

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


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Reset auto-increment ids
    op.get_bind().execute("""SELECT setval('event_id_seq', (SELECT max(id) FROM event));""")
    op.get_bind().execute("""SELECT setval('application_form_id_seq', (SELECT max(id) FROM application_form));""")
    op.get_bind().execute("""SELECT setval('section_id_seq', (SELECT max(id) FROM section));""")
    op.get_bind().execute("""SELECT setval('question_id_seq', (SELECT max(id) FROM question));""")

    # Add event
    eeml2020 = Event('EEML 2020', 'Eastern European Machine Learning Summer School 2020, 6-11 July 2020, Krakow, Poland',
        datetime.date(2020, 7, 6), datetime.date(2020, 7, 11), 'eeml2020', 2, 'contact@eeml.eu',
        'http://eeml.eu', datetime.date(2020, 2, 2), datetime.date(2020, 3, 20), datetime.date(2020, 3, 20), 
        datetime.date(2020, 4, 20), datetime.date(2020, 4, 20), datetime.date(2020, 5, 20), datetime.date(2020, 5, 20),
        datetime.date(2020, 6, 20), datetime.date(2020, 6, 20), datetime.date(2020, 6, 30))

    session.add(eeml2020)
    session.commit()

    app_form = ApplicationForm(eeml2020.id, True, datetime.date(2020, 3, 20))
    session.add(app_form)
    session.commit()

    main_section = Section(app_form.id, 'EEML 2020 Application Form', """
This is the official application form to apply for participation in EEML 2020, 6-11 July, Krakow, Poland. 

Do not forget to press Submit once you fill in the application form. It is possible (and recommended!) to submit partially completed forms early on to get familiar with the form, and come back at a later date before the application deadline (20 March 2020, 23:59 Eastern European Time) to edit/complete your responses.
    """, 1)
    session.add(main_section)
    session.commit()

    personal_info = Section(app_form.id, 'Personal Information', '', 2)
    session.add(personal_info)
    session.commit()

    personal_q1 = Question(app_form.id, personal_info.id, 'I Am:', 'Select an Option...', 1, 'multi-choice', None, 
            options=[
                {'label': 'An undergraduate student', 'value': 'undergrad'},
                {'label': 'A masters student', 'value': 'masters'},
                {'label': 'A PhD student', 'value': 'phd'},
                {'label': 'A Post-doc', 'value': 'postdoc'},
                {'label': 'Faculty', 'value': 'faculty'},
                {'label': 'Industry', 'value': 'industry'},
                {'label': 'Other (free-lancer etc)', 'value': 'other'}
            ])
    personal_q2 = Question(app_form.id, personal_info.id, 'Other', 'Other', 2, 'short-text', None, None, description='If you answered "Other", please specify', is_required=False)
    personal_q3 = Question(app_form.id, personal_info.id, 'Affiliation', 'Affiliation', 3, 'short-text', None, None, is_required=False)
    personal_q4 = Question(app_form.id, personal_info.id, 'Country', 'Select a Country...', 4, 'multi-choice', None, None, options=get_country_list(session))
    personal_q5 = Question(app_form.id, personal_info.id, 'Institution or Company', 'Institution or Company', 5, 'short-text', None, None, is_required=False, description='(if applicable)')
    personal_q6 = Question(app_form.id, personal_info.id, 'Research Group / Laboratory', 'Research Group / Laboratory', 6, 'short-text', None, None, is_required=False, description='(if applicable)')
    personal_q7 = Question(app_form.id, personal_info.id, 'Supervisor', 'Supervisor', 7, 'short-text', None, None, is_required=False, description='(if applicable)')
    personal_q8 = Question(app_form.id, personal_info.id, 'Previous attendance', 'Select an option...', 8, 'multi-choice', None, None, 
        options=[
            {'label': 'Yes', 'value': 'yes'},
            {'label': 'No', 'value': 'no'}
        ],
        description='Have you attended the previous edition of this school - TMLSS2018 or EEML2019?')
    session.add_all([personal_q1, personal_q2, personal_q3, personal_q4, personal_q5, personal_q6, personal_q7, personal_q8])

    research_interests = Section(app_form.id, 'Research Interests', '', 3)
    session.add(research_interests)
    session.commit()

    research_q1 = Question(app_form.id, research_interests.id, 'Research Interests', 'Enter 500 - 2000 characters', 1, 'long-text', 
        validation_regex='^.{500,2000}$', validation_text='You must enter between 500 and 2000 characters', 
        description='Describe your research interests, your projects related to ML, and your motivation for attending the summer school')
    research_q2 = Question(app_form.id, research_interests.id, 'Extended abstract type', 'Select an option...', 2, 'multi-choice', None, None, 
        options=[
            {'label': 'Research', 'value': 'research'},
            {'label': 'Reproduction', 'value': 'reproduction'},
            {'label': 'Review', 'value': 'review'}
        ], 
        description='Check https://www.eeml.eu/application for clarification',
        is_required=False)
    research_q3 = Question(app_form.id, research_interests.id, 'Extended abstract', 'Upload your extended abstract (pdf, max size 10MB)', 3, 'file', None, is_required=False)
    research_q4 = Question(app_form.id, research_interests.id, 'CV', 'Upload your CV (pdf, max size 10MB)', 4, 'file', None, is_required=True)

    session.add_all([research_q1, research_q2, research_q3, research_q4])

    diversity = Section(app_form.id, 'Diversity', '', 4)
    session.add(diversity)
    session.commit()

    diversity_q1 = Question(app_form.id, diversity.id, 'Gender Identity', 'Select an option...', 1, 'multi-choice', None,
        options=[
            {'label': 'Female', 'value': 'female'},
            {'label': 'Male', 'value': 'male'},
            {'label': 'Prefer not to say', 'value': 'prefer-not-to-say'}
        ])

    diversity_q2 = Question(app_form.id, diversity.id, 'Ethnicity', 'Ethnicity', 2, 'short-text', None, is_required=False, description='Leave blank if you prefer not to answer')
    diversity_q3 = Question(app_form.id, diversity.id, 'Nationality', 'Nationality', 3, 'short-text', None, is_required=False, description='Leave blank if you prefer not to answer')
    session.add_all([diversity_q1, diversity_q2, diversity_q3])

    financial_support = Section(app_form.id, 'Financial support for attending the school', """
The financial support will vary on a case-by-case basis and will cover fully or partially the costs of attending the school (registration, accommodation, travel). 

Please provide any information that you consider relevant to support your application (max 500 characters). If you need help covering travelling, please provide also an estimated travel cost (in EUR).

Note that financial support is offered on financial considerations, not on merit. This information will be hidden for reviewers, so it will not influence the selection decision.
""", 5)
    session.add(financial_support)
    session.commit()
    
    financial_q1 = Question(app_form.id, financial_support.id, 'Motivation', 'Enter up to 500 characters', 1, 'long-text', 
        validation_regex='^.{0,500}$', validation_text='Maximum 500 characters', 
        is_required=False, description='Max 500 characters')
    session.add(financial_q1)
    session.commit()

def get_country_list(session):
    countries = session.query(Country).all()
    country_list = []
    for country in countries:
        country_list.append({
            'label': country.name,
            'value': country.name
        })
    return country_list

def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='eeml2020').first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    session.query(Question).filter_by(application_form_id=app_form.id).delete()
    session.query(Section).filter_by(application_form_id=app_form.id).delete()

    session.query(ApplicationForm).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key='eeml2020').delete()

    session.commit()

    op.get_bind().execute("""SELECT setval('event_id_seq', (SELECT max(id) FROM event));""")
    op.get_bind().execute("""SELECT setval('application_form_id_seq', (SELECT max(id) FROM application_form));""")
    op.get_bind().execute("""SELECT setval('section_id_seq', (SELECT max(id) FROM section));""")
    op.get_bind().execute("""SELECT setval('question_id_seq', (SELECT max(id) FROM question));""")


