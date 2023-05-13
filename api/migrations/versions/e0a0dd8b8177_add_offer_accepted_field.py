"""Add accepted field to OfferTag

Revision ID: e0a0dd8b8177
Revises: 6159f64ed381
Create Date: 2023-04-30 12:59:16.895935

"""

# revision identifiers, used by Alembic.
revision = 'e0a0dd8b8177'
down_revision = '6159f64ed381'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('offer_tag', sa.Column('accepted', sa.Boolean(), nullable=True))
    op.execute("""UPDATE offer_tag SET accepted=null""")

def downgrade():
    op.drop_column('offer_tag', 'accepted')
