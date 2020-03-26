"""Add Deep Learning Indaba Application Form

Revision ID: 1c3fda18bad6
Revises: c3c5ef958ca1
Create Date: 2020-03-26 14:39:36.628724

"""

# revision identifiers, used by Alembic.
revision = '1c3fda18bad6'
down_revision = 'c3c5ef958ca1'


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
    event_type = db.Column(db.String(),nullable = False)

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
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    nominations = db.Column(db.Boolean(), nullable=False)
    

    def __init__(self, event_id, nominations):
        self.event_id = event_id
        self.nominations = nominations

class Section(Base):
    __tablename__ = 'section'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

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
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)
    
    def __init__(self, application_form_id, section_id, questionType, headline, placeholder, description = None, validation_regex, is_required = True, options = None, order):
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

def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Reset auto-increment ids
    op.get_bind().execute("""SELECT setval('event_id_seq', (SELECT max(id) FROM event));""")
    op.get_bind().execute("""SELECT setval('application_form_id_seq', (SELECT max(id) FROM application_form));""")
    op.get_bind().execute("""SELECT setval('section_id_seq', (SELECT max(id) FROM section));""")
    op.get_bind().execute("""SELECT setval('question_id_seq', (SELECT max(id) FROM question));""")

    #Add event
    DeepLearningIndaba2020 = Event('Deep Learning Indaba 2020','The Deep Learning Indaba 2020, Tunis, Tunisia',
                             datetime.date(2020, 8, 23),datetime.date(2020, 8, 28), 'indaba2020',1,'baobab@deeplearningindaba.com',
                             'http://www.deeplearningindaba.com/',datetime.date(2020, 3, 1),datetime.date(2020, 4, 17),
                             datetime.date(2020, 4, 25), datetime.date(2020, 5, 15), datetime.date(2020, 5, 15),
                             datetime.date(2020, 6, 1),datetime.date(2020, 6, 1),datetime.date(2020, 7, 31),
                             datetime.date(2020, 6, 1),datetime.date(2020, 7, 31),'EVENT')

    session.add(DeepLearningIndaba2020)
    session.commit()

    app_form = ApplicationForm(DeepLearningIndaba2020.id,False)
    session.add(app_form)
    session.commit()
    
    #Add Section
    main_section = Section(app_form.id, 'Deep Learning Indaba 2020 Application Form', 'This is the official application form to apply for participation in the Deep Learning Indaba to be held 23-28 August 2020 in Tunis, Tunisia.', 1)
    session.add(main_section)
    session.commit()

    main_q1 = Question(app_form.id, main_section.id, 'multi-choice', 'Application Category', 'Category',description = 'Please select the option that best describes you',None,
              options = [
                {'label': 'An undergraduate student', 'value': 'undergrad'},
                {'label': 'A masters student', 'value': 'masters'},
                {'label': 'A PhD student', 'value': 'phd'},
                {'label': 'A Post-doc', 'value': 'postdoc'},
                {'label': 'Academic Faculty', 'value': 'faculty'},
                {'label': 'Industry Professional', 'value': 'industry'},
                {'label': 'Student at a coding academy', 'value': 'student-coding-academy'},
                {'label': 'Unemployed', 'value': 'unemployed'}
              ], 1)
    session.add(main_q1)

    demographics = Section(app_form.id, 'Demographics', '', 2)
    session.add(demographics)
    session.commit()


    demographics_q1 = Question(app_form.id, demographics.id, 'multi-choice', 'Country of nationality', 'Country of nationality', None, options = get_country_list(session), 1)
    demographics_q2 = Question(app_form.id, demographics.id, 'multi-choice', 'Country of residence', 'Country of residence', None, options=get_country_list(session), 2)
    demographics_q3 = Question(app_form.id, demographics.id, 'multi-choice', 'Gender', 'Gender', None,
                      options = [
                         {'label': 'Male', 'value': 'male'},
                         {'label': 'Female', 'value': 'female'},
                         {'label': 'Transgender', 'value': 'transgender'},
                         {'label': 'Gender variant/non-conforming', 'value': 'gender-variant/non-conforming'},
                         {'label': 'Prefer not to say', 'value': 'prefer-not-to-say'}
                     ], 3)
    demographics_q4 = Question(app_form.id, demographics.id, 'multi-choice', 'Disabilities', 'Disabilities', description = 'We collect this information to ensure that we provide suitable facilities at our venue.', None,
                      options = [
                         {"label": "No disabilities", "value": "none"},
                         {"label": "Sight disability", "value": "sight"},
                         {"label": "Hearing disability", "value": "hearing"},
                         {"label": "Communication disability", "value": "communication"},
                         {"label": "Physical disability(e.g. difficulty in walking)", "value": "physical"},
                         {"label": "Mental disability(e.g. difficulty in remembering or concentrating)", "value": "mental"},
                         {"label": "Difficulty in self-care", "value": "self-care"},
                         {"label": "Other", "value": "other"}
                      ], 4)
    demographics_q5 = Question(app_form.id, demographics.id, 'short-text', 'Affiliation', 'Affiliation', description = 'The university / institution / company you are based at', None, 5)
    demographics_q6 = Question(app_form.id, demographics.id, 'short-text', 'Department', 'Department', description = 'The department or field of study you fall under at your affiliation', None, 6)
    
    session.add_all([demographics_q1, demographics_q2, demographics_q3, demographics_q4, demographics_q5, demographics_q6])

    about_you = Section(app_form.id, 'Tell Us a Bit About You', """
                         Please use this section to tell us a bit more about yourself and your intentions as a future Deep Learning Indaba ambassador
                         Take your time to fill in this section as it has the highest impact on whether or not you will be offered a place at the Indaba!""", 3)
    session.add(about_you)
    session.commit()

    about_you_q1 = Question(app_form.id, about_you.id, 'long-text', 'Why is attending the Deep Learning Indaba 2020 important to you?', 'Enter 100 to 200 words', description = 'Enter 100 to 200 words', validation_regex = '^\s*(\S+(\s+|$)){100,200}$', 1)
   
    about_you_q2 = Question(app_form.id, about_you.id, 'long-text', 'How will you share what you have learned after the Indaba?', 'Enter 50 to 150 words', description = 'Enter 50 to 150 words', validation_regex = '^\s*(\S+(\s+|$)){50,150}$', 2)
    about_you_q2.depends_on_question_id = main_q1.id
    about_you_q2.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed']

    about_you_q3 = Question(app_form.id, about_you.id, 'long-text', 'How will you use your experience at the Deep Learning Indaba to impact your teaching, research, supervision, and/or institution?', 'Enter 50 to 150 words', description = 'Enter 50 to 150 words', validation_regex = '^\s*(\S+(\s+|$)){50,150}$', 3)
    about_you_q3.depends_on_question_id = main_q1.id
    about_you_q3.show_for_values = ['academic-faculty']
    
    about_you_q4 = Question(app_form.id, about_you.id, 'long-text', 'Share with us a favourite machine learning resource you use: a paper, blog post, algorithm, result, or finding. Tell us why.', 'Enter up to 80 words', description = 'Enter up to 80 words', 'remember to include *why*', validation_regex = '^\s*(\S+(\s+|$)){0,80}$', 4)
    about_you_q4.depends_on_question_id = main_q1.id
    about_you_q4.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed, academic-faculty']

    about_you_q5 = Question(app_form.id, about_you.id, 'long-text', 'Are you or have you been a tutor for any relevant course, or part of any machine learning or data science society or meetup? If yes, give details.', 'Enter up to 80 words', description = 'Enter up to 80 words', validation_regex = '^\s*(\S+(\s+|$)){0,80}$', 5)
    about_you_q5.depends_on_question_id = main_q1.id
    about_you_q5.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed']

    about_you_q6 = Question(app_form.id, about_you.id, 'long-text', 'Have you taught any Machine Learning courses at your institution or supervised any postgraduate students on Machine Learning projects?', 'Enter up to 80 words', description = 'Enter up to 80 words', validation_regex = '^\s*(\S+(\s+|$)){0,80}$', 6)
    about_you_q6.depends_on_question_id = main_q1.id
    about_you_q6.show_for_values = ['academic-faculty']

    about_you_q7 = Question(app_form.id, about_you.id, 'multi-choice', 'Are you currently actively involved in Machine Learning Research?', 'Choose an option', description = 'Choosing no will not count against you', None,
                   options = [
                      {'label': 'Yes', 'value': 'yes'},
                      {'label': 'No', 'value': 'no'}
                   ], 7)
    about_you_q8 = Question(app_form.id, about_you.id, 'long-text', 'Add a short abstract describing your current research', 'Enter 150 to 250 words', description = 'This can be completed research or research in progress. Remember to include a description of your methodology and any key results you have so far.', validation_regex = '^\s*(\S+(\s+|$)){150,250}$', 8)
    about_you_q8.depends_on_question_id = about_you_q7.id
    about_you_q8.show_for_values = ['yes']

    about_you_q9 = Question(app_form.id, about_you.id, 'multi-choice', 'Would you be interested in submitting an extended abstract or paper to the Indaba Symposium if you are selected to attend the Indaba?', 'Choose an option', description = "We won't hold you to this, it's just to gauge interest.", None, 9)
    about_you_q9.depends_on_question_id = about_you_q7.id
    about_you_q9.show_for_values = ['yes']

    about_you_q10 = Question(app_form.id, about_you.id, 'long-text', 'Have you worked on a project that uses machine learning? Give a short description.', 'Enter upto 150 words', validation_regex = '^\s*(\S+(\s+|$)){0,150}$', 10)
   
    about_you_q11 = Question(app_form.id, about_you.id, 'file', 'Upload CV', None, is_required = True, 11)
    about_you_q11.depends_on_question_id = main_q1.id
    about_you_q11.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed']

    about_you_q12 = Question(app_form.id, about_you.id, 'multi-choice', 'May we add your CV and email address to a database for sharing with our sponsors?', 'Choose an option', None,
                    options = [
                       {'label': 'Yes', 'value': 'yes'},
                       {'label': 'No', 'value': 'no'}
                    ], 12)
    about_you_q12.depends_on_question_id = main_q1.id
    about_you_q12.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed']

    session.add_all([about_you_q1, about_you_q2, about_you_q3, about_you_q4, about_you_q5, about_you_q6, about_you_q7, about_you_q8, about_you_q9, about_you_q10, about_you_q11, about_you_q12])

    travel_support = Section(app_form.id, 'Travel Support',  """ We may be able to sponsor the cost of travel and accommodation for some attendees. These travel awards are limited and highly competitive,
                               but are assessed independently of Indaba attendance: applying for a travel award neither enhances nor undermines your chances of being accepted.
                               To help as many people attend as possible, before applying for travel support, please check if your supervisor, department or university is able to support you in any way.
                               """, 4)
    travel_support.depends_on_question_id = main_q1.id
    travel_support.show_for_values = ['undergraduate, masters, phd, post-doc, student at a coding academy, unemployed, academic-faculty']
    session.add(travel_support)
    session.commit()

    travel_support_q1 = Question(app_form.id, travel_support.id, 'multi-choice', 'Would you like to be considered for a travel grant?', 'Choose an option', description = 'Travel awards will be used to cover the costs of return flights to the host city and/or accommodation in shared dorm rooms close to the venue.', None,
                        options = [
                           {'label': 'Travel', 'value': 'travel'},
                           {'label': 'Accommodation', 'value': 'accommodation'}
                           {'label': 'Travel and Accommodation', 'value': 'travel-and-accommodation'}
                           {'label': 'None', 'value': 'none'}
                        ], 1)
    travel_support_q2 = Question(app_form.id, travel_support.id, 'short-text', 'Please state your intended airport of departure.', 'Airport of Departure', description = 'Please note that we will only provide flights in the form of a return ticket to and from a single airport on the continent of Africa.', None, 2)
    travel_support_q2.depends_on_question_id = travel_support_q1.id
    travel_support_q2.show_for_values =['travel, travel-accommodation']

    travel_support_q3 = Question(app_form.id, travel_support.id, 'multi-choice', 'If you do not receive a travel award from us, will you still be able to attend?', 'Choose an option', None,
                        options = [
                           {'label': 'Yes', 'value': 'yes'},
                           {'label': 'No', 'value': 'no'}
                        ], 3)
    travel_support_q3.depends_on_question_id = travel_support_q1.id
    travel_support_q3.show_for_values =['travel', 'accommodation', 'travel-accommodation']

    travel_support_q4 = Question(app_form.id, travel_support.id, 'long-text', 'Would you like to be considered for a registration fee waiver? If so, please provide a motivation', 'Enter up to 80 words', description = 'Enter up to 80 words', None, is_required = False, 4)
    travel_support_q4.depends_on_question_id = main_q1.id
    travel_support_q4.show_for_values = ['academic-faculty']

    session.add_all([travel_support_q1, travel_support_q2, travel_support_q3, travel_support_q4])

    attendance = Section(app_form.id, 'Previous Attendance', 'Help us quantify our progress by giving us some info on your previous Indaba experiences.', 5)
    session.add(attendance)
    session.commit()
