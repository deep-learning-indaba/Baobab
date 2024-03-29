"""empty message

Revision ID: 02089e6b336b
Revises: 13cec30f2a22
Create Date: 2022-06-28 11:16:33.586716

"""

# revision identifiers, used by Alembic.
revision = '02089e6b336b'
down_revision = '13cec30f2a22'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_invoice_client_reference_id'), 'invoice', ['client_reference_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_invoice_client_reference_id'), table_name='invoice')
    # ### end Alembic commands ###
