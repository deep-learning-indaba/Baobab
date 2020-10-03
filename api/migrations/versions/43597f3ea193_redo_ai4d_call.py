# -*- coding: utf-8 -*-

"""Redo AI4D First call with fixed file encoding

Revision ID: 43597f3ea193
Revises: 62c7711123a8
Create Date: 2020-08-29 16:40:31.984996

"""

# revision identifiers, used by Alembic.
revision = '43597f3ea193'
down_revision = '62c7711123a8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime
from enum import Enum

Base = declarative_base()

en_countries = [
    'Algeria',
    'Angola',
    'Benin',
    'Botswana',
    'Burkina Faso',
    'Burundi',
    'Cameroon',
    'Cape Verde',
    'Central African Republic',
    'Chad',
    'Comoros',
    'Democratic Republic of the Congo',
    'Republic of the Congo',
    'Côte d’Ivoire',
    'Djibouti',
    'Egypt',
    'Equatorial Guinea',
    'Eritrea',
    'Eswatini',
    'Ethiopia',
    'Gabon',
    'The Gambia',
    'Ghana',
    'Guinea',
    'Guinea-Bissau',
    'Kenya',
    'Lesotho',
    'Liberia',
    'Libya',
    'Madagascar',
    'Malawi',
    'Mali',
    'Mauritania',
    'Mauritius',
    'Morocco',
    'Mozambique',
    'Namibia',
    'Niger',
    'Nigeria',
    'Rwanda',
    'Sao Tome and Principe',
    'Senegal',
    'Seychelles',
    'Sierra Leone',
    'Somalia',
    'South Africa',
    'South Sudan',
    'Sudan',
    'Tanzania',
    'Togo',
    'Tunisia',
    'Uganda',
    'Zambia',
    'Zimbabwe'
]

fr_countries = [
    u'Algérie',
    u'Angola',
    u'Bénin',
    u'Botswana',
    u'Burkina Faso',
    u'Burundi',
    u'Cameroun',
    u'Cap-Vert',
    u'République centrafricaine',
    u'Tchad',
    u'Comores',
    u'République démocratique du Congo',
    u'République du Congo',
    u'Côte d’Ivoire',
    u'Djibouti',
    u'Égypte',
    u'Guinée équatoriale',
    u'Érythrée',
    u'Eswatini',
    u'Éthiopie',
    u'Gabon',
    u'Gambie',
    u'Ghana',
    u'Guinée',
    u'Guinée-Bissau',
    u'Kenya',
    u'Lesotho',
    u'Libéria',
    u'Libye',
    u'Madagascar',
    u'Malawi',
    u'Mali',
    u'Maroc',
    u'Mauritanie',
    u'île Maurice',
    u'Mozambique',
    u'Namibie',
    u'Niger',
    u'Nigeria',
    u'Rwanda',
    u'Sao Tomé-et-Principe',
    u'Sénégal',
    u'Seychelles',
    u'Sierra Leone',
    u'Somalie',
    u'Afrique du Sud',
    u'Soudan du Sud',
    u'Soudan',
    u'Tanzanie',
    u'Togo',
    u'Tunisie',
    u'Ouganda',
    u'Zambie',
    u'Zimbabwe'
]


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


