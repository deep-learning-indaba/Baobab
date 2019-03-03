"""Add validation text to Question model.

Revision ID: 35cdc3c51184
Revises: d4a62bfc5be5
Create Date: 2019-03-01 16:08:31.563227

"""

# revision identifiers, used by Alembic.
revision = '35cdc3c51184'
down_revision = 'd4a62bfc5be5'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from app.applicationModel.models import Question, Section


def upgrade():
    op.add_column('question', sa.Column('validation_text', sa.String(), nullable=True))
    update_question_data()


def update_question(session, question_id, validation_text):
    question = session.query(Question).filter(Question.id == question_id).first()
    question.validation_text = validation_text


def update_question_data():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    update_question(session, 1, 'Enter 50 to 150 words')

    update_question(session, 2, 'Enter 50 to 150 words')
    update_question(session, 3, 'Enter a maximum of 80 words')
    update_question(session, 4, 'Enter a maximum of 80 words')
    update_question(session, 5, 'Enter a maximum of 150 words')
    update_question(session, 9, 'Enter a maximum of 150 words')
    update_question(session, 16, 'Enter a maximum of 150 words')
    update_question(session, 18, 'Enter a maximum of 150 words')

def downgrade():
    op.drop_column('question', 'validation_text')
