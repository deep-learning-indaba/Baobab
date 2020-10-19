# -*- coding: utf-8 -*-

"""AI4D First Call Updates

Revision ID: ea987b257ee0
Revises: 613df2d7a759
Create Date: 2020-09-10 20:25:29.664321

"""

# revision identifiers, used by Alembic.
revision = 'ea987b257ee0'
down_revision = '613df2d7a759'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import select
from sqlalchemy.orm import column_property
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

class EventType(Enum):
    EVENT = 'event'
    AWARD = 'award'
    CALL = 'call'


class Event(Base):

    __tablename__ = "event"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    start_date = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    key = db.Column(db.String(255), nullable=False, unique=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
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

    event_translations = db.relationship('EventTranslation', lazy='dynamic')

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
        miniconf_url=None
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
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(2))

    event = db.relationship('Event', foreign_keys=[event_id])

    def __init__(self, name, description, language):
        self.name = name
        self.description = description
        self.language = language

class ApplicationForm(Base):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
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
    order = db.Column(db.Integer(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    key = db.Column(db.String(255), nullable=True)

    question_translations = db.relationship('QuestionTranslation', lazy='dynamic')

    def __init__(self, application_form_id, section_id, order, questionType, is_required=True):
        self.application_form_id = application_form_id
        self.section_id = section_id
        self.order = order
        self.type = questionType
        self.is_required = is_required

    def get_translation(self, language):
        question_translation = self.question_translations.filter_by(language=language).first()
        return question_translation


class Section(Base):
    __tablename__ = 'section'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey('question.id', use_alter=True), nullable=True)
    key = db.Column(db.String(255), nullable=True)

    section_translations = db.relationship('SectionTranslation', lazy='dynamic')

    def __init__(self, application_form_id, order, depends_on_question_id=None, key=None):
        self.application_form_id = application_form_id
        self.order = order
        self.depends_on_question_id = depends_on_question_id
        self.key = key

    def get_translation(self, language):
        section_translation = self.section_translations.filter_by(language=language).first()
        return section_translation


class SectionTranslation(Base):
    __tablename__ = 'section_translation'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=False)
    show_for_values = db.Column(db.JSON(), nullable=True)

    section = db.relationship('Section', foreign_keys=[section_id])

    def __init__(self, section_id, language, name, description, show_for_values=None):
        self.section_id = section_id
        self.language = language
        self.name = name
        self.description = description
        self.show_for_values = show_for_values


class QuestionTranslation(Base):
    __tablename__ = 'question_translation'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    show_for_values = db.Column(db.JSON(), nullable=True)

    question = db.relationship('Question', foreign_keys=[question_id])

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
        show_for_values=None
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


