"""empty message

Revision ID: 910e74b87f06
Revises: 742a2a556eb9
Create Date: 2020-07-28 18:17:32.401692

"""

# revision identifiers, used by Alembic.
revision = "910e74b87f06"
down_revision = "742a2a556eb9"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "event_translation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "language", name="uq_event_id_language"),
    )

    op.execute(
        "INSERT INTO event_translation (event_id, name, description, language) SELECT id, name, description, 'en' FROM event"
    )


def downgrade():
    op.drop_table("event_translation")
