"""Add question tag model

Revision ID: 478d1ac3d0ed
Revises: 9143756e596d
Create Date: 2023-08-20 09:31:29.616347

"""

# revision identifiers, used by Alembic.
revision = '478d1ac3d0ed'
down_revision = '9143756e596d'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('registration_question_tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('registration_question_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['registration_question_id'], ['registration_question.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    #op.create_foreign_key('registration_question_registration_question_tag_id_fkey', 'registration_question', 'registration_question_tag', ['id'], ['registration_question_id'])
    
    op.execute("COMMIT")
    op.execute("ALTER TYPE tag_type ADD VALUE 'QUESTION'")
    # ### end Alembic commands ###


def downgrade():
    op.drop_table('registration_question_tag')
    #op.drop_constraint('registration_question_registration_question_tag_id_fkey', 'registration_question', type_='foreignkey')
    
    op.execute("""DELETE FROM pg_enum
        WHERE enumlabel = 'QUESTION'
        AND enumtypid = (
        SELECT oid FROM pg_type WHERE typname = 'tag_type'
        )""")
    # ### end Alembic commands ###