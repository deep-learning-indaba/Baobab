"""Add keys to sections and questions

Revision ID: e3e47585f336
Revises: c3c5ef958ca1
Create Date: 2020-03-26 22:30:54.888031

"""

# revision identifiers, used by Alembic.
revision = "e3e47585f336"
down_revision = "c3c5ef958ca1"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column("question", sa.Column("key", sa.String(length=255), nullable=True))
    op.add_column("section", sa.Column("key", sa.String(length=255), nullable=True))
    op.execute(
        """UPDATE Question
        SET key = 'nomination_title'
        FROM Section
        WHERE 
        Question.section_id = Section.id
        AND Headline = 'Title'
        AND Section.name IN ('Nominee Information', 'Doctoral Candidate Information', 'Masters Candidate Information')"""
    )
    op.execute(
        """UPDATE question SET key='nomination_firstname' WHERE headline='Firstname'"""
    )
    op.execute(
        """UPDATE question SET key='nomination_lastname' WHERE headline='Lastname'"""
    )
    op.execute(
        """UPDATE question SET key='nomination_email' WHERE headline='Email Address'"""
    )

    op.execute(
        """UPDATE Section SET key='nominee_section' WHERE name IN ('Nominee Information', 'Doctoral Candidate Information', 'Masters Candidate Information')"""
    )
    op.execute(
        """UPDATE Question SET key='nominating_capacity' WHERE headline IN ('Nominating Capacity', 'Nomination Capacity')"""
    )


def downgrade():
    op.drop_column("section", "key")
    op.drop_column("question", "key")
