"""Add form translations

Revision ID: add_form_translations
Revises: 661475bafb4d
Create Date: 2024-12-26 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_form_translations'
down_revision = '661475bafb4d'
branch_labels = None
depends_on = None


def upgrade():
    # Create form_translation table
    op.create_table('form_translation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('form_id', sa.Integer(), nullable=False),
    sa.Column('language', sa.String(length=2), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['form_id'], ['form.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('form_id', 'language')
    )


def downgrade():
    op.drop_table('form_translation')
