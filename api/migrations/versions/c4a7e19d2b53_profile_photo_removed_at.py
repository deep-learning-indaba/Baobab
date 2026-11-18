"""Add photo_removed_at to member_profile.

Revision ID: c4a7e19d2b53
Revises: 5b8e2d4c9a17
Create Date: 2026-11-12 10:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'c4a7e19d2b53'
down_revision = '5b8e2d4c9a17'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('member_profile', sa.Column('photo_removed_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('member_profile', 'photo_removed_at')
