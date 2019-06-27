"""empty message

Revision ID: 9630ab6b0437
Revises: 57e55dc645c1
Create Date: 2019-06-27 06:39:06.588602

"""

# revision identifiers, used by Alembic.
revision = '9630ab6b0437'
down_revision = '57e55dc645c1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('offer', 'rejected_reason', type_=sa.String(5000))


def downgrade():
    op.alter_column('offer', 'rejected_reason', type_=sa.String(50))
