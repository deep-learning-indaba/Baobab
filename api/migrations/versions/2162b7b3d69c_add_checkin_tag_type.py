"""Add checkin tag type.

Revision ID: 2162b7b3d69c
Revises: 2961527fe515
Create Date: 2025-08-10 16:37:25.176529

"""

# revision identifiers, used by Alembic.
revision = '2162b7b3d69c'
down_revision = '2961527fe515'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE VARCHAR(255);")
    op.execute("DROP TYPE IF EXISTS tag_type;")
    op.execute("CREATE TYPE tag_type AS ENUM ('RESPONSE', 'REGISTRATION', 'GRANT', 'QUESTION', 'CHECKIN');")
    op.execute("ALTER TABLE tag ALTER COLUMN tag_type TYPE tag_type USING (tag_type::tag_type);")

def downgrade():
    op.execute("DELETE FROM pg_enum WHERE enumlabel = 'CHECKIN' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tag_type')")
