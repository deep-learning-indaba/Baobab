"""Add outbox_message queue for async email and push delivery

Revision ID: d4c81b6f9a02
Revises: b3d9f4a12c7e
Create Date: 2026-07-30 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'd4c81b6f9a02'
down_revision = 'b3d9f4a12c7e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'outbox_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organisation_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=16), nullable=False),
        sa.Column('recipient', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('sender_name', sa.String(length=100), nullable=True),
        sa.Column('sender_email', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('claim_token', sa.String(length=36), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'source_id', 'channel', 'user_id',
                            name='uq_outbox_source_channel_user'),
    )
    op.create_index('ix_outbox_claimable', 'outbox_message', ['status', 'scheduled_at'])
    op.create_index('ix_outbox_source', 'outbox_message', ['source_type', 'source_id'])


def downgrade():
    op.drop_index('ix_outbox_source', table_name='outbox_message')
    op.drop_index('ix_outbox_claimable', table_name='outbox_message')
    op.drop_table('outbox_message')
