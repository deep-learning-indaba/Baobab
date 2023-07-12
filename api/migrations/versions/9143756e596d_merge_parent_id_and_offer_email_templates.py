"""Merge migration that combines parent_id migration with latest
migrations on develop branch

Revision ID: 9143756e596d
Revises: ('0edb89e87e72', '5d5b0524b4fa')
Create Date: 2023-07-11 07:19:19.202264

"""

# revision identifiers, used by Alembic.
revision = '9143756e596d'
down_revision = ('0edb89e87e72', '5d5b0524b4fa')

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass


def downgrade():
    pass
