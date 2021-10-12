# -*- coding: utf-8 -*-

"""More changes for AI4D

Revision ID: 78f4d11203c5
Revises: ea987b257ee0
Create Date: 2020-09-13 20:42:51.751172

"""

# revision identifiers, used by Alembic.
revision = "78f4d11203c5"
down_revision = "ea987b257ee0"

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

    section_translations = db.relationship("SectionTranslation", lazy="dynamic")

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


class EmailTemplate(Base):

    __tablename__ = "email_template"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer(), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    template = db.Column(db.String(), nullable=False)
    subject = db.Column(db.String(), nullable=False)

    def __init__(self, key, event_id, subject, template, language):
        self.key = key
        self.event_id = event_id
        self.subject = subject
        self.template = template
        self.language = language


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key="prc").first()
    form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    def get_question_by_en_headline(en_headline):
        en = (
            session.query(QuestionTranslation)
            .filter_by(headline=en_headline, language="en")
            .join(Question)
            .filter_by(application_form_id=form.id)
            .first()
        )
        question = en.question
        fr = question.get_translation("fr")
        return question, en, fr

    section_en = (
        session.query(SectionTranslation)
        .filter_by(name="Section IV: Budget", language="en")
        .first()
    )
    section_en.description = """Please submit a full three year budget with notes using the Excel template available on the IDRC public website: [https://www.idrc.ca/en/resources/guides-and-forms](https://www.idrc.ca/en/resources/guides-and-forms)
(Select the ‘Proposal budget’ and download.) 

Applications that do not submit a complete budget in this template will not be considered.
"""

    section_fr = (
        session.query(SectionTranslation)
        .filter_by(name="Section IV: Budget", language="fr")
        .first()
    )
    section_en.description = """Veuillez soumettre un budget triennal complet comprenant des notes en utilisant la feuille Excel qui est disponible sur le site Web public du CRDI, à la page suivante: [https://www.idrc.ca/fr/ressources/guides-et-formulaires](https://www.idrc.ca/en/resources/guides-and-forms)

Cliquez sur ‘proposition de projet’, puis téléchargez la feuille Excel. Les demandes qui ne comprennent pas un budget complet préparé au moyen de ce modèle ne seront pas prises en considération.

Insérez ce budget en tant que pièce jointe à votre demande. Dans le cas contraire, elle sera rejetée.
"""

    question, en, fr = get_question_by_en_headline(
        "How many people in total work in your organization?"
    )
    en.validation_regex = r"\d*"
    en.validation_text = "You must enter a number"
    fr.validation_regex = r"\d*"
    fr.validation_text = "Vous devez entrer un nombre"

    call_email_template_en = EmailTemplate(
        "confirmation-response-call",
        event.id,
        "Your response to the {event_name}",
        """Dear {title} {firstname} {lastname},

Thank you for responding to the {event_name}. Your application is being reviewed by our committee and we will get back to you as soon as possible. Included below is a copy of your responses.

{question_answer_summary}

Kind Regards,
The {event_name} Team""",
        "en",
    )
    session.add(call_email_template_en)

    call_email_template_fr = EmailTemplate(
        "confirmation-response-call",
        event.id,
        "Votre demande pour {event_name}",
        """Madame / Monsieur {lastname},

Merci d’avoir soumis votre demande de participation à {event_name}. Votre demande sera examinée par notre comité et nous vous répondrons dès que possible. Vous trouverez ci-dessous une copie de vos réponses.

{question_answer_summary}

Cordialement,
L’équipe de {event_name}""",
        "fr",
    )
    session.add(call_email_template_fr)

    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    session.query(EmailTemplate).filter_by(key="confirmation-response-call").delete()
    session.commit()
