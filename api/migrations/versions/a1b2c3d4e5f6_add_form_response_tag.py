"""Add form_response_tag table

Revision ID: a1b2c3d4e5f6
Revises: fd232b2eed5e
Create Date: 2026-05-04 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fd232b2eed5e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'form_response_tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_response_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['form_response_id'], ['form_response.id']),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_response_id', 'tag_id', name='uq_form_response_tag')
    )


def downgrade():
    op.drop_table('form_response_tag')
