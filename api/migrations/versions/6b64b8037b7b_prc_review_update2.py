# -*- coding: utf-8 -*-

"""AI4D PRC Review Update 2

Revision ID: 6b64b8037b7b
Revises: 111c4f9eab84
Create Date: 2020-11-15 17:01:18.729605

"""

# revision identifiers, used by Alembic.
revision = '6b64b8037b7b'
down_revision = '111c4f9eab84'

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

class ReviewForm(Base):
    __tablename__ = 'review_form'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    application_form = db.relationship('ApplicationForm', foreign_keys=[application_form_id])
    review_questions = db.relationship('ReviewQuestion')

    def __init__(self, application_form_id, deadline):
        self.application_form_id = application_form_id
        self.is_open = True
        self.deadline = deadline

    def close(self):
        self.is_open = False


class ReviewQuestion(Base):
    __tablename__ = 'review_question'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    question_id = db.Column(db.Integer(), db.ForeignKey('question.id'), nullable=True)
    
    type = db.Column(db.String(), nullable=False)
    
    is_required = db.Column(db.Boolean(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    weight = db.Column(db.Float(), nullable=False)
    review_form = db.relationship('ReviewForm', foreign_keys=[review_form_id])
    question = db.relationship('Question', foreign_keys=[question_id])

    translations = db.relationship('ReviewQuestionTranslation', lazy='dynamic')

    def __init__(self,
                 review_form_id,
                 question_id,
                 type,
                 is_required,
                 order,
                 weight):
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
    __tablename__ = 'review_question_translation'
    __table_args__ = {'extend_existing': True}
    __table_args__ = tuple([db.UniqueConstraint('review_question_id', 'language', name='uq_review_question_id_language')])

    id = db.Column(db.Integer(), primary_key=True)
    review_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)

    description = db.Column(db.String(), nullable=True)
    headline = db.Column(db.String(), nullable=True)
    placeholder = db.Column(db.String(), nullable=True)
    options = db.Column(db.JSON(), nullable=True)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)

    def __init__(self, 
                 review_question_id,
                 language, 
                 description=None, 
                 headline=None, 
                 placeholder=None, 
                 options=None, 
                 validation_regex=None, 
                 validation_text=None):
        self.review_question_id = review_question_id
        self.language = language
        self.description = description
        self.headline = headline
        self.placeholder = placeholder
        self.options = options
        self.validation_regex = validation_regex
        self.validation_text = validation_text

class ReviewConfiguration(Base):
    __tablename__ = 'review_configuration'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    num_reviews_required = db.Column(db.Integer(), nullable=False)
    num_optional_reviews = db.Column(db.Integer(), nullable=False)
    drop_optional_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=True)
    drop_optional_agreement_values = db.Column(db.String(), nullable=True)

class ReviewScore(Base):
    __tablename__ = 'review_score'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    review_response_id = db.Column(db.Integer(), db.ForeignKey('review_response.id'), nullable=False)
    review_question_id = db.Column(db.Integer(), db.ForeignKey('review_question.id'), nullable=False)
    value = db.Column(db.String(), nullable=False)

    def __init__(self,
                 review_question_id,
                 value):
        self.review_question_id = review_question_id
        self.value = value

