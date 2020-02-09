"""empty message

Revision ID: 20a94c6b2952
Revises: c3b4ca7ceef9
Create Date: 2020-02-07 21:02:03.012704

"""

# revision identifiers, used by Alembic.
revision = '20a94c6b2952'
down_revision = 'c3b4ca7ceef9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute(r"""UPDATE question SET placeholder='Enter 150 to 500 words' WHERE headline='Research Interests' and application_form_id=2""")
    op.execute(r"""UPDATE question SET placeholder='Enter up to 150 words', description='Max 150 words' WHERE headline='Motivation' and application_form_id=2""")


def downgrade():
    op.execute(r"""UPDATE question SET placeholder='Enter 500 - 2000 characters' WHERE headline='Research Interests' and application_form_id=2""")
    op.execute(r"""UPDATE question SET placeholder='Enter up to 500 characters', description='Max 500 characters' WHERE headline='Motivation' and application_form_id=2""")
