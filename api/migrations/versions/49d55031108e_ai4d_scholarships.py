# -*- coding: utf-8 -*-

"""Set up AI4D Scholarships Call

Revision ID: 49d55031108e
Revises: d7dfd413e768
Create Date: 2020-11-03 22:26:56.570501

"""

# revision identifiers, used by Alembic.
revision = "49d55031108e"
down_revision = "d7dfd413e768"

import datetime
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()

en_countries = [
    "Algeria",
    "Angola",
    "Benin",
    "Botswana",
    "Burkina Faso",
    "Burundi",
    "Cameroon",
    "Cape Verde",
    "Central African Republic",
    "Chad",
    "Comoros",
    "Democratic Republic of the Congo",
    "Republic of the Congo",
    "Côte d’Ivoire",
    "Djibouti",
    "Egypt",
    "Equatorial Guinea",
    "Eritrea",
    "Eswatini",
    "Ethiopia",
    "Gabon",
    "The Gambia",
    "Ghana",
    "Guinea",
    "Guinea-Bissau",
    "Kenya",
    "Lesotho",
    "Liberia",
    "Libya",
    "Madagascar",
    "Malawi",
    "Mali",
    "Mauritania",
    "Mauritius",
    "Morocco",
    "Mozambique",
    "Namibia",
    "Niger",
    "Nigeria",
    "Rwanda",
    "Sao Tome and Principe",
    "Senegal",
    "Seychelles",
    "Sierra Leone",
    "Somalia",
    "South Africa",
    "South Sudan",
    "Sudan",
    "Tanzania",
    "Togo",
    "Tunisia",
    "Uganda",
    "Zambia",
    "Zimbabwe",
]

fr_countries = [
    "Algérie",
    "Angola",
    "Bénin",
    "Botswana",
    "Burkina Faso",
    "Burundi",
    "Cameroun",
    "Cap-Vert",
    "République centrafricaine",
    "Tchad",
    "Comores",
    "République démocratique du Congo",
    "République du Congo",
    "Côte d’Ivoire",
    "Djibouti",
    "Égypte",
    "Guinée équatoriale",
    "Érythrée",
    "Eswatini",
    "Éthiopie",
    "Gabon",
    "Gambie",
    "Ghana",
    "Guinée",
    "Guinée-Bissau",
    "Kenya",
    "Lesotho",
    "Libéria",
    "Libye",
    "Madagascar",
    "Malawi",
    "Mali",
    "Maroc",
    "Mauritanie",
    "île Maurice",
    "Mozambique",
    "Namibie",
    "Niger",
    "Nigeria",
    "Rwanda",
    "Sao Tomé-et-Principe",
    "Sénégal",
    "Seychelles",
    "Sierra Leone",
    "Somalie",
    "Afrique du Sud",
    "Soudan du Sud",
    "Soudan",
    "Tanzanie",
    "Togo",
    "Tunisie",
    "Ouganda",
    "Zambie",
    "Zimbabwe",
]


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


