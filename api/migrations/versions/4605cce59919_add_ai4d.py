"""Create AI4D Application Form

Revision ID: 4605cce59919
Revises: 2279e1fa2e49
Create Date: 2020-05-27 20:35:39.942895

"""

# revision identifiers, used by Alembic.
revision = "4605cce59919"
down_revision = "2279e1fa2e49"

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
    ):
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
        travel_grant,
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


class ApplicationForm(Base):
    __tablename__ = "application_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    nominations = db.Column(db.Boolean(), nullable=False)

    def __init__(self, event_id, is_open, nominations):
        self.event_id = event_id
        self.is_open = is_open
        self.nominations = nominations


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
    key = db.Column(db.String(255), nullable=True)

    def __init__(self, application_form_id, name, description, order):
        self.application_form_id = application_form_id
        self.name = name
        self.description = description
        self.order = order


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


def get_country_list(session):
    countries = session.query(Country).all()
    country_list = []
    for country in countries:
        country_list.append({"label": country.name, "value": country.name})
    return country_list


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Add event
    ai4d = Event(
        "AI4D Research Innovation",
        "AI4D-Africa Community-Based Research Innovation",
        datetime.date(2021, 1, 31),
        datetime.date(2021, 1, 31),
        "ai4d2020",
        1,
        "baobab@deeplearningindaba.com",
        "https://deeplearningindaba.com/2020/grand-challenge",
        datetime.date(2020, 5, 27),
        datetime.date(2020, 6, 20),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        datetime.date(2020, 12, 31),
        EventType.EVENT,
        False,
    )

    session.add(ai4d)
    session.commit()

    app_form = ApplicationForm(ai4d.id, True, False)
    session.add(app_form)
    session.commit()

    main_section = Section(
        app_form.id,
        "AI4D-Africa Community-Based Research Innovation: Call for Proposals",
        """
We are looking to strengthen AI research communities and the work they do during the Covid pandemic, by funding research projects across Africa that are collaborative at heart.

This Call for Proposals invites individuals, grassroots organizations, initiatives, academic, and civil society institutions to apply for funding for mini-projects. These could be new or existing projects at various stages, including projects that create and analyse new data sets around a research hypothesis, to later stage projects that require a "final push". New initiatives might also focus on a Research Grand Challenge, as set out below.

We are specifically looking to support research projects or segments of larger research endeavours:
- that are conducted in Africa;
- that have a strong machine learning or artificial intelligence component, across all disciplines of science;
- that could reach deliverable outcomes by the end of 2020.

Supported projects will have access to additional project-specific mentorship from the Deep Learning Indaba network.

APPLICATOIN DEADLINE: 19 June 2020

    """,
        1,
    )
    session.add(main_section)
    session.commit()

    q1 = Question(
        app_form.id,
        main_section.id,
        "Project Name",
        "Project Name",
        1,
        "short-text",
        None,
    )
    q2 = Question(
        app_form.id,
        main_section.id,
        "Affiliation of Project Lead",
        "Affiliation",
        2,
        "short-text",
        None,
    )
    q3 = Question(
        app_form.id,
        main_section.id,
        "Country of Project Lead",
        "Country",
        3,
        "multi-choice",
        None,
        options=get_country_list(session),
    )
    q4 = Question(
        app_form.id,
        main_section.id,
        "Preferred method of funding",
        "Method of funding",
        4,
        "multi-choice",
        None,
        options=[
            {
                "label": "(a) university/research institution/partner charity",
                "value": "partner",
            },
            {"label": "(b) through the project lead directly", "value": "project-lead"},
        ],
        description="""
There are two avenues to fund a project:
(a) through a university or research institution or local partner charity;
(b) or through the project lead directly.
In case (b), the project lead would be contracted as a consultant for Knowledge4All (K4A) until the project's completion. The project lead would receive the project funding directly as a personal research allowance, and be accountable to K4A for how the research allowance is used toward the project. We expect that income tax would be payable if the project is funded as a personal research allowance. The project lead would be personally responsible for declaring it in their yearly tax return. We don't want project leads to unexpectedly pay additional income tax on the research allowance after it is spent! Project leads are advised to include the income tax percentage and amount upfront in their budget.
    """,
    )
    q5 = Question(
        app_form.id,
        main_section.id,
        "Your Proposal",
        "Proposal",
        5,
        "file",
        None,
        description="""
    Please submit a PDF of at most 4 pages according to the following template:
1) Names of collaborators, with brief profiles of the team involved, giving relevant information as to demonstrate your ability to undertake and deliver on the proposed research;
2) Research hypothesis and expected outcomes;
3) A brief paragraph on the long-term vision for your work, if any;
4) A brief ethical review discussing any perceived risks or considerations in relation to the proposed work and its effect on people and society;
5) Timeline estimates to help us with progress assessment; 
6) Suggestions of what other support you would require from us to make your research work a success;
7) A preferred method of funding (details below);
8) A budget detailing the total amount requested and expenditure allocation (limit USD 8,000 per project). The budget may account for income tax on a personal research allowance, if option (b) below is pursued.
    """,
    )
    q6 = Question(
        app_form.id,
        main_section.id,
        "Mentorship",
        "Mentorship",
        6,
        "multi-choice",
        None,
        options=[{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}],
        description="""
    Would you appreciate project mentorship from the Deep Learning Indaba network?
    """,
    )

    session.add_all([q1, q2, q3, q4, q5, q6])
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key="ai4d2020").first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()
    session.query(Question).filter_by(application_form_id=app_form.id).delete()
    session.query(Section).filter_by(application_form_id=app_form.id).delete()

    session.query(ApplicationForm).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key="ai4d2020").delete()

    session.commit()
