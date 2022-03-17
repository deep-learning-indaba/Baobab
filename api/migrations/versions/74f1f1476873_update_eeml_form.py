"""empty message

Revision ID: 74f1f1476873
Revises: 87213d612eaf
Create Date: 2020-02-06 17:21:37.083255

"""

# revision identifiers, used by Alembic.
revision = "74f1f1476873"
down_revision = "87213d612eaf"

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.execute(
        r"""UPDATE question SET validation_regex='^\W*(\w+(\W+|$)){150,500}$', validation_text='You must enter between 150 and 500 words' WHERE headline='Research Interests' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET validation_regex='^\W*(\w+(\W+|$)){0,150}$', validation_text='You must enter fewer than 150 words' WHERE headline='Motivation' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET description='Upload your extended abstract (PDF, max size 10MB)' where headline='Extended abstract' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET description='Upload your CV (PDF, max size 10MB)' where headline='CV' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE organisation SET system_url='https://test-baobab.deeplearningindaba.com' where id=1"""
    )
    op.execute(
        r"""UPDATE organisation SET system_url='https://test-portal.eeml.eu' where id=2"""
    )
    op.execute(r"""UPDATE organisation SET system_url='http://localhost' where id=3""")


def downgrade():
    op.execute(
        r"""UPDATE question SET validation_regex='^.{500,2000}$', validation_text='You must enter between 500 and 2000 characters' WHERE headline='Research Interests' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET validation_regex='^.{0,500}$', validation_text='Maximum 500 characters' WHERE headline='Motivation' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET description='' where headline='Extended abstract' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE question SET description='' where headline='CV' and application_form_id=2"""
    )
    op.execute(
        r"""UPDATE organisation SET system_url='test-baobab.deeplearningindaba.com' where id=1"""
    )
    op.execute(
        r"""UPDATE organisation SET system_url='test-portal.eeml.eu' where id=2"""
    )
    op.execute(r"""UPDATE organisation SET system_url='localhost' where id=3""")
