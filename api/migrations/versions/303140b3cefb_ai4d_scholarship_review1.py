# -*- coding: utf-8 -*-

"""AI4D Scholarship Call Review Form

Revision ID: 303140b3cefb
Revises: 6b64b8037b7b
Create Date: 2020-12-05 21:02:18.508329

"""

# revision identifiers, used by Alembic.
revision = "303140b3cefb"
down_revision = "6b64b8037b7b"

import datetime
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import column_property

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
    CALL = "call"


class Event(Base):

    __tablename__ = "event"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
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
    travel_grant = db.Column(db.Boolean(), nullable=False)
    miniconf_url = db.Column(db.String(100), nullable=True)

    event_translations = db.relationship("EventTranslation", lazy="dynamic")

    def __init__(
        self,
        names,
        descriptions,
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
        miniconf_url=None,
    ):
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
        self.travel_grant = travel_grant
        self.miniconf_url = miniconf_url

        self.add_event_translations(names, descriptions)

    def add_event_translations(self, names, descriptions):
        for language in names:
            name = names[language]
            description = descriptions[language]
            event_translation = EventTranslation(name, description, language)
            self.event_translations.append(event_translation)


class EventTranslation(Base):

    __tablename__ = "event_translation"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(2))

    event = db.relationship("Event", foreign_keys=[event_id])

    def __init__(self, name, description, language):
        self.name = name
        self.description = description
        self.language = language


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


class Question(Base):
    __tablename__ = "question"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    section_id = db.Column(db.Integer(), db.ForeignKey("section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(
        db.Integer(), db.ForeignKey("question.id"), nullable=True
    )
    key = db.Column(db.String(255), nullable=True)

    question_translations = db.relationship("QuestionTranslation", lazy="dynamic")

    def __init__(
        self, application_form_id, section_id, order, questionType, is_required=True
    ):
        self.application_form_id = application_form_id
        self.section_id = section_id
        self.order = order
        self.type = questionType
        self.is_required = is_required

    def get_translation(self, language):
        question_translation = self.question_translations.filter_by(
            language=language
        ).first()
        return question_translation


class QuestionTranslation(Base):
    __tablename__ = "question_translation"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

    question = db.relationship("Question", foreign_keys=[question_id])

    def __init__(
        self,
        question_id,
        language,
        headline,
        description=None,
        placeholder=None,
        validation_regex=None,
        validation_text=None,
        options=None,
        show_for_values=None,
    ):
        self.question_id = question_id
        self.language = language
        self.headline = headline
        self.description = description
        self.placeholder = placeholder
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.options = options
        self.show_for_values = show_for_values


class Section(Base):
    __tablename__ = "section"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(
        db.Integer(), db.ForeignKey("question.id", use_alter=True), nullable=True
    )
    key = db.Column(db.String(255), nullable=True)

    application_form = db.relationship(
        "ApplicationForm", foreign_keys=[application_form_id]
    )
    section_translations = db.relationship("SectionTranslation", lazy="dynamic")
    questions = db.relationship(
        "Question", primaryjoin=id == Question.section_id, order_by="Question.order"
    )

    def __init__(
        self, application_form_id, order, depends_on_question_id=None, key=None
    ):
        self.application_form_id = application_form_id
        self.order = order
        self.depends_on_question_id = depends_on_question_id
        self.key = key

    def get_translation(self, language):
        section_translation = self.section_translations.filter_by(
            language=language
        ).first()
        return section_translation


class SectionTranslation(Base):
    __tablename__ = "section_translation"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey("section.id"), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=False)
    show_for_values = db.Column(db.JSON(), nullable=True)

    section = db.relationship("Section", foreign_keys=[section_id])

    def __init__(self, section_id, language, name, description, show_for_values=None):
        self.section_id = section_id
        self.language = language
        self.name = name
        self.description = description
        self.show_for_values = show_for_values


class ReviewForm(Base):
    __tablename__ = "review_form"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(
        db.Integer(), db.ForeignKey("application_form.id"), nullable=False
    )
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    application_form = db.relationship(
        "ApplicationForm", foreign_keys=[application_form_id]
    )
    review_questions = db.relationship("ReviewQuestion")

    def __init__(self, application_form_id, deadline):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline

    def close(self):
        self.is_open = False


