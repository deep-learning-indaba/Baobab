"""Add foreign key response_id to outcome

Revision ID: 3fe861d70b76
Revises: 48d559146efd
Create Date: 2025-01-29 00:54:20.105588

"""
# revision identifiers, used by Alembic.
revision = '3fe861d70b76'
down_revision = '48d559146efd'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('outcome', sa.Column('response_id', sa.Integer(), nullable=True))

    op.create_foreign_key(
        'fk_outcome_response_id',
        'outcome',
        'response',
        ['response_id'],
        ['id']
    )

    op.execute("""
        UPDATE outcome
        SET response_id = r.id
        FROM response r, application_form app_form
        WHERE outcome.user_id = r.user_id AND app_form.id = r.application_form_id AND app_form.event_id = outcome.event_id
    """)

    op.alter_column('outcome', 'response_id', nullable=False)
    

def downgrade():
    op.drop_constraint('fk_outcome_response_id', 'outcome', type_='foreignkey')

    op.drop_column('outcome', 'response_id')
