"""
Added a Boolean field called ``private`` to review_question table.
Null if the event TYPE is not CONTINUOUS_JOURNAL.
It is used to specify whether the question from the reviewer 
is private (True) or public (False).

Revision ID: ccc42bf54796
Revises: e30a22a1abf6
Create Date: 2023-07-26 15:56:00.173322

"""

# revision identifiers, used by Alembic.
revision = 'ccc42bf54796'
down_revision = 'e30a22a1abf6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('review_question', sa.Column('private', sa.Boolean(), nullable=True))
    

def downgrade():
    op.drop_column('review_question', 'private')
