"""Add active flag to ResponseReviewer model.

Revision ID: 2e81ebc8d90a
Revises: 2717ef90a874
Create Date: 2020-03-03 08:22:02.358816

"""

# revision identifiers, used by Alembic.
revision = '2e81ebc8d90a'
down_revision = '2717ef90a874'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('response_reviewer', sa.Column('active', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('response_reviewer', 'active')
    # ### end Alembic commands ###
