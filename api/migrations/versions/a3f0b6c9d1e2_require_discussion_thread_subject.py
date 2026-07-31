"""require a subject on every discussion thread

Subjects were previously optional, which produced board entries with no
subject to identify them. Existing rows with a NULL subject are backfilled
with a placeholder before the column is locked down to NOT NULL.

Revision ID: a3f0b6c9d1e2
Revises: c8a1d5e2f7b9
Create Date: 2026-07-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f0b6c9d1e2'
down_revision = 'c8a1d5e2f7b9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE discussion_thread SET subject = '(no subject)' WHERE subject IS NULL"
    )
    op.alter_column('discussion_thread', 'subject',
                     existing_type=sa.String(200), nullable=False)


def downgrade():
    op.alter_column('discussion_thread', 'subject',
                     existing_type=sa.String(200), nullable=True)
