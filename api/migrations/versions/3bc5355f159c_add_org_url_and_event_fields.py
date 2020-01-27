"""Add organisation URL and other missing event fields.

Revision ID: 3bc5355f159c
Revises: 99cfdad9869c
Create Date: 2020-01-27 15:48:21.870354

"""

# revision identifiers, used by Alembic.
revision = '3bc5355f159c'
down_revision = '99cfdad9869c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('email_from', sa.String(length=255), nullable=True))
    op.add_column('event', sa.Column('key', sa.String(length=255), nullable=True))
    op.add_column('event', sa.Column('organisation_id', sa.Integer(), nullable=True))
    op.add_column('event', sa.Column('url', sa.String(length=255), nullable=True))
    op.create_unique_constraint('unique_event_key', 'event', ['key'])
    op.create_foreign_key('fk_event_organisation', 'event', 'organisation', ['organisation_id'], ['id'])
    op.add_column('organisation', sa.Column('url', sa.String(length=100), nullable=True))

    op.execute("""UPDATE organisation SET url = 'http://www.deeplearningindaba.com' WHERE id = 1""")
    op.execute("""UPDATE organisation SET url = 'http://eeml.eu' WHERE id = 2""")
    op.execute("""UPDATE organisation SET url = 'http://www.deeplearningindaba.com' WHERE id = 3""")

    op.execute("""UPDATE event SET email_from = 'baobab@deeplearningindaba.com', key='indaba2019', organisation_id=1, url='www.deeplearningindaba.com' WHERE id = 1""")

    op.alter_column('event', 'email_from', nullable=False)
    op.alter_column('event', 'key', nullable=False)
    op.alter_column('event', 'organisation_id', nullable=False)
    op.alter_column('event', 'url', nullable=False)
    op.alter_column('organisation', 'url', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('organisation', 'url')
    op.drop_constraint('fk_event_organisation', 'event', type_='foreignkey')
    op.drop_constraint('unique_event_key', 'event', type_='unique')
    op.drop_column('event', 'url')
    op.drop_column('event', 'organisation_id')
    op.drop_column('event', 'key')
    op.drop_column('event', 'email_from')
    # ### end Alembic commands ###
