"""empty message

Revision ID: 65f15544a656
Revises: 438ca9e1c2e8
Create Date: 2019-06-26 09:47:56.216999

"""

# revision identifiers, used by Alembic.
revision = '65f15544a656'
down_revision = '438ca9e1c2e8'

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

