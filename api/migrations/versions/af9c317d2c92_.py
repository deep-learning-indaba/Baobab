"""empty message

Revision ID: af9c317d2c92
Revises: 245d12695c69
Create Date: 2020-03-12 08:49:36.009020

"""

# revision identifiers, used by Alembic.
revision = "af9c317d2c92"
down_revision = "245d12695c69"

import datetime
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()


class Organisation(Base):

    __tablename__ = "organisation"
    __table_args__ = {"extend_existing": True}

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

    def __init__(
        self,
        name,
        system_name,
        small_logo,
        large_logo,
        domain,
        url,
        email_from,
        system_url,
        privacy_policy,
    ):
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
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, name):
        self.name = name


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
        self.event_roles = []
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

    def __init__(
        self,
        application_form_id,
        section_id,
        headline,
        placeholder,
        order,
        questionType,
        validation_regex,
        validation_text=None,
        is_required=True,
        description=None,
        options=None,
    ):
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
    __tablename__ = "section"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(
        db.Integer(), db.ForeignKey("question.id", use_alter=True), nullable=True
    )
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
        country_list.append({"label": country.name, "value": country.name})
    return country_list


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # pass
    # ### end Alembic commands ###

    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    maathaiimpact2020 = Event(
        "Wangari Maathai Impact Award 2020",
        "Wangari Maathai Impact Award 2020",
        datetime.date(2020, 8, 23),
        datetime.date(2020, 8, 28),
        "maathai2020",
        1,
        "baobab@deeplearningindaba.com",
        "http://www.deeplearningindaba.com",
        datetime.date(2020, 3, 1),
        datetime.date(2020, 4, 17),
        datetime.date(2020, 4, 25),
        datetime.date(2020, 5, 15),
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 1),
        datetime.date(2020, 1, 1),
        EventType.AWARD,
    )
    session.add(maathaiimpact2020)
    session.commit()

    event_id = maathaiimpact2020.id

    application_form = ApplicationForm(event_id, True, True)
    session.add(application_form)
    session.commit()

    app_form_id = application_form.id

    main_section = Section(
        app_form_id,
        "Wangari Maathai Impact Award 2020",
        """
This is the official application form for the Wangari Maathai Impact Award 2020, an award to encourage and recognise work by African innovators that shows impactful application of machine learning and artificial intelligence. This award will be made at the Deep Learning Indaba in Tunis, Tunisia in August 2020.

This application will require:
- Personal details about the nominee,
- Details about the impactful work, including why it is impactful, who it impacts and why is it innovative,
- Details of 2 people other than the nominator to provide supporting letters for the nominee

For eligibility criteria for the Maathai Award, please see www.deeplearningindaba.com/maathai-2020

For any queries, please email awards@deeplearningindaba.com.
    """,
        1,
    )
    session.add(main_section)
    session.commit()

    q1_nomination_capacity = Question(
        application_form_id=app_form_id,
        section_id=main_section.id,
        headline="Nominating Capacity",
        placeholder="",
        order=1,
        questionType="multi-choice",
        validation_regex=None,
        is_required=True,
        options=[
            {"label": "Self-nomination", "value": "self"},
            {"label": "Nomination on behalf of a candidate", "value": "other"},
        ],
    )
    session.add(q1_nomination_capacity)
    session.commit()

    nominator_information = Section(
        app_form_id,
        "Nominator Information",
        """
    Details of the person nominating an individual, team or organisation
    """,
        2,
    )
    nominator_information.depends_on_question_id = q1_nomination_capacity.id
    nominator_information.show_for_values = ["other"]
    session.add(nominator_information)
    session.commit()

    nominator_q1 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline="Affiliation",
        placeholder="Affiliation",
        order=1,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
        description="(university, institute, company, etc)",
    )
    nominator_q2 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline="Department",
        placeholder="Department",
        order=2,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
    )
    nominator_q3 = Question(
        application_form_id=app_form_id,
        section_id=nominator_information.id,
        headline="Describe your relationship to the nominee",
        placeholder="",
        order=3,
        questionType="long-text",
        validation_regex=None,
        is_required=True,
    )
    session.add_all([nominator_q1, nominator_q2, nominator_q3])
    session.commit()

    nominee_information = Section(
        app_form_id,
        "Nominee Information",
        """
    Details of the nominated individual, team or organisation to be considered for the award. For any teams/organisations, details of the principal contact should be entered below.
    """,
        3,
    )
    session.add(nominee_information)
    session.commit()

    nominee_q1 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Title",
        placeholder="Title",
        order=1,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
    )
    nominee_q1.depends_on_question_id = q1_nomination_capacity.id
    nominee_q1.show_for_values = ["other"]
    nominee_q2 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Firstname",
        placeholder="Firstname",
        order=2,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
    )
    nominee_q2.depends_on_question_id = q1_nomination_capacity.id
    nominee_q2.show_for_values = ["other"]
    nominee_q3 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Lastname",
        placeholder="Lastname",
        order=3,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
    )
    nominee_q3.depends_on_question_id = q1_nomination_capacity.id
    nominee_q3.show_for_values = ["other"]
    nominee_q4 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Email Address",
        placeholder="Email Address",
        order=4,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
    )
    nominee_q4.depends_on_question_id = q1_nomination_capacity.id
    nominee_q4.show_for_values = ["other"]
    nominee_q5 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Affiliation",
        placeholder="Affiliation",
        order=5,
        questionType="short-text",
        validation_regex=None,
        is_required=True,
        description="(university, institute, company, etc)",
    )
    nominee_q6 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="If a team/organisation, names of team members",
        placeholder="Names of team members",
        order=6,
        questionType="short-text",
        validation_regex=None,
        is_required=False,
    )
    nominee_q7 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Country of Residence",
        placeholder="Choose an option",
        order=7,
        questionType="multi-choice",
        validation_regex=None,
        is_required=True,
        options=get_country_list(session),
    )
    nominee_q8 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Nationality",
        placeholder="Choose an option",
        order=8,
        questionType="multi-choice",
        validation_regex=None,
        is_required=True,
        options=get_country_list(session),
    )
    nominee_q9 = Question(
        application_form_id=app_form_id,
        section_id=nominee_information.id,
        headline="Website (or other online presence)",
        placeholder="Enter a URL",
        order=9,
        questionType="short-text",
        validation_regex=None,
        is_required=False,
    )
    session.add_all(
        [
            nominee_q1,
            nominee_q2,
            nominee_q3,
            nominee_q4,
            nominee_q5,
            nominee_q6,
            nominee_q7,
            nominee_q8,
            nominee_q9,
        ]
    )
    session.commit()

    impact_info = Section(app_form_id, "Information about impactful work", "", 3)
    session.add(impact_info)
    session.commit()

    impact_q1 = Question(
        application_form_id=app_form_id,
        section_id=impact_info.id,
        headline="What impactful work or project is the team/individual doing?",
        placeholder="Enter 300-500 words",
        order=1,
        questionType="long-text",
        validation_regex=r"^\s*(\S+(\s+|$)){300,500}$",
        is_required=True,
        description="Describe the work/project. In particular, describe the role of machine learning and/or artificial intelligence (300-500 words)",
    )
    impact_q2 = Question(
        application_form_id=app_form_id,
        section_id=impact_info.id,
        headline="Who does this work impact? Say how.",
        placeholder="Enter 150-200 words",
        order=2,
        questionType="long-text",
        validation_regex=r"^\s*(\S+(\s+|$)){150,200}$",
        is_required=True,
        description="Describe who is benefitting from this work (location, how many people etc). Describe how this work is positively affecting this group (150-200 words)",
    )
    impact_q3 = Question(
        application_form_id=app_form_id,
        section_id=impact_info.id,
        headline="Why is this work innovative?",
        placeholder="Enter 150-200 words",
        order=3,
        questionType="long-text",
        validation_regex=r"^\s*(\S+(\s+|$)){150,200}$",
        is_required=True,
        description="Describe the novel parts of the work, what difference it is making, or how it is moving Africa forwards (150-200 words)",
    )
    session.add_all([impact_q1, impact_q2, impact_q3])
    session.commit()

    supporting_docs = Section(
        app_form_id,
        "Supporting Documentation",
        """
    If this is a self-nomination, two supporting letters are required, otherwise one supporting letter is sufficient. The supporting letters should describe the nature of the impactful work, why it is considered to be impactful, and in what way the candidate strengthens African machine learning, and any other relevant information. Letter writers can be from anyone familiar with the impactful work.

    Supporting letters should be 600 words at most, written in English, and submitted electronically in PDF by the closing date through Baobab
    """,
        4,
    )
    session.add(supporting_docs)
    session.commit()

    supporting_docs_q1 = Question(
        application_form_id=app_form_id,
        section_id=supporting_docs.id,
        headline="Add the details of the 1 or 2 people who will provide supporting letters.",
        placeholder="",
        order=1,
        questionType="reference",
        validation_regex=None,
        is_required=True,
        description="Add at least two people if this is a self nomination and at least one if you are nominating someone else.",
        options={"min_num_referral": 1, "max_num_referral": 3},
    )
    supporting_docs_q2 = Question(
        application_form_id=app_form_id,
        section_id=supporting_docs.id,
        headline="Additional comments",
        placeholder="",
        order=2,
        questionType="long-text",
        validation_regex=None,
        is_required=False,
        description="Use this space to provide any additional details which you feel are relevant to this nomination and have not been captured by this form.",
    )
    session.add_all([supporting_docs_q1, supporting_docs_q2])
    session.commit()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # pass
    # ### end Alembic commands ###
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key="maathai2020").first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    nominator = session.query(Section).filter_by(name="Nominator Information").first()
    nominator.depends_on_question_id = None

    session.query(Question).filter_by(application_form_id=app_form.id).delete()
    session.query(Section).filter_by(application_form_id=app_form.id).delete()

    session.query(ApplicationForm).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key="maathai2020").delete()

    session.commit()
