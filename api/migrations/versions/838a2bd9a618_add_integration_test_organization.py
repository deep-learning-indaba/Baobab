"""
Creates a test organization to be used by integration tests

Revision ID: 838a2bd9a618
Revises: c3c5ef958ca1
Create Date: 2020-02-29 10:03:37.020300

"""

# revision identifiers, used by Alembic.
from sqlalchemy.sql import table, column
import sqlalchemy as sa
from alembic import op
revision = '838a2bd9a618'
down_revision = 'c3c5ef958ca1'


def upgrade():
    organisation = table('organisation',
                         sa.Column('id', sa.Integer(), nullable=False),
                         sa.Column('name', sa.String(
                             length=50), nullable=False),
                         sa.Column('small_logo', sa.String(
                             length=100), nullable=False),
                         sa.Column('large_logo', sa.String(
                             length=100), nullable=False),
                         sa.Column('domain', sa.String(
                             length=100), nullable=False),
                         sa.Column('url', sa.String(100), nullable=False),
                         sa.Column('email_from', sa.String(
                             100), nullable=True),
                         sa.Column('system_url', sa.String(
                             100), nullable=False),
                         sa.Column('privacy_policy', sa.String(
                             100), nullable=False),
                         sa.Column('system_name', sa.String(
                             100), nullable=False)
                         )

    op.bulk_insert(organisation,
                   [
                       {
                           'id': 4,
                           'name': 'Cypress Integration Test',
                           'small_logo': 'logo-32x32-white.png',
                           'large_logo': 'indaba-logo-dark.png',
                           'domain': 'webappintegration',
                           'url': 'www.deeplearningindaba.com',
                           'email_from': 'Integration Test',
                           'system_url': 'Integration Test',
                           'privacy_policy': 'PrivacyPolicy.pdf',
                           'system_name': 'integration_test'
                       }
                   ]
                   )
    op.get_bind().execute(
        """SELECT setval('organisation_id_seq', (SELECT max(id) FROM organisation));""")


def downgrade():
    op.get_bind().execute('DELETE FROM organisation where id = 4')

    op.get_bind().execute(
        """SELECT setval('organisation_id_seq', (SELECT max(id) FROM organisation));""")
