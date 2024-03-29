"""Add active column to tag

Revision ID: ae7c72f05201
Revises: 1cdf3a2cf02b
Create Date: 2023-04-05 00:23:31.627506

"""

# revision identifiers, used by Alembic.
revision = 'ae7c72f05201'
down_revision = '1cdf3a2cf02b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tag', sa.Column('active', sa.Boolean(), nullable=True))
    op.execute('UPDATE tag SET active = true;')
    op.alter_column('tag', 'active', nullable=False)


def downgrade():
    op.drop_column('tag', 'active')
