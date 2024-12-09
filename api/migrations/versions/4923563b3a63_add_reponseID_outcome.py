""" Add foreign key response_id to outcome

Revision ID: 4923563b3a63
Revises: bf4cb562e36c
Create Date: 2024-12-07 19:07:18.021334

"""

# revision identifiers, used by Alembic.
revision = '4923563b3a63'
down_revision = 'bf4cb562e36c'


from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'outcome',
        sa.Column('response_id', sa.Integer(), nullable=False)
    )

    op.create_foreign_key(
        'fk_outcome_response_id',  
        'outcome',  
        'response', 
        ['response_id'],  
        ['id'] 
    )


def downgrade():
    op.drop_constraint(
        'fk_outcome_response_id', 
        'outcome', 
        type_='foreignkey'
    )

    op.drop_column('outcome', 'response_id')


