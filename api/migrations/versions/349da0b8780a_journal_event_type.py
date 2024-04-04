"""Add journal and continuous_journal event_type

Revision ID: 349da0b8780a
Revises: 93f4dbc510f9
Create Date: 2023-02-23 07:50:04.810515

"""

# revision identifiers, used by Alembic.
revision = '349da0b8780a'
down_revision = '93f4dbc510f9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'JOURNAL'")
    op.execute("ALTER TYPE event_type ADD VALUE 'CONTINUOUS_JOURNAL'")

def downgrade():
    op.execute("""DELETE FROM pg_enum
        WHERE enumlabel = 'JOURNAL' OR enumlabel = 'CONTINUOUS_JOURNAL' 
        AND enumtypid = (
        SELECT oid FROM pg_type WHERE typname = 'event_type'
        )""")
