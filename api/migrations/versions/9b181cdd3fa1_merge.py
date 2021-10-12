"""Merge migration after adding section and question translations

Revision ID: 9b181cdd3fa1
Revises: ('3fb92272089d', '984cb348ec98')
Create Date: 2020-08-15 17:56:36.094515

"""

# revision identifiers, used by Alembic.
revision = "9b181cdd3fa1"
down_revision = ("3fb92272089d", "984cb348ec98")

import sqlalchemy as sa
from alembic import op


def upgrade():
    pass


def downgrade():
    pass
