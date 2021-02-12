"""Update reset-password email template

Revision ID: 613df2d7a759
Revises: 10b4b888c16b
Create Date: 2020-09-08 20:25:05.383106

"""

# revision identifiers, used by Alembic.
revision = '613df2d7a759'
down_revision = '10b4b888c16b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""UPDATE email_template SET subject = '{system_name} Password Reset' where key = 'password-reset' and language='en'""")


def downgrade():
    op.execute("""UPDATE email_template SET subject = '{system} Password Reset' where key = 'password-reset' and language='en'""")
