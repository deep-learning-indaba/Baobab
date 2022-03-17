# -*- coding: utf-8 -*-

"""Final changes for AI4D call before launch

Revision ID: 039addb92a03
Revises: 8339a70d7345
Create Date: 2020-09-28 22:10:55.071894

"""

# revision identifiers, used by Alembic.
revision = "039addb92a03"
down_revision = "8339a70d7345"

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


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key="prc").first()
    form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    en = (
        session.query(SectionTranslation)
        .filter_by(language="en", name="Call for Proposals for Policy Research Centres")
        .first()
    )

    fr = (
        session.query(SectionTranslation)
        .filter_by(
            language="fr",
            name="Appel à Propositions pour les Centres de Recherche Politique",
        )
        .first()
    )

    en_desc = """The International Development Research Centre (IDRC) and the Swedish International Development Agency (Sida) invite proposals from independent policy research organizations from across the African continent that are committed to using research to inform and influence national-level artificial intelligence (AI) policies and research ecosystems. This funding opportunity will provide funding to two (2) AI policy research organizations representing distinct linguistic regions (anglophone and francophone).

The goal of this initiative is to enable African think tanks to inform and shape policies and strategies on Artificial Intelligence to support the adoption of responsible AI on the continent, and to ensure African experts have a voice in global fora.

The application will begin on the following page. You will need additional information and documentation to complete the proposal, including the CVs of your research team, and examples of your research and policy work. The proposal and all requested supporting materials must be submitted here no later than **23:59 EST on November 4th, 2020**.

For eligibility criteria, please see [http://www.ai4d.ai/call-policy-research/](http://www.ai4d.ai/call-policy-research/)
We recommend that applicants read the original [AI4D in Africa Proposal](https://bit.ly/33WWT32).
For more call details and eligibility criteria please read the [call document](https://bit.ly/3mWUgGZ).
To see the full set of proposal questions in advance: [download the questionnaire](https://bit.ly/36f6Xqy).

For any queries, please email [ai4dafrica@idrc.ca](mailto:ai4dafrica@idrc.ca)
"""

    en.description = en_desc

    fr_desc = """Le Centre de recherches pour le développement international (CRDI) et l’Agence suédoise de coopération au développement international (ASDI) invitent les organismes indépendants de recherche sur les politiques de l’ensemble du continent africain à soumettre des propositions dans la mesure où ils s’engagent à utiliser la recherche pour éclairer et influencer les politiques et les écosystèmes de recherche en matière d’intelligence artificielle à l’échelle nationale. Cette possibilité de financement permettra de financer deux (2) organismes de recherche sur les politiques d’IA représentant des régions linguistiques distinctes (anglophone et francophone).

L’objectif de cette initiative est de permettre aux think tanks africains d’éclairer et de façonner des politiques et des stratégies en matière d’intelligence artificielle afin de soutenir l’adoption d’une intelligence artificielle responsable sur le continent, et de garantir que les experts africains se feront entendre dans les forums mondiaux.

La demande commence à la page suivante. Vous aurez besoin d'informations et de documents supplémentaires pour compléter la proposition, y compris les CV de votre équipe de recherche et des exemples de vos travaux de recherche et de politique. La proposition et toutes les pièces justificatives demandées doivent être soumises ici au plus tard à **23h59 HNE le 4 novembre 2020**.

Pour les critères d'éligibilité, veuillez consulter [http://www.ai4d.ai/call-policy-research/](http://www.ai4d.ai/call-policy-research/)
Nous recommandons aux candidats de lire la [proposition originale d'AI4D en Afrique](https://bit.ly/32Zzmz4).
Pour plus de détails sur l'appel et les critères d'éligibilité, veuillez lire le document [de l'appel](https://bit.ly/3cCgIR7).
Pour pouvoir consulter l'ensemble des questions de la proposition à l'avance : [téléchargez le questionnaire](https://bit.ly/3mOvyIZ)

Pour toute question, veuillez envoyer un e-mail à [ai4dafrica@idrc.ca](mailto:ai4dafrica@idrc.ca)
"""
    fr.description = fr_desc

    event.application_close = datetime.datetime(2020, 11, 5, 4, 30, 0)

    session.commit()


def downgrade():
    pass
