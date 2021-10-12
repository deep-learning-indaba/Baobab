"""Add call to event_type enum

Revision ID: 4ec21502ae82
Revises: 9b181cdd3fa1
Create Date: 2020-08-23 16:14:12.709215

"""

# revision identifiers, used by Alembic.
revision = "4ec21502ae82"
down_revision = "9b181cdd3fa1"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'CALL'")


def downgrade():
    op.execute(
        """DELETE FROM pg_enum
WHERE enumlabel = 'CALL'
AND enumtypid = (
  SELECT oid FROM pg_type WHERE typname = 'event_type'
)"""
    )
