"""Add new outcomes

Revision ID: 48d559146efd
Revises: a4662031beca
Create Date: 2025-01-28 17:11:21.400338

"""
# revision identifiers, used by Alembic.
revision = '48d559146efd'
down_revision = 'a4662031beca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("ALTER TYPE outcome_status ADD VALUE 'REVIEW';")
    op.execute("ALTER TYPE outcome_status ADD VALUE 'ACCEPT_W_REVISION';")
    op.execute("ALTER TYPE outcome_status ADD VALUE 'REJECT_W_ENCOURAGEMENT';")


def downgrade():
    op.execute("""
    DO $$ 
    BEGIN 
        ALTER TYPE outcome_status RENAME TO outcome_status_old;
        CREATE TYPE outcome_status AS ENUM('ACCEPTED', 'REJECTED', 'WAITLIST');
        ALTER TABLE outcome 
        ALTER COLUMN status 
        TYPE outcome_status 
        USING status::text::outcome_status;
        DROP TYPE outcome_status_old;
    END $$;
    """)