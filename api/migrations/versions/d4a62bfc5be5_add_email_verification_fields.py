import sqlalchemy as sa
from alembic import op
"""add email verification fields

Revision ID: d4a62bfc5be5
Revises: fbd283484655
Create Date: 2019-02-25 18:46:34.490192

"""

# revision identifiers, used by Alembic.
revision = 'd4a62bfc5be5'
down_revision = 'fbd283484655'


def upgrade():
    op.add_column('app_user', sa.Column(
        'verified_email', sa.Boolean(), nullable=True))
    op.add_column('app_user', sa.Column('verify_token', sa.String(length=255),
                                        nullable=True, unique=True))


def downgrade():
    op.drop_column('app_user', 'verified_email')
    op.drop_column('app_user', 'verify_token')
