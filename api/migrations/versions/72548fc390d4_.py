"""empty message

Revision ID: 72548fc390d4
Revises: 0023aeda53b0
Create Date: 2020-02-12 18:47:24.439244

"""

# revision identifiers, used by Alembic.
revision = "72548fc390d4"
down_revision = "0023aeda53b0"

import sqlalchemy as sa
from alembic import op


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "app_user", sa.Column("policy_agreed_datetime", sa.DateTime(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("app_user", "policy_agreed_datetime")
    # ### end Alembic commands ###
