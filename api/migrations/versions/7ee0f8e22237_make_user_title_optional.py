"""Make user title optional and add {salutation} to email templates

Revision ID: 7ee0f8e22237
Revises: c3f81a6e2d47
Create Date: 2026-09-27 14:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '7ee0f8e22237'
down_revision = 'c3f81a6e2d47'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('app_user', 'user_title', existing_type=sa.String(length=20), nullable=True)

    # {salutation} renders the title only when the user has one, so users
    # without a title aren't greeted with a stray double space.
    op.execute("""UPDATE email_template
        SET template = REPLACE(template, '{title} {firstname} {lastname}', '{salutation}')
        WHERE template LIKE '%{title} {firstname} {lastname}%'""")


def downgrade():
    op.execute("""UPDATE email_template
        SET template = REPLACE(template, '{salutation}', '{title} {firstname} {lastname}')
        WHERE template LIKE '%{salutation}%'""")

    op.execute("UPDATE app_user SET user_title = '' WHERE user_title IS NULL")
    op.alter_column('app_user', 'user_title', existing_type=sa.String(length=20), nullable=False)