class Response(Base):

    __tablename__ = "response"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(),db.ForeignKey("application_form.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey("app_user.id"), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)
    is_withdrawn = db.Column(db.Boolean(), nullable=False)
    withdrawn_timestamp = db.Column(db.DateTime(), nullable=True)
    started_timestamp = db.Column(db.DateTime(), nullable=True)
    language = db.Column(db.String(2), nullable=False)

    answers = db.relationship('Answer', order_by='Answer.order')

    def __init__(self, application_form_id, user_id, language):
        self.application_form_id = application_form_id
        self.user_id = user_id
        self.is_submitted = False
        self.submitted_timestamp = None
        self.is_withdrawn = False
        self.withdrawn_timestamp = None
        self.language = language


class Answer(Base):

    __tablename__ = "answer"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), db.ForeignKey("response.id"), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey("question.id"), nullable=False)
    value = db.Column(db.String(), nullable=False)
    order = column_property(select([Question.order]).where(Question.id==question_id).correlate_except(Question))

    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='prc').first()
    form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    def get_question_by_en_headline(en_headline):
        en = (session.query(QuestionTranslation)
                .filter_by(headline=en_headline, language='en')
                .join(Question)
                .filter_by(application_form_id=form.id)
                .first())
        question = en.question
        fr = question.get_translation('fr')
        return question, en, fr
        
    # Remove organisation email question
    question, en, fr = get_question_by_en_headline('Email Address')
    session.query(Answer).filter_by(question_id=question.id).delete()
    session.query(QuestionTranslation).filter_by(id=en.id).delete()
    session.query(QuestionTranslation).filter_by(id=fr.id).delete()
    session.query(Question).filter_by(id=question.id).delete()

    # Update capitalization
    question, en, fr = get_question_by_en_headline('Name of Organisation')
    en.headline = 'Name of organization'

    question, en, fr = get_question_by_en_headline('Email Address of principal contact')
    en.headline = 'Email address of principal contact'

    question, en, fr = get_question_by_en_headline('Policy research')
    en.description = """How will you answer the proposed research questions in the most rigorous way possible? Please include a discussion of the conceptual and theoretical framework/s, user participation, data collection and analysis.
    
Maximum 750 words"""

    question, en, fr = get_question_by_en_headline('1. Policy engagement')
    en.description = """Please describe the kinds of engagement your organization has had with national governing institutions (e.g. government departments, bodies and agencies, commissions, parliaments, regulators, and other public-sector institutions) on any of the above topics (from Section I, question 3)? This can include a reflection on what you have done well with communications and what you have not done so well.

Please give up to three examples of this engagement, such as requests for input, sitting on policy steering committees and meetings with policy makers.

Maximum 350 words"""
    fr.description = """Veuillez décrire les types d’interactions que votre organisation a eus avec des institutions gouvernementales nationales (p. ex. ministères et organismes gouvernementaux, commissions, parlements, organismes de réglementation et autres institutions du secteur public) en ce qui concerne les sujets susmentionnés (à la section I, question 3). Vous pouvez notamment faire part de vos réflexions sur ce que vous avez bien fait en matière de communication, ainsi que sur les éléments que vous devez améliorer.
        
Veuillez fournir un maximum de trois exemples de ces interactions (p. ex. demandes de consultation, participation à des comités directeurs, réunions avec des décideurs politiques).

Maximum 350 mots"""

    question, en, fr = get_question_by_en_headline('3. Regional Engagement')
    en.headline = '3. Regional engagement'

    question, en, fr = get_question_by_en_headline('Regional Engagement')
    en.headline = 'Regional engagement'

    section_en = session.query(SectionTranslation).filter_by(
        name='Section IV: Budget').first()
    section_en.description = """Please submit a full three year budget with notes using the Excel template available on the IDRC public website: [https://www.idrc.ca/en/resources/guides-and-forms](https://www.idrc.ca/en/resources/guides-and-forms)
(Select the ‘Proposal budget’ and download.) 

Applications that do not submit a complete budget in this template will not be considered.
"""

    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='prc').first()
    form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    def get_question_by_en_headline(en_headline):
        en = (session.query(QuestionTranslation)
                .filter_by(headline=en_headline, language='en')
                .join(Question)
                .filter_by(application_form_id=form.id)
                .first())
        question = en.question
        fr = question.get_translation('fr')
        return question, en, fr

    def add_question(section, order, questionType, headlines,
        descriptions=None,
        placeholders=None,
        validation_regexs=None,
        validation_texts=None,
        options=None,
        show_for_values=None,
        is_required=True,
        depends_on_question_id=None):
        question = Question(form.id, section.id, order, questionType, is_required=is_required)

        if depends_on_question_id is not None:
            question.depends_on_question_id = depends_on_question_id

        session.add(question)
        session.commit()

        translations = []
        for language in headlines:
            translations.append(QuestionTranslation(question.id, language, 
                headline=headlines[language],
                description=None if descriptions is None else descriptions[language],
                placeholder=None if placeholders is None else placeholders[language],
                validation_regex=None if validation_regexs is None else validation_regexs[language],
                validation_text=None if validation_texts is None else validation_texts[language],
                options=None if options is None else options[language],
                show_for_values=None if show_for_values is None else show_for_values[language]))
        session.add_all(translations)
        session.commit()
        return question

    section_en = session.query(SectionTranslation).filter_by(name='Organization and lead applicant contact details').first()
    add_question(section_en.section, 9, 'short-text', {
        'en': 'Email Address',
        'fr': 'Adresse de courriel'
    })

    question, en, fr = get_question_by_en_headline('Name of organization')
    en.headline = 'Name of Organisation'

    question, en, fr = get_question_by_en_headline('Email address of principal contact')
    en.headline = 'Email Address of principal contact'

    question, en, fr = get_question_by_en_headline('3. Regional engagement')
    en.headline = '3. Regional Engagement'

    question, en, fr = get_question_by_en_headline('Regional engagement')
    en.headline = 'Regional Engagement'
    
    session.commit()
