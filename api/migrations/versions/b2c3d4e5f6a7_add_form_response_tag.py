"""Add form_response_tag table

Revision ID: b2c3d4e5f6a7
Revises: ('a1b2c3d4e5f6', 'add_form_type_stage')
Create Date: 2026-05-04 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = ('a1b2c3d4e5f6', 'add_form_type_stage')

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
