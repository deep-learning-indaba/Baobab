"""Add pwa_icon_192 and pwa_icon_512 to organisation

Revision ID: 8f3a2c1d9e4b
Revises: fd232b2eed5e
Create Date: 2026-06-28 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '8f3a2c1d9e4b'
down_revision = 'fd232b2eed5e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('organisation', sa.Column('pwa_icon_192', sa.String(255), nullable=True))
    op.add_column('organisation', sa.Column('pwa_icon_512', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('organisation', 'pwa_icon_512')
    op.drop_column('organisation', 'pwa_icon_192')
