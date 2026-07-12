"""add event_id to form table

Revision ID: add_form_event_id
Revises: add_tag_expression
Create Date: 2026-03-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_form_event_id'
down_revision = 'add_tag_expression'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form', sa.Column('event_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_form_event_id', 'form', 'event', ['event_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_form_event_id', 'form', type_='foreignkey')
    op.drop_column('form', 'event_id')
