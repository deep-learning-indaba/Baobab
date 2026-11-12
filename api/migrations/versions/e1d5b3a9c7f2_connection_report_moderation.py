"""Add moderation columns to connection_report.

Revision ID: e1d5b3a9c7f2
Revises: c4a7e19d2b53
Create Date: 2026-11-12 11:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'e1d5b3a9c7f2'
down_revision = 'c4a7e19d2b53'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('connection_report', sa.Column('category', sa.String(length=16), nullable=False, server_default='person'))
    op.add_column('connection_report', sa.Column('reported_photo_url', sa.String(length=512), nullable=True))
    op.add_column('connection_report', sa.Column('status', sa.String(length=16), nullable=False, server_default='open'))
    op.add_column('connection_report', sa.Column('resolved_by_user_id', sa.Integer(), nullable=True))
    op.add_column('connection_report', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_connection_report_resolved_by', 'connection_report', 'app_user',
                          ['resolved_by_user_id'], ['id'])
    op.create_index('ix_connection_report_event_status', 'connection_report', ['event_id', 'status'])


def downgrade():
    op.drop_index('ix_connection_report_event_status', table_name='connection_report')
    op.drop_constraint('fk_connection_report_resolved_by', 'connection_report', type_='foreignkey')
    op.drop_column('connection_report', 'resolved_at')
    op.drop_column('connection_report', 'resolved_by_user_id')
    op.drop_column('connection_report', 'status')
    op.drop_column('connection_report', 'reported_photo_url')
    op.drop_column('connection_report', 'category')
