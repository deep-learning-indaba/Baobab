""" Add new status outcome

Revision ID: bf4cb562e36c
Revises: 062abca36566
Create Date: 2024-12-07 19:05:30.962104

"""
# revision identifiers, used by Alembic.
revision = 'bf4cb562e36c'
down_revision = '062abca36566'

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

