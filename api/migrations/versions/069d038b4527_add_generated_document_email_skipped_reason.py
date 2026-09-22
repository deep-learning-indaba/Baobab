"""add generated_document.email_skipped_reason

Revision ID: 069d038b4527
Revises: f3a8c1d94e2b
Create Date: 2026-09-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '069d038b4527'
down_revision = 'f3a8c1d94e2b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('generated_document', sa.Column('email_skipped_reason', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('generated_document', 'email_skipped_reason')
