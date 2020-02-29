"""Set travel_award and accommodation_award columns to non-nullable booleans

Revision ID: 57e55dc645c1
Revises: 3ab678fc66cd
Create Date: 2019-06-23 11:44:39.345362

"""

# revision identifiers, used by Alembic.
revision = '57e55dc645c1'
down_revision = '3ab678fc66cd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('offer', 'travel_award')
    op.add_column('offer', sa.Column('travel_award', sa.Boolean(), nullable=False))
    op.alter_column('offer', 'accommodation_award',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade():
    op.drop_column('offer', 'travel_award')
    op.add_column('offer', sa.Column('travel_award', sa.String(), nullable=False))
    op.alter_column('offer', 'accommodation_award',
               existing_type=sa.BOOLEAN(),
               nullable=True)
