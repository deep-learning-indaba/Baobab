"""Add indexes for answer lookups

Revision ID: ef75fde5102c
Revises: 478d1ac3d0ed
Create Date: 2023-08-26 17:17:21.927515

"""

# revision identifiers, used by Alembic.
revision = 'ef75fde5102c'
down_revision = '478d1ac3d0ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('answer_question_lookup', 'answer', ['question_id', 'response_id', 'is_active'])
    op.create_index('answer_response_lookup', 'answer', ['response_id', 'is_active'])
    op.create_index('registration_answer_lookup', 'registration_answer', ['registration_id', 'registration_question_id'])
    op.create_index('guest_registration_answer_lookup', 'guest_registration_answer', ['guest_registration_id', 'registration_question_id', 'is_active'])
    op.create_index('invited_guest_lookup', 'invited_guest', ['event_id', 'user_id'])
    op.create_index('invited_guest_event_lookup', 'invited_guest', ['event_id'])

def downgrade():
    op.drop_index('answer_question_lookup', table_name='answer')
    op.drop_index('answer_response_lookup', table_name='answer')
    op.drop_index('registration_answer_lookup', table_name='registration_answer')
    op.drop_index('guest_registration_answer_lookup', table_name='guest_registration_answer')
    op.drop_index('invited_guest_lookup', table_name='invited_guest')
    op.drop_index('invited_guest_event_lookup', table_name='invited_guest')
