"""Add badge_exported flag to attendance

Revision ID: b3d9f4a12c7e
Revises: 7a1f9d2c6b4e
Create Date: 2026-07-16 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'b3d9f4a12c7e'
down_revision = '7a1f9d2c6b4e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('attendance', sa.Column('badge_exported', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('attendance', sa.Column('badge_exported_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('attendance', 'badge_exported_at')
    op.drop_column('attendance', 'badge_exported')