class ReviewResponse(Base):
    __tablename__ = 'review_response'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    review_form_id = db.Column(db.Integer(), db.ForeignKey('review_form.id'), nullable=False)
    reviewer_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    response_id = db.Column(db.Integer(), db.ForeignKey('response.id'), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    is_submitted = db.Column(db.Boolean(), nullable=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)

    def __init__(self,
                 review_form_id,
                 reviewer_user_id,
                 response_id,
                 language):
        self.review_form_id = review_form_id
        self.reviewer_user_id = reviewer_user_id
        self.response_id = response_id
        self.language = language
        self.is_submitted = False

    def submit(self):
        self.is_submitted = True
        self.submitted_timestamp = datetime.now()

current_order = 1

def add_question(review_form_id, type, is_required, weight=0, question_id=None, 
                 descriptions=None, headlines=None, placeholders=None, options=None, 
                 validation_regexs=None, validation_texts=None):
    global current_order
    question = ReviewQuestion(review_form_id, question_id, type, is_required, current_order, weight)
    db.session.add(question)
    db.session.commit()
    en = ReviewQuestionTranslation(
        question.id, 
        'en', 
        None if descriptions is None else descriptions['en'],
        None if headlines is None else headlines['en'],
        None if placeholders is None else placeholders['en'],
        None if options is None else options['en'],
        None if validation_regexs is None else validation_regexs['en'],
        None if validation_texts is None else validation_texts['en'])
    fr = ReviewQuestionTranslation(
        question.id, 
        'fr', 
        None if descriptions is None else descriptions['fr'],
        None if headlines is None else headlines['fr'],
        None if placeholders is None else placeholders['fr'],
        None if options is None else options['fr'],
        None if validation_regexs is None else validation_regexs['fr'],
        None if validation_texts is None else validation_texts['fr'])
    db.session.add_all([en, fr])
    db.session.commit()

    current_order += 1

    return question, en, fr

def get_question(application_form_id, en_headline):
    en = (db.session.query(QuestionTranslation)
            .filter_by(language='en', headline=en_headline)
            .join(Question, QuestionTranslation.question_id == Question.id)
            .filter_by(application_form_id=application_form_id)
            .first())
    fr = db.session.query(QuestionTranslation).filter_by(language='fr', question_id=en.question_id).first()
    return en.question, en, fr

def add_evaluation_question(form_id, headlines, descriptions, min_score, max_score):
    validation_regex = '^({})$'.format('|'.join([str(i) for i in range(max_score, min_score-1, -1)]))
    validation_text = {
        'en': 'Enter a number between {} and {}'.format(min_score, max_score),
        'fr': 'Entrez un nombre entre {} et {}'.format(min_score, max_score)
    }
    placeholders = {
        'en': 'Enter a score between {} and {}'.format(min_score, max_score),
        'fr': 'Saisissez un score compris entre {} et {}'.format(min_score, max_score)
    }
    return add_question(form_id, 'short-text', True, 1, headlines=headlines, 
            descriptions=descriptions, validation_regexs={'en': validation_regex, 'fr': validation_regex}, 
            validation_texts=validation_text, placeholders=placeholders)

def add_comment_question(form_id, headlines, descriptions, is_required=False):
    return add_question(form_id, 'long-text', is_required, weight=1, descriptions=descriptions, headlines=headlines)

def add_information_question(form_id, application_form_id, en_headline, type='information', heading_override=False, description_override=None):
    question, en, fr = get_question(application_form_id, en_headline)
    
    headlines = {
        'en': None if heading_override else en.headline,
        'fr': None if heading_override else fr.headline
    }
    descriptions = {
        'en': description_override['en'] if description_override is not None else en.description,
        'fr': description_override['fr'] if description_override is not None else fr.description
    }

    if question.type == 'information':
        return add_heading(form_id, headlines)

    return add_question(form_id, type, False, question_id=question.id, headlines=headlines, descriptions=descriptions)

def add_heading(form_id, headlines):
    return add_question(form_id, 'heading', False, headlines=headlines)

def add_divider(form_id, headlines, descriptions):
    return add_question(form_id, 'section-divider', False, headlines=headlines, descriptions=descriptions)

def upgrade():
    print('Starting 6b64b8037b7b')
    event = db.session.query(Event).filter_by(key='prc').first()
    application_form = db.session.query(ApplicationForm).filter_by(event_id=event.id).first()
    form = db.session.query(ReviewForm).filter_by(application_form_id=application_form.id).first()

    questions = db.session.query(ReviewQuestion).filter_by(review_form_id=form.id).all()

    for q in questions:
        db.session.query(ReviewQuestionTranslation).filter_by(review_question_id=q.id).delete()
        db.session.query(ReviewScore).filter_by(review_question_id=q.id).delete()
    db.session.commit()

    db.session.query(ReviewQuestion).filter_by(review_form_id=form.id).delete()
    db.session.commit()

    # db.session.query(ReviewResponse).filter_by(review_form_id=form.id).delete()

    print('Removed existing form, repopulating...')

    # Set up questions
    

    divider1 = add_question(form.id, 'section-divider', False, headlines={
        'en': 'Evaluation of proposals',
        'fr': 'Évaluation des propositions'
    }, descriptions={
        'en': """Below are a series of weighted, multiple choice questions intended to evaluate the applicant’s proposal. The evaluation is divided up into the sections from the application: 
    I. Organization capacity and experience; 
    II. Policy research; 
    III. Policy engagement experience; and 
    IV. Budget, followed by section 
    V. Overall Assessment. 
At the end of each question and/or section, please reflect in your own words what you think of the answers in that section. Each evaluation question corresponds with the section and numbered question in the proposal.
""",
        'fr': """Vous trouverez ci-dessous une série de questions à choix multiples pondérées destinées à évaluer la proposition du candidat. L’évaluation est divisée en plusieurs sections à partir de la candidature: 
    I. Capacité et expérience de l’organisation; 
    II. Recherche sur les politiques;
    III. Expérience en matière d’engagement politique; et 
    IV. Budget, suivi par la section 
    V. Évaluation globale. 
À la fin de chaque question et/ou section, veuillez exprimer dans vos propres mots ce que vous pensez des réponses de cette section. Chaque question d'évaluation correspond à la section et à la question numérotée dans la proposition.
"""
    })

    divider2 = add_question(form.id, 'section-divider', False, headlines={
        'en': 'Section I: Organization capacity and experience',
        'fr': 'Section I: Capacité et expérience de l’organisation'
    }, descriptions={
        'en': """Please review and evaluate the applicant’s answers on organizational capacity, experience and mission.
\[Total possible points = 55\]

Evaluation criteria:
    - Research team has the necessary expertise and partners to conduct the activities and research proposed.
    - Experience/years of working on AI policy, or related issues (such as ICTs, digital/big/open data, communications, cyber policy issues - particularly as they pertain to human development and human rights issues - but also infrastructure, capacity-skills), with significant achievements.
    - Fit between proposed research agenda and the organization’s mission.
    - Demonstrated research quality (output, citations, research metrics) that addresses numerous facets of advanced technology policy. Please see the [Research Quality Plus](https://www.idrc.ca/en/research-in-action/research-quality-plus) assessment instrument for guidance.
""",
        'fr': """Veuillez examiner et évaluer les réponses du candidat sur la capacité organisationnelle, l’expérience et la mission.
\[Total des points possibles = 55\]

Critères d’évaluation:
    - L’équipe de recherche dispose de l’expertise et des partenaires nécessaires pour mener les activités et les recherches proposées.
    - Expérience/années de travail sur la politique d’IA, ou sur des questions connexes (telles que les TIC, les données numériques/grandes/ouvertes, les communications, les questions de cyberpolitique - en particulier en ce qui concerne le développement humain et les droits de l’homme - mais aussi les infrastructures, les capacités/compétences), avec des réalisations significatives.
    - Adéquation entre le programme de recherche proposé et la mission de l’organisation.
    - Qualité démontrée de la recherche (résultats, citations, paramètres de recherche) qui aborde de nombreuses facettes de la politique en matière de technologies avancées. Veuillez consulter l’instrument d’évaluation [Qualité de la recherche plus](https://idl-bnc-idrc.dspacedirect.org/bitstream/handle/10625/56600/IDL-56600.pdf?sequence=2&amp;isAllowed=y) pour obtenir des conseils.
"""
    })

    add_information_question(form.id, form.application_form_id, '1. Organizational capacity and experience')
    add_information_question(form.id, form.application_form_id, 'How many people in total work in your organization?')
    add_information_question(form.id, form.application_form_id, 'Of these, how many are full time policy researchers?')
    add_information_question(form.id, form.application_form_id, "Please provide the names and CVs of your organization's principal researchers (up to five)", 'multi-file')

    review_q1 = add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please review the makeup of the organization in terms of staffing and answer the following question.

Assessment of research team: After reviewing the CVs of the principal researchers, assess the strength of the research team with respect to achieving the goals and strategy of the proposed research agenda. 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Research team is insufficient and would need expansion and development
4 - 7 : Research team is adequate but needs some broad capacity development
8 - 10 : Research team is strong (although they might still benefit from limited capacity development)
""",
        'fr': """Évaluation de l’équipe de recherche: Après avoir examiné les CV des principaux chercheurs, évaluez la force de l’équipe de recherche en ce qui concerne la réalisation des objectifs et de la stratégie du programme de recherche proposé. 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : L’équipe de recherche est insuffisante et aurait besoin d’être agrandie et développée
4 - 7 : L’équipe de recherche est adéquate mais a besoin d’un large développement des capacités
8 - 10 : L’équipe de recherche est solide (bien qu’elle puisse encore bénéficier d’un développement limité des capacités)
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id,form.application_form_id,  '2. Mission for Responsible AI')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does this mission statement of the organization relate to advancing the principles of responsible AI? 
\[Total possible points = 15\]

