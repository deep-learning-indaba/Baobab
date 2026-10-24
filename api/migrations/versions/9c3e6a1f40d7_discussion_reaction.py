"""Add discussion_reaction table

Revision ID: 9c3e6a1f40d7
Revises: 4b7d2c91e5a8
Create Date: 2026-10-01 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '9c3e6a1f40d7'
down_revision = '4b7d2c91e5a8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'discussion_reaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('emoji', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['discussion_message.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_discussion_reaction_msg_user_emoji'),
    )
    op.create_index('ix_discussion_reaction_message', 'discussion_reaction', ['message_id'])


def downgrade():
    op.drop_index('ix_discussion_reaction_message', table_name='discussion_reaction')
    op.drop_table('discussion_reaction')
