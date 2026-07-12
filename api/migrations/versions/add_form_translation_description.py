"""Add description field to FormTranslation model

Revision ID: add_form_trans_desc
Revises: add_form_translations
Create Date: 2024-12-28

"""

# revision identifiers, used by Alembic.
revision = 'add_form_trans_desc'
down_revision = 'add_form_translations'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('form_translation', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('form_translation', 'description')
