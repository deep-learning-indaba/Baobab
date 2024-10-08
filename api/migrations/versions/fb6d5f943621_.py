"""empty message

Revision ID: fb6d5f943621
Revises: d4f153e3cea2
Create Date: 2024-09-16 07:53:51.262038

"""

# revision identifiers, used by Alembic.
revision = 'fb6d5f943621'
down_revision = 'd4f153e3cea2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("CREATE TYPE outcome_status_new AS ENUM ('ACCEPTED', 'REJECTED', 'WAITLIST', 'REVIEW', 'ACCEPT_W_REVISION', 'REJECT_W_ENCOURAGEMENT', 'DESK_REJECTED')")
    op.execute("ALTER TABLE outcome ALTER COLUMN status TYPE outcome_status_new USING status::text::outcome_status_new")
    op.execute("DROP TYPE outcome_status")
    op.execute("ALTER TYPE outcome_status_new RENAME TO outcome_status")

def downgrade():
    op.execute("UPDATE outcome SET status = 'REJECTED' WHERE status = 'DESK_REJECTED'")
    op.execute("CREATE TYPE outcome_status_old AS ENUM ('ACCEPTED', 'REJECTED', 'WAITLIST', 'REVIEW', 'ACCEPT_W_REVISION', 'REJECT_W_ENCOURAGEMENT')")
    op.execute("ALTER TABLE outcome ALTER COLUMN status TYPE outcome_status_old USING status::text::outcome_status_old")
    op.execute("DROP TYPE outcome_status")
    op.execute("ALTER TYPE outcome_status_old RENAME TO outcome_status")
