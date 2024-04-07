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
    # https://blog.yo1.dog/updating-enum-values-in-postgresql-the-safe-and-easy-way/
    op.execute("UPDATE event SET event_type = 'JOURNAL' WHERE event_type = 'CONTINUOUS_JOURNAL'")
    op.execute("ALTER TYPE event_type RENAME TO event_type_old")
    op.execute("CREATE TYPE event_type AS ENUM('EVENT', 'AWARD', 'CALL', 'PROGRAMME', 'JOURNAL')")
    op.execute("ALTER TABLE event ALTER COLUMN event_type TYPE event_type USING event_type::text::event_type")
    op.execute("DROP TYPE event_type_old")


def downgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE event_type ADD VALUE 'CONTINUOUS_JOURNAL'")