class SectionTranslation(Base):
    __tablename__ = "section_translation"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey("section.id"), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=False)
    show_for_values = db.Column(db.JSON(), nullable=True)

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

    ai4d = session.query(Organisation).filter_by(name="AI4D Africa").first()

    op.alter_column(
        "event_translation",
        "description",
        existing_type=sa.String(length=255),
        type_=sa.String(length=500),
    )

    # Add Event
    event = Event(
        {
            "en": "AI4D Call for Proposals: Scholarships program manager",
            "fr": "Appel à propositions IAPD: Gestionnaire des programmes de bourses",
        },
        {
            "en": "Academic capacity building to foster African talent around Artificial Intelligence: Seeking a program and financial manager for the African Artificial Intelligence for Development (AI4D) Scholarships program",
            "fr": "Renforcement des capacités dans les milieux universitaires pour favoriser le développement des talents africains autour de l’intelligence artificielle : Recherche d’un responsable de programme et directeur financier pour le programme de bourses d’études africaines en intelligence artificielle pour le développement (IAPD).",
        },
        start_date=datetime.date(2020, 12, 8),
        end_date=datetime.date(2020, 12, 8),
        key="spm",
        organisation_id=ai4d.id,
        email_from="calls@ai4d.ai",
        url="https://ai4d.ai/calls/scholarships-manager/",
        application_open=datetime.date(2020, 11, 3),
        application_close=datetime.datetime(
            2020, 12, 9, 5, 0, 0
        ),  # Equivalent to midnight EST
        review_open=datetime.date(2020, 12, 9),
        review_close=datetime.date(2020, 12, 17),
        selection_open=datetime.date(2020, 12, 18),
        selection_close=datetime.date(2020, 12, 31),
        offer_open=datetime.date(2020, 12, 18),
        offer_close=datetime.date(2020, 12, 31),
        registration_open=datetime.date(2020, 12, 31),
        registration_close=datetime.date(2020, 12, 31),
        event_type=EventType.CALL,
        travel_grant=False,
    )

    session.add(event)
    session.commit()

    form = ApplicationForm(event.id, True, False)
    session.add(form)
    session.commit()

    def add_section(
        names,
        descriptions,
        order,
        depends_on_question_id=None,
        key=None,
        show_for_values=None,
    ):
        section = Section(form.id, order)
        session.add(section)
        session.commit()

        translations = []
        for language in names:
            translations.append(
                SectionTranslation(
                    section.id,
                    language,
                    names[language],
                    "" if descriptions is None else descriptions[language],
                    show_for_values=None
                    if show_for_values is None
                    else show_for_values[language],
                )
            )
        session.add_all(translations)
        session.commit()
        return section

    def add_question(
        section,
        order,
        questionType,
        headlines,
        descriptions=None,
        placeholders=None,
        validation_regexs=None,
        validation_texts=None,
        options=None,
        show_for_values=None,
        is_required=True,
        depends_on_question_id=None,
    ):
        question = Question(
            form.id, section.id, order, questionType, is_required=is_required
        )

        if depends_on_question_id is not None:
            question.depends_on_question_id = depends_on_question_id

        session.add(question)
        session.commit()

        translations = []
        for language in headlines:
            translations.append(
                QuestionTranslation(
                    question.id,
                    language,
                    headline=headlines[language],
                    description=None
                    if descriptions is None
                    else descriptions[language],
                    placeholder=None
                    if placeholders is None
                    else placeholders[language],
                    validation_regex=None
                    if validation_regexs is None
                    else validation_regexs[language],
                    options=None if options is None else options[language],
                    show_for_values=None
                    if show_for_values is None
                    else show_for_values[language],
                )
            )
        session.add_all(translations)
        session.commit()
        return question

    en_description = """Academic capacity building to foster African talent around Artificial Intelligence: Seeking a program and financial manager for the African Artificial Intelligence for Development (AI4D) Scholarships program
    
The International Development Research Centre (IDRC) and the Swedish International Development Agency (Sida) invite proposals from qualified institutions to manage the African Artificial Intelligence for Development (AI4D) Scholarships program.  

The goal of this call is to identify a program and financial manager for the AI4D Scholarships program. The host institution (“scholarships manager”) will design and administer a scholarships program that will foster the talent needed to meet a growing demand for responsible Artificial Intelligence (“AI”) for development research and innovation in African public universities. The program will support two scholarship activities: (i) the African AI4D PhD Scholarships and (ii) the African AI4D Advanced Scholars Program. The African AI4D Scholarships program will provide support to the next generation of AI and related disciplines (such as machine learning) academics, practitioners and students who are focused on responsible AI innovation for sustainable development. Responsible AI strives to be inclusive, rights-based and sustainable in its development and implementation, ensuring that AI applications are leveraged for public benefit.1  

For eligibility criteria, please see https://ai4d.ai/calls/scholarships-manager/

The deadline for submission of the proposal online is 23:59 EST on December 8, 2020.
"""
    fr_description = """Renforcement des capacités dans les milieux universitaires pour favoriser le développement des talents africains autour de l’intelligence artificielle : Recherche d’un responsable de programme et directeur financier pour le programme de bourses d’études africaines en intelligence artificielle pour le développement (IAPD).

Le présent appel a pour objectif de désigner un gestionnaire de programme et directeur financier pour le programme de bourses d’études en IAPD. L’institution d’accueil (« gestionnaire de bourses ») concevra et administrera un programme de bourses d’études qui favorisera le développement des talents nécessaires pour répondre à une demande croissante en recherche et en innovation dans le domaine de l’intelligence artificielle (« IA ») responsable pour le développement dans les universités publiques africaines. Le programme soutiendra deux activités d’allocation de bourses : (i) les bourses de doctorat africaines en IAPD et (ii) le programme de bourses avancées africaines en IAPD. Le programme de bourses d’études africaines en IAPD apportera un soutien à la prochaine génération d’universitaires, de praticiens et d’étudiants en IA et dans les disciplines connexes (telles que l’apprentissage automatique) qui se concentrent sur l’innovation en IA responsable pour le développement durable. L’IA responsable s’efforce d’être inclusive, fondée sur les droits et durable dans son développement et sa mise en oeuvre, en veillant à ce que les applications d’IA soient exploitées au profit du public. 

La proposition et tous les documents à l’appui demandés doivent être soumis par l’intermédiaire du site baobab.ai4d.ai au plus tard le 8 decembre 2020, à 23 h 59 (HNE).

Pour les critères d'éligibilité, veuillez consulter https://ai4d.ai/calls/scholarships-manager/

Pour toute question, veuillez envoyer un e-mail à calls@ai4d.ai
"""

    # (Description Page)
    add_section(
        {
            "en": "AI4D Call for Proposals: Scholarships program manager",
            "fr": "Appel à propositions IAPD: Gestionnaire des programmes de bourses",
        },
        {"en": en_description, "fr": fr_description},
        1,
    )

    # Organisation and lead contact details
    org_section = add_section(
        {
            "en": "Organisation and Lead Applicant Contact details",
            "fr": "Coordonnées de l'organisation et de la personne-ressource pour cette demande",
        },
        None,
        2,
    )

    add_question(
        org_section,
        1,
        "information",
        {"en": "Organization Information", "fr": "Renseignements sur l’organisation"},
        is_required=False,
    )

    add_question(
        org_section,
        2,
        "short-text",
        {"en": "Name of Organisation", "fr": "Nom de l’organisation"},
        is_required=True,
    )

    add_question(
        org_section,
        3,
        "short-text",
        {"en": "Director/CEO", "fr": "Directeur ou premier dirigeant"},
        is_required=True,
    )

    add_question(
        org_section,
        4,
        "short-text",
        {"en": "Mailing address", "fr": "Adresse postale"},
        is_required=True,
    )

    add_question(
        org_section, 5, "short-text", {"en": "City", "fr": "Ville"}, is_required=True
    )

    en_options = [{"label": c, "value": c} for c in en_countries]
    fr_options = [{"label": f, "value": e} for e, f in zip(en_countries, fr_countries)]

    add_question(
        org_section,
        6,
        "multi-choice",
        {"en": "Country", "fr": "Pays"},
        descriptions={
            "en": "Eligible countries in sub-Saharan and North Africa",
            "fr": "Pays admissibles de l’Afrique subsaharienne et de l’Afrique du Nord",
        },
        placeholders={"en": "Select a Country", "fr": "Choisissez un Pays"},
        options={"en": en_options, "fr": fr_options},
        is_required=True,
    )

    add_question(
        org_section,
        7,
        "short-text",
        {"en": "Telephone", "fr": "Numéro de téléphone"},
        is_required=True,
    )

    add_question(
        org_section,
        8,
        "short-text",
        {"en": "Mobile (Optional)", "fr": "Numéro de téléphone mobile (facultatif)"},
        is_required=False,
    )

    add_question(
        org_section,
        9,
        "short-text",
        {"en": "Email Address", "fr": "Adresse de courriel"},
        is_required=True,
    )

    add_question(
        org_section,
        10,
        "short-text",
        {"en": "Website", "fr": "Site Web"},
        is_required=True,
    )

    add_question(
        org_section,
        11,
        "short-text",
        {
            "en": "Social media handles (optional)",
            "fr": "Pseudonymes sur les médias sociaux (facultatif)",
        },
        is_required=False,
    )

    add_question(
        org_section,
        12,
        "information",
        {
            "en": "Name and contact details of principal contact for the application",
            "fr": "Nom et coordonnées de la personne-ressource pour cette demande",
        },
        is_required=False,
    )

    add_question(
        org_section,
        13,
        "short-text",
        {"en": "Name of principal contact", "fr": "Nom du contact principal"},
        is_required=True,
    )

    add_question(
        org_section,
        14,
        "short-text",
        {
            "en": "Email Address of principal contact",
            "fr": "Adresse de courriel du contact principal",
        },
        is_required=True,
    )

    add_question(
        org_section,
        15,
        "short-text",
        {
            "en": "Telephone/Mobile of principal contact",
            "fr": "Numéro de téléphone ou de téléphone mobile du contact principal",
        },
        is_required=True,
    )

    # Section 1
    section1 = add_section(
        {
            "en": "Section I: Organizational capacity and program fit of scholarships manager",
            "fr": "Section I: Capacité organisationnelle et compatibilité avec le programme du gestionnaire de bourses",
        },
        None,
        3,
    )

    add_question(
        section1,
        1,
        "short-text",
        {
            "en": "1. How many people in total work in your organization?",
            "fr": "1. Combien d’employés compte votre organisation en tout?",
        },
        descriptions={
            "en": "Total number of employees",
            "fr": "Nombre total d’employés",
        },
        is_required=True,
    )

    add_question(
        section1,
        2,
        "short-text",
        {
            "en": "1a. Of these, how many are full time employees?",
            "fr": "1a. Combien d’entre eux occupent un poste d’employé à temps plein?",
        },
        is_required=True,
    )

    add_question(
        section1,
        3,
        "multi-file",
        {
            "en": "1b. Please provide the names and CVs of your institution's primary officers and administrators who will be responsible for developing and managing the African AI4D Scholarships program (up to five)",
            "fr": "1b. Veuillez fournir le nom et le CV des principaux responsables et administrateurs de votre établissement qui seront chargés d’élaborer et de gérer le programme de bourses africaines d’AI4D (cinq au maximum)",
        },
        descriptions={
            "en": "Upload the five CVs of relevant staff in the organization here.",
            "fr": "Téléchargez ici les CV des cinq employés concernés de votre organisation.",
        },
        is_required=True,
        options={"en": {"num_uploads": 5}, "fr": {"num_uploads": 5}},
    )

    add_question(
        section1,
        4,
        "long-text",
        {
            "en": "2. Demonstrated experience and capacity",
            "fr": "2. Expérience et capacité démontrées",
        },
        descriptions={
            "en": """Please provide examples of past or current related experience of your institution in implementing scholarship or grant programs to individuals in Africa. 
(Max. 1000 words)""",
            "fr": """Veuillez fournir des exemples d’expériences passées ou actuelles de mise en oeuvre par votre établissement de programmes de bourses ou de subventions destinées à des personnes en Afrique 
(1000 mots au maximum).""",
        },
        placeholders={"en": "Enter up to 1000 words", "fr": "Entrez jusqu'à 1000 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,1000}$",
            "fr": r"^\s*(\S+(\s+|$)){0,1000}$",
        },
        validation_texts={"en": "Maximum 1000 words", "fr": "Maximum 1000 mots"},
        is_required=True,
    )

    add_question(
        section1,
        5,
        "long-text",
        {"en": "2a. Available resources ", "fr": "2a. Ressources disponibles"},
        descriptions={
            "en": """Discuss the resources and capacities that your institution already has to successfully implement the African AI4D Scholarships program. (Max.750 words). Note: The scholarship manager is encouraged to use existing resources, including leveraging past or active grants and/or scholarships, to support the development and management of the scholarships. 
(Max. 750 words)""",
            "fr": """Indiquez les ressources et les capacités dont dispose déjà votre établissement pour mettre en oeuvre avec succès le programme de bourses africaines d’AI4D (750 mots au maximum). Remarque : Le gestionnaire des bourses est encouragé à utiliser les ressources existantes, notamment en tirant parti des subventions ou bourses antérieures ou actives, pour appuyer le développement et la gestion des bourses. 
(750 mots au maximum).""",
        },
        placeholders={"en": "Enter up to 750 words", "fr": "Entrez jusqu'à 750 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,750}$",
            "fr": r"^\s*(\S+(\s+|$)){0,750}$",
        },
        validation_texts={"en": "Maximum 750 words", "fr": "Maximum 750 mots"},
        is_required=True,
    )

    q2b = add_question(
        section1,
        6,
        "multi-choice",
        {"en": "2b. Partnerships plan", "fr": "2b. Plan de partenariats"},
        descriptions={
            "en": "The host institution may choose to supplement the scholarships, including the complementary activities, through different partnerships. Do you plan to partner with other institutes or groups to support the scholarships?",
            "fr": "L’établissement d’accueil peut choisir de compléter les bourses, y compris les activités complémentaires, au moyen de différents partenariats. Prévoyez-vous de vous associer à d’autres instituts ou groupes pour soutenir les bourses?",
        },
        options={
            "en": [{"label": "Yes", "value": "Yes"}, {"label": "No", "value": "No"}],
            "fr": [{"label": "Oui", "value": "Yes"}, {"label": "Non", "value": "No"}],
        },
        is_required=True,
    )

    add_question(
        section1,
        7,
        "long-text",
        {
            "en": "2c. Please provide a brief overview of your plan for coordinating those partnerships",
            "fr": "2c. Dans l’affirmative, veuillez brièvement décrire comment vous prévoyez coordonner ces partenariats",
        },
        descriptions={"en": "(Max. 350 words)", "fr": "(350 mots au maximum)"},
        placeholders={"en": "Enter up to 350 words", "fr": "Entrez jusqu'à 350 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,350}$",
            "fr": r"^\s*(\S+(\s+|$)){0,350}$",
        },
        validation_texts={"en": "Maximum 350 words", "fr": "Maximum 350 mots"},
        is_required=True,
        depends_on_question_id=q2b.id,
        show_for_values={"en": ["Yes"], "fr": ["Yes"]},
    )

    add_question(
        section1,
        8,
        "long-text",
        {
            "en": "3. Relevant expertise of staff",
            "fr": "3. Expertise pertinente du personnel",
        },
        descriptions={
            "en": """Describe the relevant expertise and skills that are in-house and can be deployed to evaluate AI for development scholarship proposals across a variety of domains. What expertise gaps do you have and how will you identify and mobilize the appropriate expertise to fill them? 
(Max. 500 words)""",
            "fr": """Décrivez l’expertise et les compétences pertinentes qui existent en interne et qui peuvent être déployées pour évaluer les propositions de bourses de développement de l’IA dans divers domaines. Quelles sont vos lacunes en matière d’expertise et comment allez-vous repérer et mobiliser l’expertise appropriée pour les combler? 
(500 mots au maximum)""",
        },
        placeholders={"en": "Enter up to 500 words", "fr": "Entrez jusqu'à 500 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,500}$",
            "fr": r"^\s*(\S+(\s+|$)){0,500}$",
        },
        validation_texts={"en": "Maximum 500 words", "fr": "Maximum 500 mots"},
        is_required=True,
    )

    # Section 2
    section2 = add_section(
        {
            "en": "Section II: Scholarship Plan and Proposal",
            "fr": """Section II: Plan et proposition de les programmes de bourses d'études""",
        },
        None,
        4,
    )

    add_question(
        section2,
        1,
        "long-text",
        {
            "en": "1. General and specific objectives for the proposed AI4D Scholarships Management",
            "fr": "1. Objectifs généraux et précis.",
        },
        descriptions={
            "en": """The general objective should state the goals being pursued by the project overall. The specific objectives should indicate the specific types of knowledge to be produced, the audiences to be reached, and forms of capacity to be reinforced. These are the objectives against which the success of the project will be judged. Use only active verbs (no passive). 
(Max. 250 words)""",
            "fr": """L’objectif général correspond à l’objectif de développement que l’on souhaite atteindre au moyen de la recherche. Les objectifs particuliers doivent signaler les types précis de connaissances recherchées, les destinataires et les capacités à renforcer. C’est en fonction de ces objectifs que sera jaugée la réussite du projet. Utilisez seulement des verbes d’action (évitez les verbes d’état).
(250 mots au maximum)""",
        },
        placeholders={"en": "Enter up to 250 words", "fr": "Entrez jusqu'à 250 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,250}$",
            "fr": r"^\s*(\S+(\s+|$)){0,250}$",
        },
        validation_texts={"en": "Maximum 250 words", "fr": "Maximum 250 mots"},
        is_required=True,
    )

    add_question(
        section2,
        2,
        "long-text",
        {
            "en": "2. Summary of the proposed approach to the financial and administrative management of the AI4D scholarships",
            "fr": "2. Résumé de l’approche proposée pour la gestion financière et administrative de la bourse d’AI4D",
        },
        descriptions={
            "en": """Briefly outline your proposal to manage the AI4D scholarship program according to the requirements outlined in section 2.1 of the Call for Proposals Background Document. What approaches, disciplines and modalities will you draw upon to support this 
Be sure to outline the key priorities, background, problems and justifications for supporting AI talent and capacity building work in the context of Africa.
Briefly describe the overall approach/logic/pathway to achieve the project objectives.
(Max. 1000 words)
""",
            "fr": """Décrivez brièvement comment vous proposez de gérer le programme de bourses d’AI4D conformément aux exigences décrites dans la section 2.1 du document de référence de l’appel à propositions. Quelles méthodes, disciplines et modalités allez-vous utiliser à l’appui? 
Veillez à présenter les principales priorités, le contexte, les problèmes et les justifications du soutien aux talents et au travail de renforcement des capacités d’IA dans le contexte de l’Afrique.
Décrivez brièvement l’approche, la logique ou le cheminement permettant d’atteindre les objectifs du projet 
(1 000 mots au maximum).""",
        },
        placeholders={"en": "Enter up to 1000 words", "fr": "Entrez jusqu'à 1000 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,1000}$",
            "fr": r"^\s*(\S+(\s+|$)){0,1000}$",
        },
        validation_texts={"en": "Maximum 1000 words", "fr": "Maximum 1000 mots"},
        is_required=True,
    )

    add_question(
        section2,
        3,
        "long-text",
        {"en": "2a.Communication strategies", "fr": "2a. Stratégies de communication"},
        descriptions={
            "en": """Discuss the plan for launching the African AI4D PhD Scholarship and the African AI4D Advanced Scholars Program.  How does the plan ensure that the program will be as inclusive as possible?
What will be the approach to spotlight the research of scholarship recipients and disseminate their project results widely, targeting both academics and practitioners?
(Max. 750 words)
""",
            "fr": """Discutez du plan de lancement de la bourse de doctorat africaine d’AI4D et du programme de bourses avancées africaines d’AI4D. Comment le plan garantira-t-il que le programme sera aussi inclusif que possible? 
Quelle sera l’approche adoptée pour mettre en lumière les recherches des bénéficiaires de bourses et diffuser largement les résultats de leurs projets, en ciblant à la fois les universitaires et les praticiens?
(750 mots au maximum).""",
        },
        placeholders={"en": "Enter up to 750 words", "fr": "Entrez jusqu'à 750 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,750}$",
            "fr": r"^\s*(\S+(\s+|$)){0,750}$",
        },
        validation_texts={"en": "Maximum 750 words", "fr": "Maximum 750 mots"},
        is_required=True,
    )

    add_question(
        section2,
        4,
        "long-text",
        {
            "en": "2b. Monitoring, evaluation, and learning (MEL)",
            "fr": "2b. Suivi, évaluation et apprentissage",
        },
        descriptions={
            "en": """Discuss your strategy for ongoing monitoring of the scholarship programs, adapting in response to lessons learned and emergent issues, learning to improve future scholarship calls, and evaluating the impact of the program? 
(Max. 750 words)""",
            "fr": """Discutez de votre stratégie de suivi permanent des programmes de bourses, d’adaptation en fonction des enseignements tirés et des questions émergentes, d’apprentissage pour améliorer les futurs appels à propositions de bourses et d’évaluation de l’impact du programme 
(750 mots au maximum).""",
        },
        placeholders={"en": "Enter up to 750 words", "fr": "Entrez jusqu'à 750 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,750}$",
            "fr": r"^\s*(\S+(\s+|$)){0,750}$",
        },
        validation_texts={"en": "Maximum 750 words", "fr": "Maximum 750 mots"},
        is_required=True,
    )

    add_question(
        section2,
        5,
        "long-text",
        {
            "en": "3. Design of the scholarship plans",
            "fr": "3. Conception des plans de bourses ",
        },
        descriptions={
            "en": """Briefly outline your proposed plan for the design of the (i) PhD Scholarship and (ii) Early Career Scholars Program. Include details on how funds will be disbursed and explain how the scholarships would support research of the winning PhD students and Early Career Academics in practise. 
How will your proposed approach help meet the requirements for the calls outlined in section 2?
(Max. 1000 words)""",
            "fr": """Décrivez brièvement le plan que vous proposez pour la conception (i) de la bourse de doctorat et (ii) du programme de bourses d’études en début de carrière. Donnez des détails sur la manière dont les fonds seront déboursés et expliquez comment les bourses appuieront la recherche des étudiants en doctorat et des universitaires en début de carrière bénéficiaires des bourses dans la pratique. 
Comment l’approche que vous proposez contribuera-t-elle à répondre aux exigences des appels décrites dans la section 2?
(1 000 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 1000 words", "fr": "Entrez jusqu'à 1000 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,1000}$",
            "fr": r"^\s*(\S+(\s+|$)){0,1000}$",
        },
        validation_texts={"en": "Maximum 1000 words", "fr": "Maximum 1000 mots"},
        is_required=True,
    )

    add_question(
        section2,
        6,
        "long-text",
        {
            "en": "3a. Gender and Inclusion Considerations",
            "fr": "3a. Considérations liées à la sexospécificité et à l’inclusion",
        },
        descriptions={
            "en": """How will your proposed approach promote increased diversity and equity in AI research? What literature or experience will you draw upon to support gender equity and linguistic equity goals in the design and execution of the calls? How will you process integrate best practices in marketing and outreach, engagement, and support for recipients? 
(Max. 750 words)""",
            "fr": """Comment l’approche que vous proposez va-t-elle promouvoir une plus grande diversité et équité dans la recherche en IA? Quelle documentation ou expérience allez-vous utiliser pour soutenir les objectifs d’équité entre les sexes et d’équité linguistique dans la conception et l’exécution des appels? Comment allez-vous procéder pour intégrer les meilleures pratiques en matière de marketing et de sensibilisation, d’engagement et de soutien aux bénéficiaires?
(750 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 750 words", "fr": "Entrez jusqu'à 750 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,750}$",
            "fr": r"^\s*(\S+(\s+|$)){0,750}$",
        },
        validation_texts={"en": "Maximum 750 words", "fr": "Maximum 750 mots"},
        is_required=True,
    )

    add_question(
        section2,
        7,
        "long-text",
        {
            "en": "3b. Selection process and evaluation",
            "fr": "3b. Processus de sélection et évaluation",
        },
        descriptions={
            "en": """Broadly discuss the evaluation process for the two scholarships activities 
How will the evaluation process ensure that the projects funded will be relevant to the AI4D Africa program’s responsible AI mandate, address ethical concerns and gender dimensions, and assess the capacity of applicants to carry out the proposed research? 
(Max. 1000 words)""",
            "fr": """Présentez dans les grandes lignes le processus d’évaluation des deux activités de bourses.
Comment le processus d’évaluation garantira-t-il que les projets financés auront un rapport direct avec le mandat responsable en IA d’AI4D Africa, qu’ils répondront aux préoccupations éthiques et aux dimensions sexospécifiques, et qu’ils évalueront la capacité des candidats à mener à bien la recherche proposée?
(1000 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 1000 words", "fr": "Entrez jusqu'à 1000 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,1000}$",
            "fr": r"^\s*(\S+(\s+|$)){0,1000}$",
        },
        validation_texts={"en": "Maximum 1000 words", "fr": "Maximum 1000 mots"},
        is_required=True,
    )

    add_question(
        section2,
        8,
        "long-text",
        {
            "en": "4. Complementary Activities Plan",
            "fr": "4. Plan d’activités complémentaires",
        },
        descriptions={
            "en": """Briefly outline the plan for the complementary activities that will be developed in relation to the two scholarship programs.
How will the complementary activities enable PhD students to develop professionally and connect with their peers and publicize their work? 
 How will the complementary activities help in forming links between Early Career Academics and add value in an aggregate way?
(Max. 1000 words)""",
            "fr": """Décrivez brièvement le plan des activités complémentaires qui seront élaborées en relation avec les deux programmes de bourses.
Comment les activités complémentaires vont-elles permettre aux étudiants en doctorat de se développer professionnellement, d’entrer en contact avec leurs pairs et de faire connaître leurs travaux?
Comment les activités complémentaires aideront-elles à établir des liens entre les universitaires en début de carrière et à apporter une valeur ajoutée dans l’ensemble?
(1000 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 1000 words", "fr": "Entrez jusqu'à 1000 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,1000}$",
            "fr": r"^\s*(\S+(\s+|$)){0,1000}$",
        },
        validation_texts={"en": "Maximum 1000 words", "fr": "Maximum 1000 mots"},
        is_required=True,
    )

    add_question(
        section2,
        9,
        "long-text",
        {"en": "5. Ethical considerations", "fr": "5. Considérations d’ordre éthique"},
        descriptions={
            "en": """All projects that include human subjects must ensure that their privacy, dignity, and integrity are protected. An independent ethical review committee must approve the protocols. Please describe the key ethical considerations for the proposed research and the research ethics protocols your organization uses.
(Max. 350 words)""",
            "fr": """Dans le cadre de tout projet de recherche portant sur des sujets humains, il faut garantir la protection de la vie privée, de la dignité et de l’intégrité de la personne. Un comité d’éthique indépendant doit autoriser les protocoles. Veuillez décrire les principales considérations d’ordre éthique pour la recherche proposée, ainsi que les protocoles d’éthique de la recherche utilisés par votre organisation.
(350 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 350 words", "fr": "Entrez jusqu'à 350 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,350}$",
            "fr": r"^\s*(\S+(\s+|$)){0,350}$",
        },
        validation_texts={"en": "Maximum 350 words", "fr": "Maximum 350 mots"},
        is_required=True,
    )

    add_question(
        section2,
        10,
        "long-text",
        {"en": "6. Results", "fr": "6. Résultats"},
        descriptions={
            "en": """Please describe what success will look like at the end of the three years. What markers will you use to gauge your success in the  AI4D scholarships? What are your expected outputs and outcomes?
(Max. 500 words)""",
            "fr": """Veuillez décrire ce à quoi ressemblera la réussite à la fin de la période de trois années. Quels marqueurs utiliserez-vous pour évaluer votrel’initiative IAPD Afrique? Quels sont les résultats escomptés de votre recherche?
(500 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 500 words", "fr": "Entrez jusqu'à 500 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,500}$",
            "fr": r"^\s*(\S+(\s+|$)){0,500}$",
        },
        validation_texts={"en": "Maximum 500 words", "fr": "Maximum 500 mots"},
        is_required=True,
    )

    add_question(
        section2,
        11,
        "long-text",
        {"en": "7. Project schedule", "fr": "7. Calendrier du projet"},
        descriptions={
            "en": """Please provide a draft schedule for how you envision the activities will be organized according to the specific objectives of the project. The project schedule should include a list of key outputs and milestones (key events or deliverables). These need to be related to the items included in the project budget (Section IV).
(Max. 350 words)""",
            "fr": """Veuillez fournir un calendrier provisoire pour expliquer la façon dont vous comptez organiser les activités, compte tenu des objectifs spécifiques du projet. Le calendrier du projet doit comprendre une liste des principaux extrants et jalons (événements ou produits livrables clés). Ils doivent être liés aux éléments qui figurent dans le budget du projet (section 4).
(350 mots au maximum)
""",
        },
        placeholders={"en": "Enter up to 350 words", "fr": "Entrez jusqu'à 350 mots"},
        validation_regexs={
            "en": r"^\s*(\S+(\s+|$)){0,350}$",
            "fr": r"^\s*(\S+(\s+|$)){0,350}$",
        },
        validation_texts={"en": "Maximum 350 words", "fr": "Maximum 350 mots"},
        is_required=True,
    )

    add_question(
        section2,
        12,
        "multi-file",
        {
            "en": "8. Supplemental documentation (optional).",
            "fr": "8. Documents supplémentaires (facultatifs).",
        },
        descriptions={
            "en": "Attach any supplemental documentation that will help clarify your application.",
            "fr": "Veuillez joindre toute documentation supplémentaire qui aidera à clarifier votre demande.",
        },
        is_required=False,
    )

    # Section 3
    section3 = add_section(
        {"en": "Section III", "fr": """Section III"""},
        {
            "en": r"""IDRC Open Access Policy 
[https://www.idrc.ca/en/open-access-policy-idrc-funded-project-outputs](https://www.idrc.ca/en/open-access-policy-idrc-funded-project-outputs)

IDRC Open Data Statement of Principles 
[https://www.idrc.ca/en/open-data-statement-principles](https://www.idrc.ca/en/open-data-statement-principles)

IDRC Corporate Principles on Research Ethics 
[https://www.idrc.ca/en/idrcs-advisory-committee-research-ethics](https://www.idrc.ca/en/idrcs-advisory-committee-research-ethics)

IDRC’s Standard Terms and Conditions for a Grant Agreement
[https://www.idrc.ca/sites/default/files/sp/Documents%20EN/resources/idrc-general-terms-and-conditions-of-agreement.pdf](https://www.idrc.ca/sites/default/files/sp/Documents%20EN/resources/idrc-general-terms-and-conditions-of-agreement.pdf)""",
            "fr": r"""Politique de libre accès aux extrants des projets financés par le CRDI
[https://www.idrc.ca/fr/politique-de-libre-acces-aux-extrants-des-projets-finances-par-le-crdi](https://www.idrc.ca/fr/politique-de-libre-acces-aux-extrants-des-projets-finances-par-le-crdi)

Énoncé des principes des données ouvertes
[https://www.idrc.ca/fr/enonce-des-principes-des-donnees-ouvertes](https://www.idrc.ca/fr/enonce-des-principes-des-donnees-ouvertes)

Principes du CRDI en matière d’éthique de la recherche
[https://www.idrc.ca/fr/comite-consultatif-dethique-de-la-recherche-du-crdi](https://www.idrc.ca/fr/comite-consultatif-dethique-de-la-recherche-du-crdi)

Conditions générales de l’accord de subvention
[https://www.idrc.ca/sites/default/files/sp/Documents%20FR/grant_agreement_fr.pdf](https://www.idrc.ca/sites/default/files/sp/Documents%20FR/grant_agreement_fr.pdf)
""",
        },
        5,
    )

    add_question(
        section3,
        1,
        "multi-choice",
        {
            "en": """I confirm that I am aware of IDRC's applicable policies and that my institution and the scholarship recipients will have to comply with them.""",
            "fr": """Je confirme que je connais les politiques applicables du CRDI et que mon établissement et les bénéficiaires des bourses devront s’y conformer.""",
        },
        options={
            "en": [{"label": "Yes", "value": "Yes"}, {"label": "No", "value": "No"}],
            "fr": [{"label": "Oui", "value": "Yes"}, {"label": "Non", "value": "No"}],
        },
        is_required=True,
    )

    # Section 4
    en_desc = """Please submit a full three year budget with notes using the Excel template available on the IDRC public website: [https://www.idrc.ca/en/resources/guides-and-forms](https://www.idrc.ca/en/resources/guides-and-forms)
(Select the ‘Proposal budget’ and download.) 

Applications that do not submit a complete budget in this template will not be considered.
"""

    fr_desc = """Veuillez soumettre un budget triennal complet comprenant des notes en utilisant la feuille Excel qui est disponible sur le site Web public du CRDI, à la page suivante: [https://www.idrc.ca/fr/ressources/guides-et-formulaires](https://www.idrc.ca/fr/ressources/guides-et-formulaires)

Cliquez sur ‘proposition de projet’, puis téléchargez la feuille Excel. Les demandes qui ne comprennent pas un budget complet préparé au moyen de ce modèle ne seront pas prises en considération.

Insérez ce budget en tant que pièce jointe à votre demande. Dans le cas contraire, elle sera rejetée.
"""

    section4 = add_section(
        {"en": "Section IV: Budget", "fr": "Section IV: Budget"},
        {"en": en_desc, "fr": fr_desc},
        6,
    )

    add_question(
        section4,
        1,
        "file",
        {"en": "Budget", "fr": "Budget"},
        is_required=True,
        options={
            "en": {
                "accept": ".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            },
            "fr": {
                "accept": ".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            },
        },
    )


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key="spm").first()
    app_form = session.query(ApplicationForm).filter_by(event_id=event.id).first()

    questions = session.query(Question).filter_by(application_form_id=app_form.id).all()
    for q in questions:
        session.query(QuestionTranslation).filter_by(question_id=q.id).delete()
        q.depends_on_question_id = None
    session.commit()

    session.query(Question).filter_by(application_form_id=app_form.id).delete()

    sections = session.query(Section).filter_by(application_form_id=app_form.id).all()
    for s in sections:
        session.query(SectionTranslation).filter_by(section_id=s.id).delete()
    session.query(Section).filter_by(application_form_id=app_form.id).delete()
    session.commit()

    session.query(ApplicationForm).filter_by(event_id=event.id).delete()

    event = session.query(Event).filter_by(key="spm").first()
    session.query(EventTranslation).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key="spm").delete()

    session.commit()

    op.alter_column(
        "event_translation",
        "description",
        existing_type=sa.String(length=500),
        type_=sa.String(length=255),
    )

    session.commit()