class SectionTranslation(Base):
    __tablename__ = 'section_translation'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.id'), nullable=False)
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


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    event = session.query(Event).filter_by(key='prc').first()
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

    event = session.query(Event).filter_by(key='prc').first()
    session.query(EventTranslation).filter_by(event_id=event.id).delete()
    session.query(Event).filter_by(key='prc').delete()

    session.commit()

    ai4d = session.query(Organisation).filter_by(name='AI4D Africa').first()

    # Add Event
    event = Event(
        {
            'en': 'Call for Proposals for Policy Research Centres',
            'fr': u'Appel à Propositions pour les Centres de Recherche Politique'
        },
        {
            'en': 'Policy Research Centres on Artificial Intelligence for Development in Africa: Getting to responsible AI through research and policy development',
            'fr': u'Centres de Recherche sur les Politiques concernant l’intelligence artificielle (IA) pour le développement en Afrique: Vers une IA responsable grâce à la recherche et à l’élaboration de politiques'
        },
        start_date=datetime.date(2020, 11, 6),
        end_date=datetime.date(2020, 11, 6),
        key='prc',
        organisation_id=ai4d.id,
        email_from='calls@ai4d.ai',
        url='ai4d.ai',
        application_open=datetime.date(2020,9,1),
        application_close=datetime.datetime(2020,10,17,5,0,0),  # Equivalent to midnight EST
        review_open=datetime.date(2020,10,17),
        review_close=datetime.date(2020,10,30),
        selection_open=datetime.date(2020,11,1),
        selection_close=datetime.date(2020,11,6),
        offer_open=datetime.date(2020,12,31),
        offer_close=datetime.date(2020,12,31),
        registration_open=datetime.date(2020,12,31),
        registration_close=datetime.date(2020,12,31),
        event_type=EventType.CALL,
        travel_grant=False
    )

    session.add(event)
    session.commit()

    form = ApplicationForm(event.id, True, False)
    session.add(form)
    session.commit()

    def add_section(names, descriptions, order, depends_on_question_id=None, key=None, show_for_values=None):
        section = Section(form.id, order)
        session.add(section)
        session.commit()

        translations = []
        for language in names:
            translations.append(SectionTranslation(
                section.id, 
                language, 
                names[language], 
                '' if descriptions is None else descriptions[language], 
                show_for_values=None if show_for_values is None else show_for_values[language]))
        session.add_all(translations)
        session.commit()
        return section

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
                options=None if options is None else options[language],
                show_for_values=None if show_for_values is None else show_for_values[language]))
        session.add_all(translations)
        session.commit()
        return question

    en_description = """The International Development Research Centre (IDRC) and the Swedish International Development Agency (Sida) invite proposals from independent policy research organizations from across the African continent that are committed to using research to inform and influence national-level artificial intelligence (AI) policies and research ecosystems. This funding opportunity will provide funding to two (2) AI policy research organizations representing distinct linguistic regions (anglophone and francophone).

The goal of this initiative is to enable African think tanks to inform and shape policies and strategies on Artificial Intelligence to support the adoption of responsible AI on the continent, and to ensure African experts have a voice in global fora.

The call for proposals will be submitted via baobab.ai4d.ai. You will need to create an account, which will allow you to access to your application as many times as you need until you decide to submit. You will also need additional information and documentation to complete the proposal, including examples of your research and policy work and the CVs of your research team. The proposal and all requested supporting materials must be submitted through baobab.ai4d.ai no later than 23:59 EST on Oct 16, 2020.

For eligibility criteria, please see www.ai4d.ai/calls

For any queries, please email calls@ai4d.ai"""
    fr_description = u"""Le Centre de recherches pour le développement international (CRDI) et l’Agence suédoise de coopération au développement international (ASDI) invitent les organismes indépendants de recherche sur les politiques de l’ensemble du continent africain à soumettre des propositions dans la mesure où ils s’engagent à utiliser la recherche pour éclairer et influencer les politiques et les écosystèmes de recherche en matière d’intelligence artificielle à l’échelle nationale. Cette possibilité de financement permettra de financer deux (2) organismes de recherche sur les politiques d’IA représentant des régions linguistiques distinctes (anglophone et francophone).

L’objectif de cette initiative est de permettre aux think tanks africains d’éclairer et de façonner des politiques et des stratégies en matière d’intelligence artificielle afin de soutenir l’adoption d’une intelligence artificielle responsable sur le continent, et de garantir que les experts africains se feront entendre dans les forums mondiaux.

L’appel à propositions sera soumis par l’intermédiaire du site suivant : baobab.ai4d.ai. Vous devrez vous créer un compte, qui vous permettra d’accéder à votre demande aussi souvent que nécessaire jusqu’à ce que vous décidiez de la soumettre. Pour que votre proposition soit complète, vous devrez également fournir des renseignements et des documents supplémentaires, notamment des exemples de vos travaux en matière de recherche et de politiques, ainsi que les curriculums vitae des membres de votre équipe de recherche. La proposition et tous les documents à l’appui demandés doivent être soumis par l’intermédiaire du site baobab.ai4d.ai au plus tard le 16 octobre 2020, à 23 h 59 (HNE).

Pour les critères d'éligibilité, veuillez consulter www.ai4d.ai/calls

Pour toute question, veuillez envoyer un e-mail à calls@ai4d.ai"""

    # (Description Page)
    add_section({
        'en': 'Call for Proposals for Policy Research Centres',
        'fr': u'Appel à Propositions pour les Centres de Recherche Politique'
    },
    {'en': en_description, 'fr': fr_description},
    1)

    # Organisation and lead contact details
    org_section = add_section({
        'en': 'Organisation and Lead Applicant Contact details',
        'fr': u"Coordonnées de l'organisation et de la personne-ressource pour cette demande"
    }, None, 2)

    add_question(org_section, 1, 'information', {
        'en': 'Organization Information',
        'fr': u'Renseignements sur l’organisation'
    }, is_required=False)

    add_question(org_section, 2, 'short-text', {
        'en': 'Name of Organisation',
        'fr': u'Nom de l’organisation'
    }, is_required=True)

    add_question(org_section, 3, 'short-text', {
        'en': 'Director/CEO',
        'fr': u'Directeur ou premier dirigeant'
    }, is_required=True)

    add_question(org_section, 4, 'short-text', {
        'en': 'Mailing address',
        'fr': u'Adresse postale'
    }, is_required=True)

    add_question(org_section, 5, 'short-text', {
        'en': 'City',
        'fr': u'Ville'
    }, is_required=True)

    en_options = [
        {'label': c, 'value': c} for c in en_countries
    ]
    fr_options = [
        {'label': f, 'value': e} for e, f in zip(en_countries, fr_countries)
    ]

    add_question(org_section, 6, 'multi-choice', {
        'en': 'Country',
        'fr': u'Pays'
    }, 
    descriptions={
        'en': 'Eligible countries in sub-Saharan and North Africa',
        'fr': u'Pays admissibles de l’Afrique subsaharienne et de l’Afrique du Nord'
    },
    placeholders={
        'en': 'Select a Country',
        'fr': u'Choisissez un Pays'
    },
    options={
        'en': en_options,
        'fr': fr_options
    },
    is_required=True)

    add_question(org_section, 7, 'short-text', {
        'en': 'Telephone',
        'fr': u'Numéro de téléphone'
    }, is_required=True)

    add_question(org_section, 8, 'short-text', {
        'en': 'Mobile (Optional)',
        'fr': u'Numéro de téléphone mobile (facultatif)'
    }, is_required=False)

    add_question(org_section, 9, 'short-text', {
        'en': 'Email Address',
        'fr': u'Adresse de courriel'
    }, is_required=True)

    add_question(org_section, 10, 'short-text', {
        'en': 'Website',
        'fr': 'Site Web'
    }, is_required=True)

    add_question(org_section, 11, 'short-text', {
        'en': 'Social media handles',
        'fr': u'Pseudonymes sur les médias sociaux'
    }, is_required=True)

    add_question(org_section, 12, 'information', {
        'en': 'Name and contact details of principal contact for the application',
        'fr': u'Nom et coordonnées de la personne-ressource pour cette demande'
    }, is_required=False)

    add_question(org_section, 13, 'short-text', {
        'en': 'Name of principal contact',
        'fr': u'Nom du contact principal'
    }, is_required=True)

    add_question(org_section, 14, 'short-text', {
        'en': 'Email Address of principal contact',
        'fr': u'Adresse de courriel du contact principal'
    }, is_required=True)

    add_question(org_section, 15, 'short-text', {
        'en': 'Telephone/Mobile of principal contact',
        'fr': u'Numéro de téléphone ou de téléphone mobile du contact principal'
    }, is_required=True)

    # Section 1
    section1 = add_section({
        'en': 'Section 1: Organisation Experience and Capacity',
        'fr': u'Section 1: Expérience et capacités de l’organisation'
    }, None, 3)

    add_question(section1, 1, 'short-text', {
        'en': '1. How many people in total work in your organization?',
        'fr': u'1. Combien d’employés compte votre organisation en tout?'
    }, descriptions={
        'en': 'Total number of employees',
        'fr': u'Nombre total d’employés'
    },
    is_required=True)

    add_question(section1, 2, 'short-text', {
        'en': '1a. Of these, how many are full time policy researchers?',
        'fr': u'1a. Combien d’entre eux occupent un poste de chercheur en matière de politiques à temps plein?'
    }, is_required=True)

    add_question(section1, 3, 'multi-file', {
        'en': "1b. Please provide the names and CVs of your organization's principal researchers (up to five)",
        'fr': u'1b. Veuillez fournir les noms et les CV des principaux chercheurs de votre organisation (maximum de cinq)'
    }, descriptions={
        'en': 'Upload the CVs of relevant researchers in the organization here.',
        'fr': u'Téléchargez ici les CV des chercheurs concernés de votre organisation'
    }, is_required=True)

    add_question(section1, 4, 'long-text', {
        'en': '2. Mission for Responsible AI',
        'fr': u'2. Mission pour une IA responsable'
    }, descriptions={
        'en': 'Responsible AI is an approach to artificial intelligence that is inclusive, sustainable, ethical and which supports human rights. Please describe the mission of your organization as it relates to the principles of responsible AI.',
        'fr': u"L’intelligence artificielle (IA) responsable est une approche de l’IA à la fois inclusive, durable, éthique et fondée sur les droits de la personne. Veuillez décrire la mission de votre organisation par rapport aux principes de l’IA responsable."
    }, placeholders={
        'en': 'Enter up to 250 words',
        'fr': u"Entrez jusqu'à 250 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,250}$',
       'fr': r'^\s*(\S+(\s+|$)){0,250}$',
    }, validation_texts={
       'en': 'Maximum 250 words',
       'fr': 'Maximum 250 mots' 
    }, is_required=True)

    en_options = [
        'Enabling beneficial AI research and development',
        'Economic impacts, labor shifts, inequality, and technological unemployment',
        'Accountability, transparency, and explainability',
        'Surveillance, privacy, and civil liberties',
        'Fairness, ethics, and human rights',
        'Diversity and gender equality',
        'Data capacity, analytics and governance',
        'Political manipulation and computational propaganda',
        'Human dignity, autonomy, and psychological impact',
        'AI safety'
    ]

    fr_options = [
        u'Recherche-développement utile en lien avec l’IA',
        u'Répercussions économiques, mouvements de main-d’oeuvre, inégalité et chômage technologique',
        u'Responsabilité, transparence et explicabilité',
        u'Surveillance, vie privée et libertés civiles',
        u'Équité, éthique et droits de l’homme',
        u'Diversité et égalité des genres',
        u'Capacités en matière de données, d’analyses et de gouvernance',
        u'Manipulation politique et propagande virtuelle',
        u'Dignité humaine, autonomie et répercussions psychologiques',
        u'Sécurité de l’IA'
    ]

    fr_options = [
        {'label': f, 'value': e} for e, f in zip(en_options, fr_options)
    ]
    en_options = [
        {'label': o, 'value': o} for o in en_options
    ]

    add_question(section1, 5, 'multi-checkbox', {
        'en': '3. Demonstrated expertise.',
        'fr': u'3. Une expertise reconnue.'
    }, descriptions={
        'en': 'Please indicate the subject areas that your organization has experience in developing policy research and frameworks for, as they relate to artificial intelligence or any advanced technologies. Select all that apply.',
        'fr': u'Veuillez préciser les domaines dans lesquels votre organisation a acquis de l’expérience en matière de recherches et de cadres stratégiques liés à l’IA ou à d’autres technologies de pointe. Cochez toutes les réponses qui s’appliquent.'
    }, options={
        'en': en_options,
        'fr': fr_options
    }, is_required=True)

    add_question(section1, 6, 'long-text', {
        'en': '3a. Examples.',
        'fr': u'3a. Exemples.'
    }, descriptions={
        'en': 'Please provide three to five examples here that demonstrate your research and policy analysis conducted in these areas. You may provide links, or upload documents and/or PDFs at the end of the application.',
        'fr': u'Veuillez fournir trois à cinq exemples qui témoignent des recherches et des analyses des politiques que vous avez effectuées dans ces domaines. Vous pouvez fournir des liens ou télécharger des documents ou des documents PDF à la fin de la demande.'
    }, is_required=True)

    # Section 2
    section2 = add_section({
        'en': 'Section 2: Policy Research',
        'fr': u'Section 2: Recherche sur les politiques'
    }, None, 4)

    add_question(section2, 1, 'long-text', {
        'en': '1. Research background, problem statement and justification.',
        'fr': u'1. Contexte, énoncé du problème et justification'
    }, descriptions={
        'en': 'Please briefly outline what the top three priorities of your research agenda and what the key research questions will be as an AI Policy Center, and explain why you are selecting these priorities. Provide a background and review of the local context which describes these priorities within the country/region and how the focus of this project clearly links with the local needs of the country and region. It should also indicate whether others are addressing this problem and why these proposed priorities are justified, or whether the project derives some of its importance from involving research which is largely neglected.',
        'fr': u"Veuillez décrire brièvement les trois principales priorités de votre programme de recherche et les principales questions de recherche que vous aborderez en tant que centre des politiques sur l’IA, puis expliquer pourquoi vous avez sélectionné ces priorités. Donnez une vue d’ensemble et effectuez un examen du contexte local décrivant ces priorités dans le pays ou la région et expliquez le lien établi entre l’axe thématique du projet et les besoins particuliers du pays ou de la région. Vous devez également préciser s’il existe d’autres parties concernées qui se penchent sur le problème énoncé, les raisons justifiant les priorités proposées, et si l’importance du projet tient au fait qu’il porte sur un sujet de recherche grandement négligé"
    }, placeholders={
        'en': 'Enter up to 1000 words',
        'fr': u"Entrez jusqu'à 1000 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,1000}$',
       'fr': r'^\s*(\S+(\s+|$)){0,1000}$',
    }, validation_texts={
       'en': 'Maximum 1000 words',
       'fr': 'Maximum 1000 mots' 
    }, is_required=True)

    add_question(section2, 2, 'long-text', {
        'en': '2. General and specific objectives.',
        'fr': u'2. Objectifs généraux et précis.'
    }, descriptions={
        'en': 'The general objective should state the development goal being pursued by the research. The specific objectives should indicate the specific types of knowledge to be produced, the audiences to be reached, and forms of capacity to be reinforced. These are the objectives against which the success of the project will be judged. Use only active verbs (no passive). Typical objectives focus on 1) deepening understanding of a topic through research; 2) influencing policy and practice; and 3) building capacity.',
        'fr': u"L’objectif général correspond à l’objectif de développement que l’on souhaite atteindre au moyen de la recherche. Les objectifs particuliers doivent signaler les types précis de connaissances recherchées, les destinataires et les capacités à renforcer. C’est en fonction de ces objectifs que sera jaugée la réussite du projet. Utilisez seulement des verbes d’action (évitez les verbes d’état). En règle générale, les objectifs permettent : 1) de comprendre un sujet en profondeur grâce à la recherche; 2) d’influencer les politiques et les pratiques; et 3) de favoriser le renforcement des capacités."
    }, placeholders={
        'en': 'Enter up to 250 words',
        'fr': u"Entrez jusqu'à 250 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,250}$',
       'fr': r'^\s*(\S+(\s+|$)){0,250}$',
    }, validation_texts={
       'en': 'Maximum 250 words',
       'fr': 'Maximum 250 mots' 
    }, is_required=True)

    add_question(section2, 3, 'information', {
        'en': '3. Methodology and approach.',
        'fr': u'3. Méthodologie et approche.'
    }, is_required=False)

    add_question(section2, 4, 'long-text', {
        'en': '3a. Approach.',
        'fr': u'3a. Approche.'
    }, descriptions={
        'en': 'Briefly describe the overall approach/logic/pathway to achieve the above objectives.',
        'fr': u"Décrivez brièvement l’approche, la logique ou le cheminement permettant d’atteindre les objectifs mentionnés précédemment."
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section2, 5, 'long-text', {
        'en': '3b. Policy research.',
        'fr': u'3b. Recherche sur les politiques.'
    }, descriptions={
        'en': 'How will you answer the proposed research questions in the most rigorous way possible? This includes conceptual and theoretical frameworks, user participation, data collection and analysis.',
        'fr': u"Comment comptez-vous répondre aux questions de recherche proposées de la façon la plus rigoureuse possible ? Veuillez notamment fournir des précisions à l’égard des cadres conceptuels et théoriques, de la participation des utilisateurs, et de la collecte et de l’analyse des données."
    }, placeholders={
        'en': 'Enter up to 750 words',
        'fr': u"Entrez jusqu'à 750 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,750}$',
       'fr': r'^\s*(\S+(\s+|$)){0,750}$',
    }, validation_texts={
       'en': 'Maximum 750 words',
       'fr': 'Maximum 750 mots' 
    }, is_required=True)

    add_question(section2, 6, 'long-text', {
        'en': '3c. Gender and inclusion.',
        'fr': u'3c. Sexospécificité et inclusion.'
    }, descriptions={
        'en': """i. How has your organization addressed gender-equality and other kinds of inclusion and diversity dimensions [socioeconomic, political, cultural, ethnic] in its policy research? 
    ii. How do you anticipate this will improve with this AI4D support? 
    iii. Please give a brief explanation of your strategy with gender, inclusion and diversity related issues as it relates to AI/advanced technologies and offer examples of the research work. 

Please provide examples [PDF or links] to material that demonstrates your strategy and research on gender, inclusion and diversity. You may upload supporting documents at the end of the application. """,
        'fr': u"""i. Comment votre organisation a-t-elle tenu compte de l’égalité des genres et d’autres dimensions (p. ex. socio-économiques, politiques, culturelles, ethniques) liées à l’inclusion et à la diversité dans sa recherche sur les politiques?
ii. Dans quelle mesure pensez-vous que ces éléments s’amélioreront grâce au soutien de l’initiative Intelligence artificielle pour le développement (IAPD) ? 
iii. Veuillez expliquer brièvement votre stratégie en ce qui a trait aux questions liées à la sexospécificité, à l’inclusion et à la diversité, ainsi qu’à l’IA et aux technologies de pointe, et fournir des exemples de travaux de recherche.

Veuillez fournir des exemples (c.-à-d. des documents en format PDF, ou des liens menant vers des fichiers) qui démontrent votre stratégie et vos recherches sur la sexospécificité, l’inclusion et la diversité.
"""
    }, placeholders={
        'en': 'Enter up to 750 words',
        'fr': u"Entrez jusqu'à 750 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,750}$',
       'fr': r'^\s*(\S+(\s+|$)){0,750}$',
    }, validation_texts={
       'en': 'Maximum 750 words',
       'fr': 'Maximum 750 mots' 
    }, is_required=True)

    add_question(section2, 7, 'long-text', {
        'en': '3d. Ethical considerations.',
        'fr': u'3d. Considérations d’ordre éthique.'
    }, descriptions={
        'en': 'All projects that include human subjects must ensure that their privacy, dignity, and integrity are protected. An independent ethical review committee must approve the protocols. Please describe the key ethical considerations for the proposed research and the research ethics protocols your organization uses.',
        'fr': u"Dans le cadre de tout projet de recherche portant sur des sujets humains, il faut garantir la protection de la vie privée, de la dignité et de l’intégrité de la personne. Un comité d’éthique indépendant doit autoriser les protocoles. Veuillez décrire les principales considérations d’ordre éthique pour la recherche proposée, ainsi que les protocoles d’éthique de la recherche utilisés par votre organisation."
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section2, 8, 'long-text', {
        'en': '4. Capacity development.',
        'fr': u'4. Développement des capacités.'
    }, descriptions={
        'en': 'In terms of developing capacity, how would your organization use this grant to advance the capacity of your research team in any of the above subject areas? What would you need to do to build capacity to improve your work and outcomes to advance responsible artificial intelligence in your country/region?',
        'fr': u"En matière de développement des capacités, comment votre organisation utiliserait-elle cette subvention pour renforcer les capacités de votre équipe de recherche dans l’un des domaines susmentionnés ? Que devriez- vous faire pour renforcer vos capacités, améliorer la qualité de votre travail, obtenir de meilleurs résultats, et faire progresser l’IA responsable dans votre pays ou votre région?"
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section2, 9, 'long-text', {
        'en': '5. Communicating for influence.',
        'fr': u'5. Communication en vue d’exercer une influence.'
    }, descriptions={
        'en': 'Please provide a description of your intended research communications strategy to influence policy in the context of this AI4D Africa funding.',
        'fr': u"Veuillez fournir une description de la stratégie de communication que vous comptez adopter dans le cadre de votre recherche pour exercer une influence sur les politiques, grâce à ce financement de l’initiative IAPD Afrique."
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section2, 10, 'long-text', {
        'en': '6. Results.',
        'fr': u'6. Résultats.'
    }, descriptions={
        'en': 'Please describe what success will look like at the end of the three years. What markers will you use to gauge your success in AI4D policy and research? What are your expected research outputs and outcomes?',
        'fr': u"Veuillez décrire ce à quoi ressemblera la réussite à la fin de la période de trois années. Quels marqueurs utiliserez-vous pour évaluer votre réussite pour les politiques et les recherches liées à l’initiative IAPD Afrique? Quels sont les résultats escomptés de votre recherche?"
    }, placeholders={
        'en': 'Enter up to 500 words',
        'fr': u"Entrez jusqu'à 500 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,500}$',
       'fr': r'^\s*(\S+(\s+|$)){0,500}$',
    }, validation_texts={
       'en': 'Maximum 500 words',
       'fr': 'Maximum 500 mots' 
    }, is_required=True)

    add_question(section2, 11, 'long-text', {
        'en': '7. Project schedule.',
        'fr': u'7. Calendrier du projet.'
    }, descriptions={
        'en': 'Please provide a draft schedule for how you envision the activities will be organized according to the specific objectives of the project. The project schedule should include a list of key outputs and milestones (key events or deliverables). These need to be related to the items included in the project budget (Section 4).',
        'fr': u"Veuillez fournir un calendrier provisoire pour expliquer la façon dont vous comptez organiser les activités, compte tenu des objectifs spécifiques du projet. Le calendrier du projet doit comprendre une liste des principaux extrants et jalons (événements ou produits livrables clés). Ils doivent être liés aux éléments qui figurent dans le budget du projet (section 4)."
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section2, 12, 'multi-file', {
        'en': '8. Supplemental documentation (optional).',
        'fr': u'8. Documents supplémentaires (facultatifs).'
    }, descriptions={
        'en': 'Attach any supplemental documentation that will help clarify your application (e.g., Theory of Change, supporting graphics)',
        'fr': u"Veuillez joindre toute documentation supplémentaire qui aidera à clarifier votre demande (p. ex. théorie du changement, graphiques à l’appui)."
    }, is_required=False)

    # Section 3
    section3 = add_section({
        'en': 'Section 3: Policy engagement experience',
        'fr': u'Section 3: Expérience en matière d’interaction avec la sphère des politiques'
    }, None, 5)

    add_question(section3, 1, 'long-text', {
        'en': '1. Please describe the kinds of engagement your organization has had with national governing institutions (e.g. government departments, bodies and agencies, commissions, parliaments, regulators, and other public-sector institutions) on any of the above topics (from Section 1, question 3)? This can include a reflection on what you have done well with communications, and what you have done not so well.',
        'fr': u'Veuillez décrire les types d’interactions que votre organisation a eus avec des institutions gouvernementales nationales (p. ex. ministères et organismes gouvernementaux, commissions, parlements, organismes de réglementation et autres institutions du secteur public) en ce qui concerne les sujets susmentionnés (à la section 1, question 3). Vous pouvez notamment faire part de vos réflexions sur ce que vous avez bien fait en matière de communication, ainsi que sur les éléments que vous devez améliorer.'
    }, descriptions={
        'en': 'Please give up to three examples of this engagement, such as requests for input, sitting on policy steering committees and meetings with policy makers.',
        'fr': u'Veuillez fournir un maximum de trois exemples de ces interactions (p. ex. demandes de consultation, participation à des comités directeurs, réunions avec des décideurs politiques).'
    }, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    add_question(section3, 2, 'long-text', {
        'en': '2. Describe and give examples of how your research has informed public debate or policy processes nationally and/or regionally. ',
        'fr': u'Décrivez votre recherche et donnez des exemples de la façon dont elle a exercé une influence sur le débat public ou les processus politiques à l’échelle nationale ou régionale.'
    }, descriptions=None, placeholders={
        'en': 'Enter up to 350 words',
        'fr': u"Entrez jusqu'à 350 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,350}$',
       'fr': r'^\s*(\S+(\s+|$)){0,350}$',
    }, validation_texts={
       'en': 'Maximum 350 words',
       'fr': 'Maximum 350 mots' 
    }, is_required=True)

    q3 = add_question(section3, 3, 'multi-choice', {
        'en': '3. Does your organization also work regionally and/or globally on technology policy related issues?',
        'fr': u'3. Votre organisation travaille-t-elle aussi sur des questions liées aux politiques technologiques à l’échelle régionale ou mondiale?'
    }, options={
        'en': [{'label': 'Yes', 'value': 'Yes'}, {'label': 'No', 'value': 'No'}],
        'fr': [{'label': 'Oui', 'value': 'Yes'}, {'label': 'Non', 'value': 'No'}]
    }, is_required=True)

    add_question(section3, 4, 'long-text', {
        'en': '3a. If yes, please describe this engagement. List any regional and global networks/association memberships if appropriate.',
        'fr': u'3a. Si oui, veuillez décrire la nature de ces travaux. Dressez une liste des associations ou des réseaux auxquels vous appartenez à l’échelle régionale et mondiale, le cas échéant.'
    }, descriptions=None, placeholders={
        'en': 'Enter up to 250 words',
        'fr': u"Entrez jusqu'à 250 mots" 
    }, validation_regexs={
       'en': r'^\s*(\S+(\s+|$)){0,250}$',
       'fr': r'^\s*(\S+(\s+|$)){0,250}$',
    }, validation_texts={
       'en': 'Maximum 250 words',
       'fr': 'Maximum 250 mots' 
    }, is_required=True, depends_on_question_id=q3.id, show_for_values={
        'en': 'Yes',
        'fr': 'Yes'
    })

    # Section 4
    en_desc = """Please submit a full three year budget with notes using the Excel sheet available on the IDRC public website: https://www.idrc.ca/en/resources/guides-and-forms
 
Select the ‘Proposal budget’ and download the Excel sheet. Applications that do not submit a complete budget in the above template will not be considered. 

Submit this budget as an attachment at the end of this proposal. Failure to do this will disqualify your application. 
"""

    fr_desc = u"""Veuillez soumettre un budget triennal complet comprenant des notes en utilisant la feuille Excel qui est disponible sur le site Web public du CRDI, à la page suivante: https://www.idrc.ca/fr/ressources/guides-et-formulaires

Cliquez sur ‘proposition de projet’, puis téléchargez la feuille Excel. Les demandes qui ne comprennent pas un budget complet préparé au moyen de ce modèle ne seront pas prises en considération.

Insérez ce budget en tant que pièce jointe à votre demande. Dans le cas contraire, elle sera rejetée.
"""

    section4 = add_section({
        'en': 'Section 4: Budget',
        'fr': 'Section 4: Budget'
    }, {
        'en': en_desc,
        'fr': fr_desc
    }, 6)

    add_question(section4, 1, 'file', {
        'en': 'Budget',
        'fr': 'Budget'
    }, is_required=True, options={
        'en': {"accept": ".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"},
        'fr': {"accept": ".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"},
    })


def downgrade():
    # No practical way to back out of this really
    pass