**Scale:**
0 - 5 : Limited demonstration of mission and the significance
6 - 10 : Somewhat demonstrates mission and the significance
11 - 15 : Superior demonstration of mission and the significance
""",
        'fr': """Dans quelle mesure cette déclaration de mission de l’organisation est-elle liée à la promotion des
principes de l’IA responsable? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Démonstration limitée de la mission et de sa signification
6 - 10 : Démontre quelque peu la mission et la signification
11 - 15 : Démonstration supérieure de la mission et de sa signification
"""
    }, min_score=0, max_score=15)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '3. Demonstrated expertise')
    add_information_question(form.id, form.application_form_id, 'Examples')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant demonstrate knowledge and expertise with at least three of the key research areas? 
\[Total possible points = 15\]

**Scale:**
0 - 5 : Limited demonstrated knowledge and expertise
6 - 10 : Some demonstrated knowledge and expertise in at least two areas
11 - 15 : Superior/significant demonstrated knowledge and expertise in three areas
""",
        'fr': """Dans quelle mesure le candidat démontre-t-il des connaissances et une expertise dans au moins trois des principaux domaines de recherche? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Connaissances et compétences démontrées limitées
6 - 10 : Certains aspects font preuve de connaissances et d’expertise dans au moins deux domaines
11 - 15 : Connaissances et expertise supérieures/significatives démontrées dans trois domaines
"""
    }, min_score=0, max_score=15)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please review the examples provided by the applicant from the organization’s research portfolio. Based on what they’ve written and provided, to what extent does the organization demonstrate an ability to produce high quality policy research on these issues? 
