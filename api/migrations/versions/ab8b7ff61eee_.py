"""empty message

Revision ID: ab8b7ff61eee
Revises: 472bf293e0a1
Create Date: 2019-06-21 11:31:26.876062

"""

# revision identifiers, used by Alembic.
revision = "ab8b7ff61eee"
down_revision = "472bf293e0a1"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "invitation_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("template_path", sa.String(), nullable=False),
        sa.Column("send_for_travel_award_only", sa.Boolean(), nullable=False),
        sa.Column("send_for_accommodation_award_only", sa.Boolean(), nullable=False),
        sa.Column("send_for_both_travel_accommodation", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "invitation_letter_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registration_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("work_address", sa.String(), nullable=False),
        sa.Column("addressed_to", sa.String(), nullable=False),
        sa.Column("residential_address", sa.String(), nullable=False),
        sa.Column("passport_name", sa.String(), nullable=False),
        sa.Column("passport_no", sa.String(), nullable=False),
        sa.Column("passport_issued_by", sa.String(), nullable=False),
        sa.Column("invitation_letter_sent_at", sa.String(), nullable=False),
        sa.Column("to_date", sa.DateTime(), nullable=False),
        sa.Column("from_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["registration.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("invitation_template")
    op.drop_table("invitation_letter_request")
