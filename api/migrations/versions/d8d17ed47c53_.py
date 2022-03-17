"""empty message

Revision ID: d8d17ed47c53
Revises: 1993beca93d7
Create Date: 2020-02-06 15:15:58.466396

"""

# revision identifiers, used by Alembic.
revision = "d8d17ed47c53"
down_revision = "1993beca93d7"

import sqlalchemy as sa
from alembic import op


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "reference_request",
        sa.Column("reference_submitted", sa.Boolean(), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("reference_request", "reference_submitted")
    # ### end Alembic commands ###