class ReviewQuestion(Base):
    __tablename__ = "review_question"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=True)

    type = db.Column(db.String(), nullable=False)

    is_required = db.Column(db.Boolean(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    weight = db.Column(db.Float(), nullable=False)
    review_form = db.relationship("ReviewForm", foreign_keys=[review_form_id])
    question = db.relationship("Question", foreign_keys=[question_id])

    translations = db.relationship("ReviewQuestionTranslation", lazy="dynamic")

    def __init__(self, review_form_id, question_id, type, is_required, order, weight):
        self.review_form_id = review_form_id
        self.question_id = question_id
        self.type = type
        self.is_required = is_required
        self.order = order
        self.weight = weight

    def get_translation(self, language):
        translation = self.translations.filter_by(language=language).first()
        return translation


class ReviewQuestionTranslation(Base):
    __tablename__ = "review_question_translation"
    __table_args__ = {"extend_existing": True}
    __table_args__ = tuple(
        [
            db.UniqueConstraint(
                "review_question_id", "language", name="uq_review_question_id_language"
            )
        ]
    )

    id = db.Column(db.Integer(), primary_key=True)
    review_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=False
    )
    language = db.Column(db.String(2), nullable=False)

    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)

    def __init__(
        self,
        review_question_id,
        language,
        description=None,
        headline=None,
        placeholder=None,
        options=None,
        validation_regex=None,
        validation_text=None,
    ):
        self.review_question_id = review_question_id
        self.language = language
        self.description = description
        self.headline = headline
        self.placeholder = placeholder
        self.options = options
        self.validation_regex = validation_regex
        self.validation_text = validation_text


class ReviewConfiguration(Base):
    __tablename__ = "review_configuration"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=True
    )
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)


class ReviewScore(Base):
    __tablename__ = "review_score"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    review_response_id = db.Column(
        db.Integer(), db.ForeignKey("review_response.id"), nullable=False
    )
    review_question_id = db.Column(
        db.Integer(), db.ForeignKey("review_question.id"), nullable=False
    )
    value = db.Column(db.String(), nullable=False)

    def __init__(self, review_question_id, value):
        self.review_question_id = review_question_id
        self.value = value


class ReviewResponse(Base):
    __tablename__ = "review_response"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(
        db.Integer(), db.ForeignKey("review_form.id"), nullable=False
    )
    reviewer_user_id = db.Column(
        db.Integer(), db.ForeignKey("app_user.id"), nullable=False
    )
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)

    def __init__(self, review_form_id, reviewer_user_id, response_id, language):
        self.review_form_id = review_form_id
        self.reviewer_user_id = reviewer_user_id
        self.response_id = response_id
        self.language = language
        self.is_submitted = False

    def submit(self):
        self.is_submitted = True
        self.submitted_timestamp = datetime.now()


current_order = 1


def add_question(
    review_form_id,
    type,
    is_required,
    weight=0,
    question_id=None,
    descriptions=None,
    headlines=None,
    placeholders=None,
    options=None,
    validation_regexs=None,
    validation_texts=None,
):
    global current_order
    question = ReviewQuestion(
        review_form_id, question_id, type, is_required, current_order, weight
    )
    db.session.add(question)
    db.session.commit()
    en = ReviewQuestionTranslation(
        question.id,
        "en",
        None if descriptions is None else descriptions["en"],
        None if headlines is None else headlines["en"],
        None if placeholders is None else placeholders["en"],
        None if options is None else options["en"],
        None if validation_regexs is None else validation_regexs["en"],
        None if validation_texts is None else validation_texts["en"],
    )
    fr = ReviewQuestionTranslation(
        question.id,
        "fr",
        None if descriptions is None else descriptions["fr"],
        None if headlines is None else headlines["fr"],
        None if placeholders is None else placeholders["fr"],
        None if options is None else options["fr"],
        None if validation_regexs is None else validation_regexs["fr"],
        None if validation_texts is None else validation_texts["fr"],
    )
    db.session.add_all([en, fr])
    db.session.commit()

    current_order += 1

    return question, en, fr


def get_question(application_form_id, en_headline):
    en = (
        db.session.query(QuestionTranslation)
        .filter_by(language="en", headline=en_headline)
        .join(Question, QuestionTranslation.question_id == Question.id)
        .filter_by(application_form_id=application_form_id)
        .first()
    )
    fr = (
        db.session.query(QuestionTranslation)
        .filter_by(language="fr", question_id=en.question_id)
        .first()
    )
    return en.question, en, fr