\[Total possible points = 15\]
*High quality research is relevant, shows integrity, legitimacy, importance (originality) and is well positioned for use. Please refer to the [Research Quality Plus](https://www.idrc.ca/en/research-in-action/research-quality-plus) assessment instrument if you have questions.*

**Scale:**
0 - 5 : Limited track record of producing high quality research
6 - 10 : Demonstrates variable research quality with some high-quality research
11 - 15 : Significant experience producing high quality research
""",
        'fr': """Veuillez examiner les exemples fournis par le candidat à partir du portefeuille de recherche de l’organisme. Sur la base de ce qu’ils ont écrit et fourni, dans quelle mesure l’organisme démontre-t-il sa capacité à produire des recherches politiques de haute qualité sur ces questions? 
\[Total des points possibles = 15\]

Une recherche de haute qualité est pertinente, fait preuve d’intégrité, de légitimité, d’importance (originalité) et est bien placée pour être utilisée. Veuillez-vous référer à l’instrument d’évaluation [Qualité de la recherche plus](https://idl-bnc-idrc.dspacedirect.org/bitstream/handle/10625/56600/IDL-56600.pdf?sequence=2&amp;isAllowed=y) si vous avez des questions.

**Scale:**
0 - 5 : Expérience limitée dans la production de recherches de haute qualité
6 - 10 : Démontre une qualité de recherche variable avec quelques recherches de haute qualité
11 - 15 : Une expérience significative dans la production de recherches de haute qualité
"""
    }, min_score=0, max_score=15)
    
    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    print('Finished configuring Section I')

    add_divider(form.id, {
        'en': 'Section II: Policy Research',
        'fr': 'Section II: Recherche sur les politiques'
    }, {
        'en': """Please review and evaluate the applicant’s answers on their research, objectives and methodologies.
\[Total possible points = 135\]

Evaluation criteria, proposals must demonstrate:
    - A clear understanding of and justification for the top research priorities, and how the research priorities are relevant to the themes of this call.
    - Clearly articulated objectives that are relevant and feasible, and a strong justification for the proposed approach, methodology and techniques.
    - Overall logic of the proposed methodology must be sound and appropriate for the given objectives, and demonstrate a multidisciplinary approach to the research.
    - A clear articulation of how the proposed approaches and interventions are appropriate and relevant to research users.
    - Strong considerations of gender and inclusion in research design, questions, strategies to reduce bias, and ensure an inclusive approach. This is critical for the 45% proposal overall, and a poorly articulated gender and inclusion strategy will impact the score of the application.
    - A clear articulation of the ethical considerations of the research. Evidence that structures and systems, including ethics boards, are in place to deal with ethical, legal, and socio-economic implications of proposed research, and that proposed approaches demonstrate strategies for oversight that are rights-based, ethical, inclusive and sustainable.
    - Clear and coherent focus on capacity development.
    - Clear communications strategy to extend the impact of the research and results.
    - Clear articulation of results and the metrics to gauge them.
    - Clear and appropriate project management plan that is tied to budget.
""",
        'fr': """Veuillez examiner et évaluer les réponses des candidats sur leurs recherches, leurs objectifs et leurs méthodologies.
\[Total des points possibles = 135\]

Critères d’évaluation: Les propositions doivent démontrer :
    - Une compréhension claire et une justification des principales priorités de recherche, ainsi que de la pertinence de ces priorités par rapport aux thèmes du présent appel.
    - Des objectifs clairement articulés, pertinents et réalisables, et une justification solide de l’approche, de la méthodologie et des techniques proposées.
    - La logique générale de la méthodologie proposée doit être solide et appropriée aux objectifs donnés, et démontrer une approche multidisciplinaire de la recherche.
    - Une articulation claire de la façon dont les approches et les interventions proposées sont appropriées et pertinentes pour les utilisateurs de la recherche.
    - De solides considérations sur le genre et l’inclusion dans la conception de la recherche, les questions, les stratégies pour réduire les préjugés et assurer une approche inclusive. Ceci est essentiel pour la proposition de 45% dans son ensemble, et une stratégie mal articulée en matière de genre et d’inclusion aura un impact sur la note de la demande.
    - Une articulation claire des considérations éthiques de la recherche. La preuve que des structures et des systèmes, y compris des comités d’éthique, sont en place pour traiter les implications éthiques, juridiques et socio-économiques de la recherche proposée, et que les approches proposées font preuve de stratégies de surveillance qui sont fondées sur les droits, éthiques, inclusives et durables.
    - Une attention claire et cohérente portée au développement des capacités.
    - Une stratégie de communication claire pour étendre l’impact de la recherche et des résultats.
    - Une articulation claire des résultats et des mesures permettant de les évaluer.
    - Un plan de gestion de projet clair et approprié qui est lié au budget.
"""
    })

    add_information_question(form.id, form.application_form_id, '1. Research background, problem statement and justification')
    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant clearly articulate why these priorities are significant for the AI4D research agenda of the organization and the contexts in which they work? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : No or limited clarity of research priorities
4 - 7 : Substantive clarity of research priorities
8 - 10 : Superior/significant clarity of research priorities
""",
        'fr': """Dans quelle mesure le candidat explique-t-il clairement pourquoi ces priorités sont importantes pour l’agenda de recherche IAPD de l’organisation et les contextes dans lesquels elles s’inscrivent? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Clarté des priorités de recherche nulle ou limitée
4 - 7 : Clarté de fond des priorités de recherche
8 - 10 : Clarté supérieure des priorités de recherche
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant demonstrate the ability to draw upon evidence to support the background, context and arguments for why these are the priorities for their research? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : No or limited demonstrated ability
4 - 7 : Substantive demonstrated ability
8 - 10 : Superior/significant demonstrated ability
""",
        'fr': """Dans quelle mesure le candidat démontre-t-il sa capacité à s’appuyer sur des preuves pour étayer le contexte et les arguments qui expliquent pourquoi il s’agit là des priorités de sa recherche? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Pas ou peu de capacité démontrée
4 - 7 : Capacité démontrée
8 - 10 : Capacité démontrée supérieure
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant demonstrate the ability to write on complex issues succinctly and intelligently? 
\[Total possible points = 5\]

**Scale:**
0 - 1 : Limited ability to write on complex issues (confusing, lacks logical flow and coherence)
2 - 3 : Some ability to write on complex issues (some good ideas, structure may lack coherence)
4 - 5 : Superior/significant ability to write on complex issues (exceptionally clear and coherent)
""",
        'fr': """Dans quelle mesure le candidat démontre-t-il sa capacité à écrire sur des questions complexes de manière succincte et intelligente? 
\[Total des points possibles = 5\]

Scale: 
0 - 1 : Capacité limitée à écrire sur des sujets complexes (confus, manque de logique et de cohérence)
2 - 3 : Une certaine capacité à écrire sur des questions complexes (quelques bonnes idées, la structure peut manquer de cohérence)
4 - 5 : Capacité supérieure à rédiger sur des questions complexes (exceptionnellement clair et cohérent)
"""
    }, min_score=0, max_score=5)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '2. General and specific objectives')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent are the general and specific objectives appropriate and logically connected to problem statement and justification? Are they feasible? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Poorly articulated and not connected with problem statement, inappropriate and/or infeasible objectives
4 - 7 : Objectives need improvement, but are relatively appropriate and connected to problem statement
8 - 10 : Objectives are coherent, flow logically, and are appropriate and feasible
""",
        'fr': """Dans quelle mesure les objectifs généraux et spécifiques sont-ils appropriés et logiquement liés à l’énoncé et à la justification du problème? Sont-ils réalisables? 
\[Total des points possibles = 10\]

**Scale:** 
0 - 3 : Mal articulé et sans lien avec l’énoncé du problème, objectifs inappropriés et/ou irréalisables
4 - 7 : Les objectifs doivent être améliorés, mais ils sont relativement appropriés et liés à l’énoncé du problème
8 - 10 : Les objectifs sont cohérents et logiques, et sont appropriés et réalisables
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '3. Methodology and approach')
    add_information_question(form.id, form.application_form_id, 'Approach')
    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate a coherent approach to achieving their research objectives? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Little demonstrated coherence
