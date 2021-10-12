"""Add validation text to Question model.

Revision ID: 35cdc3c51184
Revises: d4a62bfc5be5
Create Date: 2019-03-01 16:08:31.563227

"""

# revision identifiers, used by Alembic.
revision = "35cdc3c51184"
down_revision = "d4a62bfc5be5"

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()


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
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)

    def __init__(
        self,
        application_form_id,
        section_id,
        headline,
        placeholder,
        order,
        questionType,
        validation_regex,
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


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)
    op.add_column("question", sa.Column("validation_text", sa.String(), nullable=True))
    update_question_data()


def update_question(session, question_id, validation_text):
    question = session.query(Question).filter(Question.id == question_id).first()
    question.validation_text = validation_text


def update_question_data():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    update_question(session, 1, "Enter 50 to 150 words")

    update_question(session, 2, "Enter 50 to 150 words")
    update_question(session, 3, "Enter a maximum of 80 words")
    update_question(session, 4, "Enter a maximum of 80 words")
    update_question(session, 5, "Enter a maximum of 150 words")
    update_question(session, 9, "Enter a maximum of 150 words")
    update_question(session, 16, "Enter a maximum of 150 words")
    update_question(session, 18, "Enter a maximum of 150 words")


def downgrade():
    op.drop_column("question", "validation_text")
