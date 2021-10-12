"""Update EEML Review form

Revision ID: eb6f96db82e8
Revises: 6d34d1ab6864
Create Date: 2020-04-16 21:40:16.198719

"""

# revision identifiers, used by Alembic.
revision = "eb6f96db82e8"
down_revision = "6d34d1ab6864"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.get_bind().execute(
        """update review_question 
                             set type = 'file'
                             from question
                             where review_question.question_id = question.id
                             and question.headline = 'CV'"""
    )

    op.get_bind().execute(
        """update review_question 
                             set type = 'file'
                             from question
                             where review_question.question_id = question.id
                             and question.headline = 'Extended abstract'"""
    )


def downgrade():
    op.get_bind().execute(
        """update review_question 
                             set type = 'information'
                             from question
                             where review_question.question_id = question.id
                             and question.headline = 'CV'"""
    )

    op.get_bind().execute(
        """update review_question 
                             set type = 'information'
                             from question
                             where review_question.question_id = question.id
                             and question.headline = 'Extended abstract'"""
    )