def add_evaluation_question(form_id, headlines, descriptions, min_score, max_score):
    validation_regex = "^({})$".format(
        "|".join([str(i) for i in range(max_score, min_score - 1, -1)])
    )
    validation_text = {
        "en": "Enter a number between {} and {}".format(min_score, max_score),
        "fr": "Entrez un nombre entre {} et {}".format(min_score, max_score),
    }
    placeholders = {
        "en": "Enter a score between {} and {}".format(min_score, max_score),
        "fr": "Saisissez un score compris entre {} et {}".format(min_score, max_score),
    }
    return add_question(
        form_id,
        "short-text",
        True,
        1,
        headlines=headlines,
        descriptions=descriptions,
        validation_regexs={"en": validation_regex, "fr": validation_regex},
        validation_texts=validation_text,
        placeholders=placeholders,
    )


def add_comment_question(form_id, headlines, descriptions, is_required=False):
    return add_question(
        form_id,
        "long-text",
        is_required,
        weight=1,
        descriptions=descriptions,
        headlines=headlines,
    )


def add_information_question(
    form_id,
    application_form_id,
    en_headline,
    type="information",
    heading_override=False,
    description_override=None,
):
    question, en, fr = get_question(application_form_id, en_headline)

    headlines = {
        "en": None if heading_override else en.headline,
        "fr": None if heading_override else fr.headline,
    }
    descriptions = {
        "en": description_override["en"]
        if description_override is not None
        else en.description,
        "fr": description_override["fr"]
        if description_override is not None
        else fr.description,
    }

    if question.type == "information":
        return add_heading(form_id, headlines)

    return add_question(
        form_id,
        type,
        False,
        question_id=question.id,
        headlines=headlines,
        descriptions=descriptions,
    )


def add_heading(form_id, headlines):
    return add_question(form_id, "heading", False, headlines=headlines)


def add_divider(form_id, headlines, descriptions, sub_heading=False):
    return add_question(
        form_id,
        "sub-heading" if sub_heading else "section-divider",
        False,
        headlines=headlines,
        descriptions=descriptions,
    )


