"""add survey_open to event

Revision ID: 80393b25a1bb
Revises: 966139aff9ed
Create Date: 2026-08-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '80393b25a1bb'
down_revision = '966139aff9ed'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('event', sa.Column('survey_open', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('event', 'survey_open')
