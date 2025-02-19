"""add_review_summary_outcome



Revision ID: 0b6fae140f61
Revises: 3fe861d70b76
Create Date: 2025-02-19 19:52:27.330452

"""

# revision identifiers, used by Alembic.
revision: str = '0b6fae140f61'
down_revision: str ='3fe861d70b76'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column(
        'outcome',
        sa.Column('review_summary', sa.String(250), nullable=True)
    )

def downgrade():
    op.drop_column('outcome', 'review_summary')


