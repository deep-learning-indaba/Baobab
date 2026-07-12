"""add section and question tag_expression

Revision ID: add_tag_expression
Revises: add_form_visibility_expression
Create Date: 2026-01-01 18:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tag_expression'
down_revision = 'add_form_visibility_expression'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form_section', sa.Column('tag_expression', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('form_question', sa.Column('tag_expression', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('form_section', 'tag_expression')
    op.drop_column('form_question', 'tag_expression')
