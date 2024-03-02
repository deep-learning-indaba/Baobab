"""
Adds a field called ``is_private`` to review_response table.
It is used to specify whether the response from the reviewer is public,
or private. If it is private, then only the meta-reviewer can see the response.

Revision ID: 6d2e1dc65ef6
Revises: 5d5b0524b4fa
Create Date: 2023-08-24 19:44:58.051586

"""

# revision identifiers, used by Alembic.
revision = '6d2e1dc65ef6'
down_revision = '5d5b0524b4fa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('review_response', sa.Column('is_private', sa.Boolean(), nullable=True))
    op.execute("UPDATE review_response SET is_private = false")
    op.alter_column('review_response', 'is_private', nullable=False)

def downgrade():
    op.drop_column('review_response', 'is_private')
