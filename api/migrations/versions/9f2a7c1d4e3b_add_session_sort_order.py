"""Programme: add sort_order to sessions, for ordering parallel sessions.

Revision ID: 9f2a7c1d4e3b
Revises: e1d2c3b4a5f6
Create Date: 2026-07-11 09:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '9f2a7c1d4e3b'
down_revision = 'e1d2c3b4a5f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('programme_session', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('programme_session', 'sort_order')
