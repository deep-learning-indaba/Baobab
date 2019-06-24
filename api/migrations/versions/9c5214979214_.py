"""empty message

Revision ID: 9c5214979214
Revises: 4d5e701eda6e
Create Date: 2019-06-24 07:37:53.501857

"""

# revision identifiers, used by Alembic.
revision = '9c5214979214'
down_revision = '4d5e701eda6e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():

    op.create_table('guest_registration',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('registration_form_id', sa.Integer(), nullable=False),
                    sa.Column('confirmed', sa.Boolean(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('confirmation_email_sent_at', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
                    sa.ForeignKeyConstraint(['registration_form_id'], ['registration_form.id']),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('guest_registration_answer',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('guest_registration_id', sa.Integer(), nullable=False),
                    sa.Column('registration_question_id', sa.Integer(), nullable=False),
                    sa.Column('value', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['guest_registration_id'], ['guest_registration.id']),
                    sa.ForeignKeyConstraint(['registration_question_id'], ['registration_question.id']),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('guest_registration_answer')
    op.drop_table('guest_registration')
