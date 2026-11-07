"""Add organisation branding columns and widen logo columns.

Revision ID: 5b8e2d4c9a17
Revises: 3f9c2a7d1e64
Create Date: 2026-11-07 09:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '5b8e2d4c9a17'
down_revision = '3f9c2a7d1e64'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('organisation', sa.Column('primary_colour', sa.String(length=7), nullable=True))
    op.add_column('organisation', sa.Column('secondary_colour', sa.String(length=7), nullable=True))
    op.add_column('organisation', sa.Column('favicon', sa.String(length=255), nullable=True))
    for column in ('small_logo', 'large_logo', 'icon_logo'):
        op.alter_column('organisation', column, existing_type=sa.String(length=100),
                        type_=sa.String(length=255), existing_nullable=False)


def downgrade():
    for column in ('small_logo', 'large_logo', 'icon_logo'):
        op.alter_column('organisation', column, existing_type=sa.String(length=255),
                        type_=sa.String(length=100), existing_nullable=False)
    op.drop_column('organisation', 'favicon')
    op.drop_column('organisation', 'secondary_colour')
    op.drop_column('organisation', 'primary_colour')
