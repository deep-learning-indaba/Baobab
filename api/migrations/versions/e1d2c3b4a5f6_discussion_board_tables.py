"""Event app: discussion board tables.

Revision ID: e1d2c3b4a5f6
Revises: 724757fece76
Create Date: 2026-07-09 10:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'e1d2c3b4a5f6'
down_revision = '724757fece76'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'discussion_thread',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_discussion_thread_event_activity', 'discussion_thread',
                    ['event_id', 'last_activity_at'])

    op.create_table(
        'discussion_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('body_markdown', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('deleted_by', sa.String(length=16), nullable=True),
        sa.Column('deleted_reason', sa.String(length=500), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['discussion_thread.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.ForeignKeyConstraint(['parent_message_id'], ['discussion_message.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_discussion_message_thread', 'discussion_message',
                    ['thread_id', 'created_at'])

    op.create_table(
        'discussion_subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscribed', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['discussion_thread.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id', 'user_id', name='uq_discussion_sub_thread_user'),
    )

    op.create_table(
        'discussion_read',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['discussion_thread.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id', 'user_id', name='uq_discussion_read_thread_user'),
    )

    op.create_table(
        'discussion_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('reporter_user_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['discussion_message.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['reporter_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'reporter_user_id', name='uq_discussion_report_msg_reporter'),
    )


def downgrade():
    op.drop_table('discussion_report')
    op.drop_table('discussion_read')
    op.drop_table('discussion_subscription')
    op.drop_index('ix_discussion_message_thread', table_name='discussion_message')
    op.drop_table('discussion_message')
    op.drop_index('ix_discussion_thread_event_activity', table_name='discussion_thread')
    op.drop_table('discussion_thread')
