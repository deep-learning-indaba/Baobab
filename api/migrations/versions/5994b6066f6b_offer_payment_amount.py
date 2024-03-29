"""Add payment amount to offer

Revision ID: 5994b6066f6b
Revises: fd232b2eed5e
Create Date: 2022-05-24 21:28:07.188861

"""

# revision identifiers, used by Alembic.
revision = '5994b6066f6b'
down_revision = 'fd232b2eed5e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offer', sa.Column('payment_amount', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('offer', 'payment_amount')
    # ### end Alembic commands ###