4 - 7 : Some demonstrated coherence
8 - 10 : Significant demonstrated coherence
""",
        'fr': """Dans quelle mesure l’organisme fait-il preuve d’une approche cohérente pour atteindre ses objectifs de recherche? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Peu de cohérence démontrée
4 - 7 : Certains aspects font preuve de cohérence
8 - 10 : Démontre une cohérence significative
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, 'Policy research')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent is the conceptual and theoretical framework appropriate to the research question at hand? How well is the framework linked to the proposed research design? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Little demonstrated strategy in linking framework to research design
4 - 7 : Some demonstrated strategy in linking framework to research design
8 - 10 : Significant demonstrated strategy in linking framework to research design
""",
        'fr': """Dans quelle mesure le cadre conceptuel et théorique est-il adapté à la question de recherche en question? Dans quelle mesure le cadre est-il lié à la conception de la recherche proposée? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Stratégie peu démontrée pour relier le cadre à la conception de la recherche
4 - 7 : Quelques stratégies démontrées pour relier le cadre à la conception de la recherche
8 - 10 : Stratégie importante démontrée pour relier le cadre à la conception de la recherche
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate a rigorous approach to answering their research questions? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Little demonstrated rigor
4 - 7 : Some demonstrated rigor
8 - 10 : Significant/superior demonstrated rigor
""",
        'fr': """Dans quelle mesure l’organisation fait-elle preuve de rigueur dans ses réponses aux questions de recherche? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Démontre peu de rigueur
4 - 7 : Certains aspects font preuve de rigueur
8 - 10 : Démontre une rigueur supérieure
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, 'Gender and inclusion', description_override={
        'en': """How has your organization addressed gender-equality and other kinds of inclusion and diversity dimensions socioeconomic, political, cultural, ethnic in its policy research? 
How do you anticipate this will improve with this AI4D support? 
Please give a brief explanation of your strategy with gender, inclusion and diversity related issues as it relates to AI/advanced technologies and offer examples of the research work. 

Please provide examples PDF or links to material that demonstrates your strategy and research on gender, inclusion and diversity.

Maximum 750 words""",
    'fr': ""
    })
    add_information_question(form.id, form.application_form_id, 'Gender and inclusion: Supporting documents', type='multi-file')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate in-depth knowledge of gender-related dimensions of AI4D? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Limited or some demonstrated ability with gender related issues
4 - 7 : Substantive demonstrated ability with gender related issues
8 - 10 : Superior/significant demonstrated ability with gender related issues
""",
        'fr': """Dans quelle mesure l’organisation fait-elle preuve d’une connaissance approfondie des dimensions de genre d’IAPD? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Capacité limitée ou démontrée à traiter des questions liées au genre
4 - 7 : Capacité démontrée à traiter des questions liées au genre
8 - 10 : Capacité supérieure démontrée en matière de questions liées au genre
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate in-depth knowledge of other inclusion-related dimensions of AI4D, such as socioeconomics, cultural/ethnic and broader social inclusion issues? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Limited or some demonstrated understanding of inclusion-related challenges
4 - 7 : Substantive demonstrated understanding of inclusion-related challenges
8 - 10 : Significant demonstrated understanding of inclusion-related challenges
""",
        'fr': """Dans quelle mesure l’organisation démontre-t-elle une connaissance approfondie d’autres dimensions de l’IAPD liées à l’inclusion, telles que la socio-économie, la culture/ethnie et les questions plus larges d’inclusion sociale? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Compréhension limitée ou démontrée des défis liés à l’inclusion
4 - 7 : Compréhension démontrée des défis liés à l’nclusion
8 - 10 : Une compréhension significative et démontrée des défis liés à l’inclusion
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Considering the answer on gender and inclusion and the examples provided by the applicant, to what extent does the organization demonstrate in-depth knowledge of gender and inclusion-related issues/challenges in AI and advanced technologies? 
\[Total possible points = 5\]

**Scale:**
0 - 1 : No or limited knowledge of gender and inclusion-related issues
2 - 3 : Some knowledge of gender and inclusion-related issues
4 - 5 : Superior/significant knowledge of gender and inclusion-related issues
""",
        'fr': """Compte tenu de la réponse sur le genre et l’inclusion et des exemples fournis par le candidat, dans quelle mesure l’organisation démontre-t-elle une connaissance approfondie des questions et des défis liés au genre et à l’inclusion dans le domaine de l’IA et des technologies avancées? 
\[Total des points possibles = 5\]

**Scale:**
0 - 1 : Aucune connaissance ou une connaissance limitée des questions liées au genre et à l’inclusion
2 - 3 : Une certaine connaissance des questions liées à l’égalité des sexes et à l’inclusion
4 - 5 : Connaissance supérieure des questions liées au genre et à l’inclusion
"""
    }, min_score=0, max_score=5)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, 'Ethical considerations')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please assess the applicant’s ethics review process for their research. Does the applicant outline a clear and independent process for reviewing and ensuring the privacy, dignity, and integrity of individuals who are the subjects of their research? 
\[Total possible points = 5\]

**Scale:**
0 - 1 : Limited research ethics protocols
2 - 3 : Some research ethics protocols
4 - 5 : Significant research ethics protocols
""",
        'fr': """Veuillez évaluer le processus d’évaluation éthique du candidat pour sa recherche. Le candidat décrit-il un processus clair et indépendant pour évaluer et garantir la vie privée, la dignité et l’ntégrité des personnes qui font l’objet de ses recherches? 
\[Total des points possibles = 5\]

**Scale:**
0 - 1 : Protocoles d’éthique de la recherche limités
2 - 3 : Quelques protocoles d’éthique de la recherche
4 - 5 : Protocoles importants en matière d’éthique de la recherche
"""
    }, min_score=0, max_score=5)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '4. Capacity development')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant clearly identify where they need the most capacity building to improve work and outcomes to advance responsible AI in their country/region - and offer a coherent, reasonable strategy for addressing the gap? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Limited ability to identify capacity development needs