def upgrade():
    event = db.session.query(Event).filter_by(key="spm").first()
    application_form = (
        db.session.query(ApplicationForm).filter_by(event_id=event.id).first()
    )

    form = ReviewForm(application_form.id, datetime.datetime(2020, 12, 31))
    db.session.add(form)
    db.session.commit()
    review_config = ReviewConfiguration(
        review_form_id=form.id, num_reviews_required=3, num_optional_reviews=0
    )
    db.session.add(review_config)
    db.session.commit()

    # Set up application form responses
    divider1 = add_divider(
        form.id, {"en": "Application", "fr": "Application"}, descriptions=None
    )

    sections = (
        db.session.query(Section)
        .filter_by(application_form_id=application_form.id)
        .all()
    )
    for section in sections:
        en = section.get_translation("en")
        if (
            en.name == "Organisation and Lead Applicant Contact details"
            or en.name == "AI4D Call for Proposals: Scholarships program manager"
        ):
            continue
        add_divider(
            form.id,
            {"en": en.name, "fr": section.get_translation("fr").name},
            None,
            sub_heading=True,
        )
        for question in section.questions:
            translation = question.get_translation("en")
            if question.type == "multi-file":
                q_type = "multi-file"
            elif question.type == "file":
                q_type = "file"
            else:
                q_type = "information"
            add_information_question(
                form.id, application_form.id, translation.headline, type=q_type
            )

    # Add review questions
    add_divider(form.id, {"en": "Review", "fr": "Review"}, None)

    add_divider(
        form.id,
        {
            "en": "1. Organizational capacity and program fit of the host institution",
            "fr": "1. Organizational capacity and program fit of the host institution",
        },
        None,
        sub_heading=True,
    )

    add_evaluation_question(
        form.id,
        None,
        {
            "en": """1.1.a. To what extent does the organization and their proposal demonstrate strong fit with the AI4D programme outcomes and demonstrate sufficient organizational capacity to manage the call, such as: 
    -  A strong record of relevant experience in hosting scholarships in the African context; 
    -  Availability of, or ability to acquire, required resources and capacities; 
    -  A proposal for clear and appropriate coordination and governance of the partnership; 
    -  A clear articulation of how appropriate expertise will be acquired to evaluate proposals on AI, ML, or related disciplines and which contributes to the SDGs; 
    -  A demonstrated fit with the AI4D approach. 

References: Section I, Section II, and Section IV
 
**0 - Very poor**: does not meet criteria 
**5 - Poor**: meets some criteria for capacity and program fit 
**10 - Satisfactory**: meets most criteria though needs further elaboration 
**15 - Good**: meets all criteria for capacity and program fit 
**20 - Very Good**: meets and exceeds criteria for capacity and program fit 
""",
            "fr": """""",
        },
        0,
        20,
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """1.1.b: To what extent does the organization and their proposal demonstrate strong fit with the AI4D programme outcomes and demonstrate sufficient organizational capacity to manage the call?""",
            "fr": """""",
        },
        True,
    )

    add_evaluation_question(
        form.id,
        None,
        {
            "en": """1.2.a To what extent does the organization and the proposed budget and approach demonstrate value for money (e.g. low management to scholarship cost ratios), and a history of good fiscal management? 

Reference: Section IV (Budget) 

**0 - Very poor**: does not meet criteria 
**5 - Poor**: demonstrates some criteria  
**10 - Satisfactory**: meets most criteria though needs further elaboration 
**15 - Good**: meets all criteria  
**20 - Very Good**: meets and exceeds criteria  


""",
            "fr": """""",
        },
        0,
        20,
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """1.2.b: Qualitative assessment: To what extent does the organization and the proposed budget and approach demonstrate value for money (e.g. low management to scholarship cost ratios), and a history of good fiscal management? """,
            "fr": """""",
        },
        True,
    )

    add_divider(
        form.id,
        {"en": "2. Scholarship Plan Proposal", "fr": "2. Scholarship Plan Proposal"},
        None,
        sub_heading=True,
    )

    add_evaluation_question(
        form.id,
        None,
        {
            "en": """2.1 To what extent does the scholarship plan proposal demonstrate a feasible and coherent approach to supporting early career academics and winning PhD students, to meeting the basic call requirements for eligibility, structuring evaluation and selection of candidates, and ensuring gender, inclusion, equity and ethical considerations are included?  

Reference: Section II (all)

**0 - Very Poor**: Proposal provides little to no evidence or background justification for approach, does not address local contexts and needs, does not mention or meet requirements, does meet any expectations around design, outcomes, gender or inclusion principles 
**5 - Poor**: Minimal evidence and justification is provided for proposed approach; limited potential; provides vague anticipated outputs and outcomes; poor or absent strategy, significant weaknesses in meeting requirements, gender and inclusion, and ethics;  
**15 - Satisfactory**: Demonstrates satisfactory evidence and justification for approach and design, but certain improvements and clarifications are needed; meets the basic standards for meeting the call requirements; basic consideration of gender and inclusion principles, meets basic requirements   
**25 - Good**: Convincing and well cited justification for the proposed design; well-conceived approach with a likelihood for success; may go beyond the business-as-usual to support local contexts and needs; meets or slightly exceeds call requirements relating to evaluation of projects, engaging experts, and selection for gender, equity and inclusion as well as ethics. 
**35 - Very Good**: Very convincing approach with strong examples of evidence; very well conceived approach with a very high likelihood for success; innovative approaches will definitely go beyond the business-as-usual to support local contexts and needs; meets and exceeds call requirements relating to evaluation of projects, engaging experts in the selection process, and selection for gender, equity and inclusion as well as ethics.
""",
            "fr": """""",
        },
        0,
        35,
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """2.1.b To what extent does the scholarship plan proposal demonstrate a feasible and coherent approach to supporting early career academics and winning PhD students, to meeting the basic call requirements for eligibility, structuring evaluation and selection of candidates, and ensuring gender, inclusion, equity and ethical considerations are included?""",
            "fr": """""",
        },
        True,
    )

    add_divider(
        form.id,
        {
            "en": "3. Complementary activities plan",
            "fr": "3. Complementary activities plan",
        },
        None,
        sub_heading=True,
    )

    add_evaluation_question(
        form.id,
        None,
        {
            "en": """3.1 To what extent does the plan for complementary activities demonstrate that it meets the following criteria:  
    - Support for PhD students to connect with their peers, form scientific communities, network with industry, and other relevant opportunities that enable their success; 
    - That the program will create links between the individual early-career academics and their projects and teams to help add value across the program.; 
    - Support for the success of women, ethnic and linguistic minorities in activity design; 
    - Enable the success of host institutions; 
    - Advance the field of AI. 

Reference: Section 2.4   

**0 - Very poor**: does not meet criteria 
**5 - Poor**: demonstrates some criteria  
**10 - Satisfactory**: meets most criteria though needs further elaboration 
**15 - Good**: meets all criteria  
**20 - Very Good**: meets and exceeds criteria  
""",
            "fr": """""",
        },
        0,
        20,
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """3.1.b Please provide considerations to justify the score for question 3.1""",
            "fr": """""",
        },
        True,
    )

    add_divider(
        form.id,
        {"en": """4. Marketing and communications approach""", "fr": """"""},
        None,
        sub_heading=True,
    )

    add_evaluation_question(
        form.id,
        None,
        {
            "en": """4.1 To what extend does the proposal outline an effective marketing and communications strategy that will bring awareness to the AI4D Africa Scholars program? 

Reference: Section 3.a.
 
**0 - Very poor**: does not meet criteria 
**3 - Poor**: demonstrates some criteria  
**5 - Satisfactory**: meets most criteria though needs further elaboration 
**7 - Good**: meets all criteria  
**10 - Very Good**: meets and exceeds criteria """,
            "fr": """""",
        },
        0,
        10,
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """4.1.b: To what extend does the proposal outline an effective marketing and communications strategy that will bring awareness to the AI4D Africa Scholars program?""",
            "fr": """""",
        },
        True,
    )

    add_divider(
        form.id,
        {"en": """5. Final Overview""", "fr": """5. Final Overview"""},
        None,
        sub_heading=True,
    )

    add_question(
        form.id,
        "multi-choice",
        True,
        descriptions={
            "en": "5.1 On the basis of your overall review, do you recommend this proposal for selection?",
            "fr": "5.1 On the basis of your overall review, do you recommend this proposal for selection?",
        },
        options={
            "en": [
                {"value": "recommend", "label": "I recommend this proposal"},
                {"value": "reservations", "label": "I recommend with reservations"},
                {"value": "not-recommend", "label": "I do not recommend"},
            ],
            "fr": [
                {"value": "recommend", "label": "I recommend this proposal"},
                {"value": "reservations", "label": "I recommend with reservations"},
                {"value": "not-recommend", "label": "I do not recommend"},
            ],
        },
    )

    add_comment_question(
        form.id,
        None,
        {
            "en": """5.2 Overall considerations about the proposal (if not covered by earlier responses):""",
            "fr": """""",
        },
        True,
    )

    add_comment_question(
        form.id, None, {"en": """5.3 Feedback for applicant:""", "fr": """"""}, True
    )

    en, q = (
        db.session.query(QuestionTranslation, Question)
        .filter_by(headline="Name of Organisation", language="en")
        .join(Question, QuestionTranslation.question_id == Question.id)
        .filter_by(application_form_id=application_form.id)
        .first()
    )

    q.key = "review-identifier"

    en, q = (
        db.session.query(QuestionTranslation, Question)
        .filter_by(headline="Country", language="en")
        .join(Question, QuestionTranslation.question_id == Question.id)
        .filter_by(application_form_id=application_form.id)
        .first()
    )

    q.key = "review-identifier"

    db.session.commit()


def downgrade():
    event = db.session.query(Event).filter_by(key="spm").first()
    application_form = (
        db.session.query(ApplicationForm).filter_by(event_id=event.id).first()
    )
    form = (
        db.session.query(ReviewForm)
        .filter_by(application_form_id=application_form.id)
        .first()
    )

    questions = db.session.query(ReviewQuestion).filter_by(review_form_id=form.id).all()

    for q in questions:
        db.session.query(ReviewQuestionTranslation).filter_by(
            review_question_id=q.id
        ).delete()
        db.session.query(ReviewScore).filter_by(review_question_id=q.id).delete()
    db.session.commit()

    db.session.query(ReviewQuestion).filter_by(review_form_id=form.id).delete()
    db.session.commit()

    db.session.query(ReviewConfiguration).filter_by(review_form_id=form.id).delete()
    db.session.query(ReviewForm).filter_by(
        application_form_id=application_form.id
    ).delete()

    db.session.commit()
