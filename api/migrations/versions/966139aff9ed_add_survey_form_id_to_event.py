"""add survey_form_id to event

Revision ID: 966139aff9ed
Revises: a3f0b6c9d1e2
Create Date: 2026-08-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '966139aff9ed'
down_revision = 'a3f0b6c9d1e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('event', sa.Column('survey_form_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'event_survey_form_id_fkey', 'event', 'form', ['survey_form_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('event_survey_form_id_fkey', 'event', type_='foreignkey')
    op.drop_column('event', 'survey_form_id')