4 - 7 : Some ability to identify capacity development needs
8 - 10 : Significant ability to identify capacity development needs
""",
        'fr': """Dans quelle mesure le candidat identifie-t-il clairement les domaines dans lesquels il a le plus besoin de renforcer ses capacités pour améliorer le travail et les résultats afin de faire progresser l’IA responsable dans son pays/région - et propose-t-il une stratégie cohérente et raisonnable pour combler les lacunes?
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Capacité limitée à identifier les besoins en matière de renforcement des capacités
4 - 7 : Une certaine capacité à identifier les besoins en matière de développement des capacités
8 - 10 : Capacité importante à identifier les besoins en matière de renforcement des capacités
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '5. Communicating for influence')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please review the applicant's description of their research communications strategy. To what extent does the organization demonstrate an ability or approach to communicate their research well to influence policy? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Little demonstrated ability to communicate research
4 - 7 : Some demonstrated ability to communicate research
8 - 10 : Significant/superior demonstrated ability to communicate research
""",
        'fr': """Veuillez examiner la description par le candidat de sa stratégie de communication sur la recherche. Dans quelle mesure l’organisme démontre-t-il une capacité ou une approche pour bien communiquer sur sa recherche afin d’influencer les politiques? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Démontre peu d’aptitude à communiquer sur la recherche
4 - 7 : Démontre une capacité modérée à communiquer sur la recherche
8 - 10 : Démontre une capacité supérieure à communiquer sur la recherche
"""
    }, min_score=0, max_score=10)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '6. Results')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent are the proposed markers for measuring success for the organization in the context of this project specific, appropriate, achievable, timely and measurable? 
\[Total possible points = 15\]

**Scale:**
0 - 5 : Limited clarity for a vision of success, markers are unclear or poorly defined
6 - 10 : Some articulation of success, markers may lack clarity, specificity, appropriateness, feasibility, or measurability
11- 15 : Clear vision of success matched with strong, measurable markers
""",
        'fr': """Dans quelle mesure les marqueurs proposés pour mesurer le succès de l’organisation dans le cadre de ce projet sont-ils spécifiques, appropriés, réalisables, opportuns et mesurables? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Clarté limitée pour une vision de la réussite, les marqueurs sont peu clairs ou mal définis
6 - 10 : Une certaine articulation de la réussite, les marqueurs peuvent manquer de clarté, de spécificité, de pertinence, de faisabilité ou de mesurabilité
11- 15 : Une vision claire de la réussite assortie de marqueurs forts et mesurables
"""
    }, min_score=0, max_score=15)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '7. Project schedule')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant demonstrate a clear and realistic project schedule for achieving their objectives with outputs and milestones as they relate to the budget? 
\[Total possible points = 5\]

**Scale:**
0 - 1 : Limited demonstration of how to achieve project objectives
2 - 3 : Some demonstration of how to achieve project objectives
4 - 5 : Superior/significant demonstration of how to achieve project objectives
""",
        'fr': """Dans quelle mesure le demandeur démontre-t-il un calendrier de projet clair et réaliste pour atteindre ses objectifs, avec des résultats et des étapes en rapport avec le budget? 
\[Total des points possibles = 5\]

Scale: 
0 - 1 : Démonstration limitée de la manière d’atteindre les objectifs du projet
2 - 3 : Quelques démonstrations de la manière d’atteindre les objectifs du projet
4 - 5 : Démonstration supérieure/significative de la manière d’atteindre les objectifs du projet
"""
    }, min_score=0, max_score=5)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '8. Supplemental documentation (optional).')

    add_comment_question(form.id, headlines=None, descriptions={
        'en': """Please review the supplemental documentation and provide your assessment of these documents. This question is not weighted, but your assessment will be taken into consideration should there be a tie, or a close score that requires an assessment of the applicant’s overall work.""",
        'fr': """Veuillez examiner les documents complémentaires et donner votre évaluation de ces documents. Cette question n’est pas pondérée, mais votre évaluation sera prise en considération en cas d’égalité ou de score serré nécessitant une évaluation de l’ensemble du travail du candidat."""
    })

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    print('Finished configuring Section II')

    add_divider(form.id, headlines={
        'en': 'Section III: Policy Engagement Experience',
        'fr': 'Section III : Expérience de l’engagement politique'
    }, descriptions={
        'en': """Please review and evaluate the applicant’s answers on their policy engagement experience.
\[Total possible points: 75\]

Evaluation criteria:
    - Evidence of national and regional policy engagement and influence as well as regional and global experience. Applicant must be able to show regular policy engagement with target audiences, including policymakers, media, and civil society organizations.
    - Neutrality and ability to convene a broad spectrum of views, with a strong commitment to expand your research portfolio, engage broader perspectives on AI policy issues, and improve organizational performance.
""",
        'fr': """Veuillez examiner et évaluer les réponses du candidat en fonction de son expérience en matière d’engagement politique.
\[Total des points possibles = 75\]

