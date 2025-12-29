"""Add allow_edits field to Form model

Revision ID: add_form_allow_edits
Revises: add_form_trans_desc
Create Date: 2024-12-29

"""

# revision identifiers, used by Alembic.
revision = 'add_form_allow_edits'
down_revision = 'add_form_trans_desc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('form', sa.Column('allow_edits', sa.Boolean(), nullable=True))
    op.execute("UPDATE form SET allow_edits = True;")
    op.alter_column('form', 'allow_edits', nullable=False)


def downgrade():
    op.drop_column('form', 'allow_edits')
