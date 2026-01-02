"""add form visibility_expression

Revision ID: add_form_visibility_expression
Revises: add_form_allow_edits
Create Date: 2026-01-01 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_form_visibility_expression'
down_revision = 'add_form_allow_edits'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('form', sa.Column('visibility_expression', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('form', 'visibility_expression')
