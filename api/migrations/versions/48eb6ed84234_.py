"""empty message

Revision ID: 48eb6ed84234
Revises: 1b081014926a
Create Date: 2023-02-22 20:15:34.485391

"""

# revision identifiers, used by Alembic.
revision = '48eb6ed84234'
down_revision = '1b081014926a'

from alembic import op
import sqlalchemy as sa



def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'JOURNAL'")
    op.execute("ALTER TYPE event_type ADD VALUE 'CONTINUOUS_JOURNAL'")

def downgrade():
        op.execute("""DELETE FROM pg_enum
WHERE enumlabel = 'JOURNAL'  OR enumlabel = 'CONTINUOUS_JOURNAL' 
AND enumtypid = (
  SELECT oid FROM pg_type WHERE typname = 'event_type'
)""")

