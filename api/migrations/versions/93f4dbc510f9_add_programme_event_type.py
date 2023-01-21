"""Add programme event_type

Revision ID: 93f4dbc510f9
Revises: ec9886a36eab
Create Date: 2023-01-21 12:00:50.061334

"""

# revision identifiers, used by Alembic.
revision = '93f4dbc510f9'
down_revision = 'ec9886a36eab'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'PROGRAMME'")

    op.execute("UPDATE organisation set privacy_policy='aims-sa-privacy-policy.pdf' where domain='aims'")


def downgrade():
        op.execute("""DELETE FROM pg_enum
WHERE enumlabel = 'PROGRAMME'
AND enumtypid = (
  SELECT oid FROM pg_type WHERE typname = 'event_type'
)""")
