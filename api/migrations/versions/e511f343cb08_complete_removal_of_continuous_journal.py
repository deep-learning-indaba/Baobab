"""Complete removal of continuous journal

Revision ID: e511f343cb08
Revises: 81526c9dbb6f
Create Date: 2024-04-02 19:49:24.440649

"""

# revision identifiers, used by Alembic.
revision = 'e511f343cb08'
down_revision = '81526c9dbb6f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""DELETE FROM pg_enum
        WHERE enumlabel = 'CONTINUOUS_JOURNAL' 
        AND enumtypid = (
        SELECT oid FROM pg_type WHERE typname = 'event_type'
        )""")


def downgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'CONTINUOUS_JOURNAL'")
