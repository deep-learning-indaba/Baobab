"""Add icon field to organisation and swap small logo into icon

Revision ID: 7f37bf248c81
Revises: 2279e1fa2e49
Create Date: 2020-05-23 22:05:35.967772

"""

# revision identifiers, used by Alembic.
revision = '7f37bf248c81'
down_revision = '2279e1fa2e49'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('organisation', sa.Column('icon_logo', sa.String(length=100), nullable=True))
    op.execute("""UPDATE organisation SET icon_logo=small_logo""")
    op.execute("""UPDATE organisation SET small_logo='indaba_logo_cufflink_small.png' WHERE system_name IN ('Baobab', 'Baobab Dev', 'integration_test')""")
    op.execute("""UPDATE organisation SET small_logo='eeml_logo_black_small.png' WHERE system_name IN ('EEML Portal')""")
    op.alter_column('organisation', 'icon_logo', existing_type=sa.String(), nullable=False)


def downgrade():
    op.drop_column('organisation', 'icon_logo')
    op.execute("""UPDATE organisation SET small_logo='logo-32x32-white.png' WHERE system_name IN ('Baobab', 'Baobab Dev', 'integration_test')""")
    op.execute("""UPDATE organisation SET small_logo='logo_eeml_white.png' WHERE system_name IN ('EEML Portal')""")