Critères d’évaluation :
    - Preuve de l’engagement et de l’influence de la politique nationale et régionale ainsi que de l’expérience régionale et mondiale. Le candidat doit être en mesure de démontrer un engagement politique régulier auprès des publics cibles, notamment les décideurs politiques, les médias et les organisations de la société civile.
    - Neutralité et capacité à réunir un large éventail de points de vue, avec un engagement fort à élargir votre portefeuille de recherche, à engager des perspectives plus larges sur les questions de politique d’IA et à améliorer la performance organisationnelle.
"""
    })

    add_information_question(form.id, form.application_form_id, '1. Policy engagement')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate quality engagement with national governing institutions (e.g. government departments, bodies and agencies, as well as regulators, and other public-sector institutions) on advanced technology issues?  \[Total possible points = 15\] 
*Note: For the purposes of this initiative, having national policy influence is critical.*

Applicant receives and responds to requests for input from governments/other regulatory institutions.

**Scale:**
0 - 5 : Limited quality engagement 
6 - 10 : Some quality engagement
11- 15 : Significant quality engagement
""",
        'fr': """Dans quelle mesure l’organisation fait-elle preuve d’un engagement de qualité avec les institutions nationales de gouvernance (par exemple, les ministères, les organismes et les agences gouvernementales, ainsi que les régulateurs et autres institutions du secteur public) sur les questions de technologie avancée? 
\[Total des points possibles = 15\]
*Note: Pour les besoins de cette initiative, il est essentiel d'avoir une influence sur les politiques nationales.*

Le candidat reçoit et répond aux demandes de contribution des gouvernements/autres institutions de régulation
**Scale:**
0 - 5 : Engagement de qualité limité
6 - 10 : Engagement de qualité partiel
11- 15 : Engagement de qualité important
"""
    }, min_score=0, max_score=15)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Applicant proactively engages with policy makers (such as on steering committees, or on emerging policy issues).

**Scale:**
0 - 5 : Limited quality engagement 
6 - 10 : Some quality engagement
11- 15 : Significant quality engagement
""",
        'fr': """Dans quelle mesure l’organisation fait-elle preuve d’un engagement de qualité avec les institutions nationales de gouvernance (par exemple, les ministères, les organismes et les agences gouvernementales, ainsi que les régulateurs et autres institutions du secteur public) sur les questions de technologie avancée? 
\[Total des points possibles = 15\]
*Note: Pour les besoins de cette initiative, il est essentiel d'avoir une influence sur les politiques nationales.*

Le candidat s’engage de manière proactive auprès des décideurs politiques, par exemple au sein des comités de pilotage, ou sur les questions émergentes.
**Scale:**
0 - 5 : Engagement de qualité limité
6 - 10 : Engagement de qualité partiel
11- 15 : Engagement de qualité important
"""
    }, min_score=0, max_score=15)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please review the three examples of policy engagement. To what extent does the applicant demonstrate an ability to engage with policy makers on substantive/technical policy issues? 
\[Total possible points = 15\]

**Scale:**
0 - 5 : Limited demonstrated ability to engage with policy makers on substantive/technical policy issues
6 - 10 : Some demonstrated ability to engage with policy makers on substantive/technical policy issues
11- 15 : Significant/superior demonstrated ability to engage with policy makers on substantive/technical policy issues
""",
        'fr': """Veuillez examiner les trois exemples d’engagement politique. Dans quelle mesure le candidat démontre-t-il une capacité à s’engager auprès des décideurs politiques sur des questions politiques de fond/techniques? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Capacité limitée et avérée à dialoguer avec les décideurs politiques sur des questions politiques de fond/techniques
6 - 10 : Certains aspects font preuve de leur capacité à dialoguer avec les décideurs politiques sur des questions politiques de fond/techniques
11- 15 : Capacité supérieurement démontrée à s’engager avec les décideurs politiques sur des questions de fond/techniques
"""
    }, min_score=0, max_score=15)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    add_information_question(form.id, form.application_form_id, '2. Informing debates and policies')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the applicant demonstrate an ability to inform public debate and policy processes nationally or regionally? 
\[Total possible points = 15\]

**Scale:**
0 - 5 : Limited ability
6 - 10 : Some demonstrated ability
11- 15 : Significant demonstrated ability
""",
        'fr': """Dans quelle mesure le candidat démontre-t-il une capacité à informer le débat public et les processus politiques au niveau national ou régional? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Capacité limitée
6 - 10 : Certains aspects font preuve de capacités
11- 15 : Capacité significative
"""
    }, min_score=0, max_score=15)

    add_information_question(form.id, form.application_form_id, '3. Regional engagement')
    add_information_question(form.id, form.application_form_id, 'Regional engagement', heading_override=True)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """To what extent does the organization demonstrate clear regional/international engagement on AI/advanced technology policy issues with other governments, public sector institutions, bi-lateral, multilateral or international institutions/organizations or multi stakeholder fora? 
\[Total possible points = 15\]

Scale: 
0 - 5 : Limited regional/international engagement
6 - 10 : Substantive regional/international engagement
11- 15 : Significant regional/international engagement
""",
        'fr': """Dans quelle mesure l’organisation fait-elle preuve d’un engagement régional/international clair sur les questions de politique technologique avancée et d’IA avec d’autres gouvernements, des institutions du secteur public, des institutions/organisations bilatérales, multilatérales ou internationales ou des forums multipartites? 
\[Total des points possibles = 15\]

**Scale:**
0 - 5 : Engagement régional/international limité
6 - 10 : Engagement régional/international substantiel
11- 15 : Un engagement régional/international important
"""
    }, min_score=0, max_score=15)

    add_comment_question(form.id, descriptions={
        'en': "Comments",
        'fr': "Des commentaires?"
    }, headlines=None)

    print('Finished configuring Section III')

    add_divider(form.id, headlines={
        'en': "Section IV: Budget",
        'fr': "Section IV: Budget"
    }, descriptions={
        'en': """Please review and evaluate the applicant’s budget.
