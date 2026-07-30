"""Record an announcement's audience so it can be resent

Revision ID: e7b3a95c1d48
Revises: d4c81b6f9a02
Create Date: 2026-07-30 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'e7b3a95c1d48'
down_revision = 'd4c81b6f9a02'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Nullable with no default: an existing announcement's audience was never
    # recorded, and guessing one would be worse than a resend asking for it.
    op.add_column('announcement', sa.Column('critical', sa.Boolean(), nullable=True))
    op.add_column('announcement', sa.Column('target_audience', sa.String(length=16), nullable=True))
    op.add_column('announcement', sa.Column('tag_id', sa.Integer(), nullable=True))
    op.create_foreign_key('announcement_tag_id_fkey', 'announcement', 'tag', ['tag_id'], ['id'])


def downgrade():
    op.drop_constraint('announcement_tag_id_fkey', 'announcement', type_='foreignkey')
    op.drop_column('announcement', 'tag_id')
    op.drop_column('announcement', 'target_audience')
    op.drop_column('announcement', 'critical')
