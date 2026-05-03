"""Add offer_note tag type.

Revision ID: a1b2c3d4e5f6
Revises: 7fb62ea19309
Create Date: 2026-05-03 17:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7fb62ea19309'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE VARCHAR(255);")
    op.execute("DROP TYPE IF EXISTS tag_type;")
    op.execute("CREATE TYPE tag_type AS ENUM ('RESPONSE', 'REGISTRATION', 'GRANT', 'QUESTION', 'CHECKIN', 'OFFER_NOTE');")
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE tag_type USING (tag_type::tag_type);")

def downgrade():
    op.execute("DELETE FROM pg_enum WHERE enumlabel = 'OFFER_NOTE' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tag_type')")
