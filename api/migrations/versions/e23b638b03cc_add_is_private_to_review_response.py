"""
Adds a field called ``is_private`` to review_response table.
It is used to specify whether the response from the reviewer is public,
or private. If it is private, then only the meta-reviewer can see the response.

Revision ID: e23b638b03cc
Revises: 9143756e596d
Create Date: 2023-07-30 19:16:28.509240

"""

# revision identifiers, used by Alembic.
revision = 'e23b638b03cc'
down_revision = '9143756e596d'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('review_response', sa.Column('is_private', sa.Boolean(), nullable=False))

def downgrade():
    op.drop_column('review_response', 'is_private')