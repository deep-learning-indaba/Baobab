"""empty message

Revision ID: 3e7bdff8af80
Revises: 20a94c6b2952
Create Date: 2020-02-09 15:49:49.758524

"""

# revision identifiers, used by Alembic.
revision = '3e7bdff8af80'
down_revision = '20a94c6b2952'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime

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


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    op.execute("""
        UPDATE email_template
        SET template = 'Dear {title} {firstname} {lastname},
This email serves to confirm that you have withdrawn your application to attend {event_name}. 
If this was a mistake, you may resubmit an application before the application deadline. If the deadline has past, please get in touch with us.
Kind Regards,
The {event_name} Team'
        WHERE key='withdrawal'
        AND event_id IS NULL
""")

    op.execute("UPDATE question SET description='Your university or company' WHERE headline='Affiliation' and application_form_id=2")

    company_question = session.query(Question).filter_by(headline='Institution or Company', application_form_id=2).first()

    if company_question:
        op.execute("DELETE FROM answer WHERE question_id={}".format(company_question.id))
        op.execute("DELETE FROM question WHERE id={}".format(company_question.id))

    op.execute("UPDATE question set description='The country where you work or study.' WHERE headline='Country' AND application_form_id=2")
    op.execute("UPDATE question set is_required=True WHERE headline='Extended abstract type' and application_form_id=2")
    op.execute("UPDATE question set is_required=True WHERE headline='Extended abstract' and application_form_id=2")
    op.execute("""UPDATE question set options='[{"value": "TMLSS2018", "label": "TMLSS 2018"}, {"value": "EEML2019", "label": "EEML 2019"}, {"value": "TMLSS2018-EEML2019", "label": "Both"}, {"value": "none", "label": "Neither"}]' WHERE headline='Previous attendance' AND application_form_id=2""")
    op.execute("""UPDATE organisation set name='EEML' WHERE id=2""")


def downgrade():
    pass
