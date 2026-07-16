"""Event app: discussion spaces (hierarchical grouping of threads).

Discussion board is new and only has test data in any environment so far,
so rather than backfilling existing threads into a synthetic space, this
migration just clears the existing discussion data and adds a NOT NULL
space_id straight away.

Revision ID: 7a1f9d2c6b4e
Revises: 9f2a7c1d4e3b
Create Date: 2026-07-16 09:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '7a1f9d2c6b4e'
down_revision = '9f2a7c1d4e3b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'discussion_space',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subscribe_on_reply', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_discussion_space_event', 'discussion_space', ['event_id', 'position'])

    # Pre-existing discussion data is only ever test content at this point;
    # clear it out (FK-safe order) rather than backfill a synthetic space.
    op.execute('DELETE FROM discussion_report')
    op.execute('DELETE FROM discussion_subscription')
    op.execute('DELETE FROM discussion_read')
    op.execute('DELETE FROM discussion_message')
    op.execute('DELETE FROM discussion_thread')

    op.add_column('discussion_thread', sa.Column('space_id', sa.Integer(), nullable=False))
    op.create_index('ix_discussion_thread_space', 'discussion_thread', ['space_id'])
    op.create_foreign_key(
        'fk_discussion_thread_space_id', 'discussion_thread', 'discussion_space',
        ['space_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_discussion_thread_space_id', 'discussion_thread', type_='foreignkey')
    op.drop_index('ix_discussion_thread_space', table_name='discussion_thread')
    op.drop_column('discussion_thread', 'space_id')

    op.drop_index('ix_discussion_space_event', table_name='discussion_space')
    op.drop_table('discussion_space')
