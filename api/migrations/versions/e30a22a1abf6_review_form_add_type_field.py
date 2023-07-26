"""
Added a field called ``reviewer_type`` to review_form table.
Null if the event TYPE is not CONTINUOUS_JOURNAL.
It is used to specify whether the reviewer is a 'Meta-reviewer' or a normal 'Reviewer'.

Revision ID: e30a22a1abf6
Revises: 9143756e596d
Create Date: 2023-07-26 12:30:18.181998
"""

# revision identifiers, used by Alembic.
revision = 'e30a22a1abf6'
down_revision = '9143756e596d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('review_form', sa.Column('reviewer_type', sa.String(), nullable=True))


def downgrade():
    op.drop_column('review_form', 'reviewer_type')