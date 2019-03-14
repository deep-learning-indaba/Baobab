"""empty message

Revision ID: b4c1dfa70233
Revises: 91468f804113
Create Date: 2019-03-14 21:10:03.713712

"""

# revision identifiers, used by Alembic.
revision = 'b4c1dfa70233'
down_revision = '91468f804113'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db

# Freeze the question model
Base = declarative_base()

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
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)

    def __init__(self, application_form_id, section_id, headline, placeholder, order, questionType, validation_regex, validation_text=None, is_required = True, description = None, options = None):
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


class ApplicationForm(Base):
    __tablename__ = 'application_form'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    is_open = db.Column(db.Boolean(), nullable=False)
    deadline = db.Column(db.DateTime(), nullable=False)

    def __init__(self, event_id, is_open, deadline):
        self.event_id = event_id
        self.is_open = is_open
        self.deadline = deadline


class Section(Base):
    __tablename__ = 'section'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer(), primary_key=True)
    application_form_id = db.Column(db.Integer(), db.ForeignKey('application_form.id'), nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer(), unique=True, nullable=False)

    def __init__(self, application_form_id, name, description, order):
        self.application_form_id = application_form_id
        self.name = name
        self.description = description
        self.order = order


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Add ethnicity question to apply for travel support section
    section = session.query(Section).filter(Section.name == 'Apply For Travel Support ').first()
    new_question = Question(section.application_form_id, section.id, 
        'You Ethnicity (South African applicants only)', 
        'Select an option...', 
        5,
        'multi-choice',
        None,
        None,
        False, 
        'Please fill this in if you are applying for travel support from South Africa, leave blank otherwise. We may be required to provide this information to some of our South African sponsors for reporting purposes.',
        [
            {"label": "Black", "value": 'black'},
            {"label": "Coloured / Mixed Descent", "value": 'coloured/mixed'},
            {"label": "White", "value": 'white'},
            {"label": "Indian Descent", "value": 'indian'},
            {"label": "Other", "value": "other"}
        ])

    # Reset the auto-increment ID sequence for the table
    op.execute("""SELECT setval('question_id_seq', (SELECT max(id) FROM question));""")
    session.add(new_question)
    session.commit()
    session.flush()

    # Add word limit to additional information sections
    question = session.query(Question).filter(Question.headline == 'Any additional comments or remarks for the selection committee?').first()
    question.validation_regex = r'^\W*(\w+(\W+|$)){0,150}$'
    question.validation_text = 'Enter a maximum of 150 words'
    question.description = 'Maximum 150 words.'

    # Update validation text on anything relevant question
    question = session.query(Question).filter(Question.headline == 'Anything else you think relevant, for example links to personal webpage, papers, GitHub/code repositories, community and outreach activities. ').first()
    question.validation_text = 'Maximum 150 words.'

    session.commit()
    session.flush()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    # Delete the new question
    # question = session.query(Question).filter(Question.headline == 'You Ethnicity (South African applicants only)').delete()

    # Undo changes to additional comments question
    question = session.query(Question).filter(Question.headline == 'Any additional comments or remarks for the selection committee?').first()
    question.validation_regex = None
    question.validation_text = None
    question.description = None

    # Undo changes to anything relevant question
    question = session.query(Question).filter(Question.headline == 'Anything else you think relevant, for example links to personal webpage, papers, GitHub/code repositories, community and outreach activities. ').first()
    question.validation_text = None

    session.commit()
