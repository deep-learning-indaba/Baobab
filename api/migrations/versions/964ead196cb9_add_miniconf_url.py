"""empty message

Revision ID: 964ead196cb9
Revises: 1e05a293f402
Create Date: 2020-06-17 20:40:02.574425

"""

# revision identifiers, used by Alembic.
revision = "964ead196cb9"
down_revision = "1e05a293f402"

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app.events.models import Event

Base = declarative_base()


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    op.add_column(
        "event", sa.Column("miniconf_url", sa.String(length=100), nullable=True)
    )
    event = session.query(Event).filter_by(key="eeml2020").first()
    op.execute(
        """UPDATE event SET miniconf_url = 'miniconf.eeml.eu' WHERE id = {}""".format(
            event.id
        )
    )


def downgrade():
    op.drop_column("event", "miniconf_url")