\[Total possible points = 30\]

Evaluation criteria:
    - Clear and coherent
    - Appropriate for the proposed activities
    - Aligned with management plan
""",
        'fr': """Veuillez examiner et évaluer le budget du candidat.
\[Total des points possibles = 30\]

Critères d’évaluation :
    - Clair et cohérent
    - Approprié pour les activités proposées
    - Aligné sur le plan de gestion
"""
    })

    add_information_question(form.id, form.application_form_id, 'Budget', 'file')

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Please review the applicant’s budget and consider the coherence and clarity, the appropriateness of budget lines for proposed activities and the budget’s alignment with the research plan.
In terms of overall coherence, appropriateness to research activities and fiscal management, please rate the applicant’s budget. 
\[Total possible points = 30\]

**Scale:**
0 - 10 : Budget somewhat demonstrates coherence and appropriateness for research and policy impact
11 - 20 : Budget substantively demonstrates coherence and appropriateness for research and policy impact
21 - 30 : Budget demonstrates superior coherence and appropriateness for research and policy impact
""",
        'fr': """Veuillez examiner le budget du candidat et considérer la cohérence et la clarté, la pertinence des lignes budgétaires pour les activités proposées et l’alignement du budget sur le plan de recherche.
En termes de cohérence globale, d’adéquation aux activités de recherche et de gestion budgétaire, veuillez évaluer le budget du candidat. 
\[Total des points possibles = 30\]

**Scale:**
0 - 10 : Le budget démontre quelque peu la cohérence et l’adéquation à la recherche et à l’impact politique
11 - 20 : Le budget démontre de manière substantielle la cohérence et l’adéquation à la recherche et à l’impact politique
21 - 30 : Le budget démontre une cohérence et une adéquation supérieures pour la recherche et l’impact politique
"""
    }, min_score=0, max_score=30)

    add_comment_question(form.id, headlines=None, descriptions={
        'en': """IDRC’s grants administration team will be reviewing all of the budgets independently, and their assessment will be discussed during the final selection process. However, given the significance of budgets in terms of institutional strength, research planning and strategy, and risk mitigation, please provide feedback on the applicant’s proposed budget, and offer any input or insights you may have regarding the soundness of the applicant’s budget in relation to their research objectives and overall plan.""",
        'fr': """L’équipe d’administration des subventions du CRDI examinera tous les budgets de manière indépendante et leur évaluation sera discutée lors du processus de sélection final. Toutefois, étant donné l’importance des budgets en termes de force institutionnelle, de planification et de stratégie de recherche et d’atténuation des risques, veuillez donner votre avis sur le budget proposé par le candidat et faire part de vos commentaires ou de vos idées concernant"""
    })
    
    print('Finished configuring Section IV')

    add_divider(form.id, headlines={
        'en': "Section V: Overall quality of application",
        'fr': "Section V : Qualité générale de la demande"
    }, descriptions={
        'en': """Taking the proposal as a whole, please answer the following questions.
\[Total possible points = 25\]""",
        'fr': """En prenant la proposition dans son ensemble, veuillez répondre aux questions suivantes.
\[Total des points possibles = 25\]"""
    })

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Is the overall application well-articulated and does it demonstrate clarity of purpose and potential impact for AI4D? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Limited articulation and clarity
4 - 7 : Somewhat well-articulated and clear
8 - 10 : Very well-articulated and clear
""",
        'fr': """La demande globale est-elle bien articulée et démontre-t-elle la clarté de l’objectif et l’impact potentiel pour IAPD? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Articulation et clarté limitées
4 - 7 : Assez bien articulé et clair
8 - 10 : Très bien articulé et clair
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Does the proposal demonstrate in-depth, well-rounded, and multi-disciplinary knowledge of AI and advanced technology policy themes and issues? 
\[Total possible points = 10\]

**Scale:**
0 - 3 : Little multi-disciplinary knowledge
4 - 7 : Some multi-disciplinary knowledge
8 - 10 : Significant multi-disciplinary knowledge
""",
        'fr': """La proposition démontre-t-elle une connaissance approfondie, bien équilibrée et pluridisciplinaire des thèmes et des questions de politique en matière d’IA et de technologies avancées? 
\[Total des points possibles = 10\]

**Scale:**
0 - 3 : Peu de connaissances pluridisciplinaires
4 - 7 : Quelques connaissances pluridisciplinaires
8 - 10 : Connaissances pluridisciplinaires importantes
"""
    }, min_score=0, max_score=10)

    add_evaluation_question(form.id, headlines=None, descriptions={
        'en': """Does the proposal demonstrate a clear strategy of how the organization will benefit from the support offered by this initiative and add to debates on the AI and advanced technology policy themes in the region? 
\[Total possible points = 5\]

**Scale:**
0 - 1 : Little
2 - 3 : Some
4 - 5 : Significant
""",
        'fr': """La proposition présente-t-elle une stratégie claire quant à la manière dont l’organisation bénéficiera du soutien offert par cette initiative et contribue-t-elle aux débats sur les thèmes de l’IA et de la politique en matière de technologies avancées dans la région? 
\[Total des points possibles = 5\]

**Scale:**
0 - 1 : Peu
2 - 3 : Quelques
4 - 5 : Important
"""
    }, min_score=0, max_score=5)

    add_comment_question(form.id, headlines=None, descriptions={
        'en': """Please provide any final comments on the overall application. These will feed into discussions""",
        'fr': """Veuillez fournir tout commentaire final sur l’ensemble de la demande. Ces commentaires seront pris en compte dans les discussions."""
    })

    print('DONE')


def downgrade():
    pass

