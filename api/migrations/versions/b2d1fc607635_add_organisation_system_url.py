"""empty message

Revision ID: b2d1fc607635
Revises: 29dd5b8bc663
Create Date: 2020-02-02 21:57:33.212329

"""

# revision identifiers, used by Alembic.
revision = "b2d1fc607635"
down_revision = "29dd5b8bc663"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.add_column(
        "organisation", sa.Column("system_url", sa.String(length=100), nullable=True)
    )

    op.execute(
        """UPDATE organisation SET system_url = 'test-baobab.deeplearningindaba.com' WHERE id = 1"""
    )
    op.execute(
        """UPDATE organisation SET system_url = 'test-portal.eeml.eu' WHERE id = 2"""
    )
    op.execute("""UPDATE organisation SET system_url = 'localhost' WHERE id = 3""")

    op.alter_column("organisation", "system_url", nullable=False)


def downgrade():
    op.drop_column("organisation", "system_url")
