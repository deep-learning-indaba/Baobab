"""Remove the linked-form-question type and form_question.linked_question_id

A form now chooses which of its linked form's answers are shown through
form.settings['linked_display'] instead of one question per answer.

Revision ID: 3f9c2a7d1e64
Revises: b8d41f6a2c95
Create Date: 2026-10-17 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '3f9c2a7d1e64'
down_revision = 'b8d41f6a2c95'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Display-only, so there should be no answers, but any stray ones would
    # block the delete through form_answer's foreign key.
    op.execute("""
        DELETE FROM form_answer WHERE question_id IN (
            SELECT id FROM form_question WHERE type = 'linked-form-question'
        )
    """)
    op.execute("""
        DELETE FROM form_question_translation WHERE form_question_id IN (
            SELECT id FROM form_question WHERE type = 'linked-form-question'
        )
    """)
    op.execute("""
        UPDATE form_question SET linked_question_id = NULL WHERE linked_question_id IN (
            SELECT id FROM form_question WHERE type = 'linked-form-question'
        )
    """)
    op.execute("DELETE FROM form_question WHERE type = 'linked-form-question'")

    op.drop_constraint('form_question_linked_question_id_fkey', 'form_question', type_='foreignkey')
    op.drop_column('form_question', 'linked_question_id')


def downgrade():
    op.add_column('form_question', sa.Column('linked_question_id', sa.Integer(), nullable=True))
    op.create_foreign_key('form_question_linked_question_id_fkey', 'form_question', 'form_question',
                          ['linked_question_id'], ['id'])
