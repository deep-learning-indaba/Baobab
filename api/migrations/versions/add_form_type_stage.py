"""add form_type and stage to form table

Revision ID: add_form_type_stage
Revises: add_form_event_id
Create Date: 2026-03-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_form_type_stage'
down_revision = 'add_form_event_id'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form', sa.Column('form_type', sa.String(50), nullable=True))
    op.add_column('form', sa.Column('stage', sa.Integer(), nullable=True))
    op.create_unique_constraint(
        'uq_event_form_type_stage', 'form',
        ['event_id', 'form_type', 'stage']
    )


def downgrade():
    op.drop_constraint('uq_event_form_type_stage', 'form', type_='unique')
    op.drop_column('form', 'stage')
    op.drop_column('form', 'form_type')
