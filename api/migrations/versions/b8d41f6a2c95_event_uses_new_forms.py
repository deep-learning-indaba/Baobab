"""Add event.uses_new_forms

Revision ID: b8d41f6a2c95
Revises: e5a1c7d93b20
Create Date: 2026-10-08 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'b8d41f6a2c95'
down_revision = 'e5a1c7d93b20'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('event', sa.Column(
        'uses_new_forms', sa.Boolean(), nullable=False, server_default=sa.text('true')
    ))
    # Existing events stay on the legacy system unless they already have a
    # new-system application form.
    op.execute("""
        UPDATE event SET uses_new_forms = EXISTS (
            SELECT 1 FROM form
            WHERE form.event_id = event.id AND form.form_type = 'application'
        )
    """)


def downgrade():
    op.drop_column('event', 'uses_new_forms')
