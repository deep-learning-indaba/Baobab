"""add affiliation, country, email to member_profile

Revision ID: f9e8d7c6b5a4
Revises: 8bfeebfbdf01
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'f9e8d7c6b5a4'
down_revision = '8bfeebfbdf01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('member_profile', sa.Column('country', sa.String(120), nullable=True))
    op.add_column('member_profile', sa.Column('affiliation', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('member_profile', 'affiliation')
    op.drop_column('member_profile', 'country')
