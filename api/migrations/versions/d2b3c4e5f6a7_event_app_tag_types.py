"""Event app: add INTEREST, TRACK, SESSION_TYPE to tag_type enum (migration B).

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3d4e5f6
Create Date: 2026-06-14 10:01:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'd2b3c4e5f6a7'
down_revision = 'c1a2b3d4e5f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE VARCHAR(255);")
    op.execute("DROP TYPE IF EXISTS tag_type;")
    op.execute(
        "CREATE TYPE tag_type AS ENUM ("
        "'RESPONSE', 'REGISTRATION', 'GRANT', 'QUESTION', 'CHECKIN', 'OFFER_NOTE', "
        "'INTEREST', 'TRACK', 'SESSION_TYPE'"
        ");"
    )
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE tag_type USING (tag_type::tag_type);")


def downgrade():
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE VARCHAR(255);")
    op.execute("DROP TYPE IF EXISTS tag_type;")
    op.execute(
        "CREATE TYPE tag_type AS ENUM ("
        "'RESPONSE', 'REGISTRATION', 'GRANT', 'QUESTION', 'CHECKIN', 'OFFER_NOTE'"
        ");"
    )
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE tag_type USING (tag_type::tag_type);")
