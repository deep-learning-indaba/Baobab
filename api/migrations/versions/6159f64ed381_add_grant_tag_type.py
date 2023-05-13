"""empty message

Revision ID: 6159f64ed381
Revises: ae7c72f05201
Create Date: 2023-04-29 04:50:11.882690

"""

# revision identifiers, used by Alembic.
revision = '6159f64ed381'
down_revision = 'ae7c72f05201'

from alembic import op

def upgrade():
    op.execute("COMMIT")
    op.execute("ALTER TYPE tag_type ADD VALUE 'GRANT'")

def downgrade():
    op.execute("""DELETE FROM pg_enum
        WHERE enumlabel = 'GRANT'
        AND enumtypid = (
        SELECT oid FROM pg_type WHERE typname = 'tag_type'
        )""")
