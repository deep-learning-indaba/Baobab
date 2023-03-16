"""Add review, accept with revision, and reject with encouragement states.

Revision ID: d0fd3894941a
Revises: 349da0b8780a
Create Date: 2023-03-14 14:43:16.898594

"""

# revision identifiers, used by Alembic.
revision = 'd0fd3894941a'
down_revision = '349da0b8780a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE outcome_status ADD VALUE 'REVIEW'")
    op.execute("ALTER TYPE outcome_status ADD VALUE 'ACCEPT_W_REVISION'")
    op.execute("ALTER TYPE outcome_status ADD VALUE 'REJECT_W_ENCOURAGEMENT'")

def downgrade():
    op.execute("""DELETE FROM pg_enum
        WHERE enumlabel = 'REVIEW' OR enumlabel = 'ACCEPT_W_REVISION' OR enumlabel = 'REJECT_W_ENCOURAGEMENT'
        AND enumtypid = (
        SELECT oid FROM pg_type WHERE typname = 'outcome_status'
        )""")
