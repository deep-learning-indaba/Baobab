"""Add privacy policy to organisation

Revision ID: c3b4ca7ceef9
Revises: 74f1f1476873
Create Date: 2020-02-06 18:08:01.476297

"""

# revision identifiers, used by Alembic.
revision = 'c3b4ca7ceef9'
down_revision = '74f1f1476873'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('organisation', sa.Column('privacy_policy', sa.String(length=100), nullable=True))
    op.execute("""UPDATE organisation set privacy_policy='PrivacyPolicy.pdf' WHERE id in (1, 3)""")
    op.execute("""UPDATE organisation set privacy_policy='EEML_PrivacyPolicy.pdf' WHERE id = 2""")
    op.alter_column('organisation', 'privacy_policy', nullable=False)


def downgrade():
    op.drop_column('organisation', 'privacy_policy')
    
