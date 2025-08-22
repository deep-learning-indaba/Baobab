"""Add MenaML Org

Revision ID: e8eafcfe7800
Revises: d4f153e3cea2
Create Date: 2024-09-19 20:46:21.875864

"""

# revision identifiers, used by Alembic.
revision = 'e8eafcfe7800'
down_revision = 'd4f153e3cea2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime

Base = declarative_base()

class Organisation(Base):

    __tablename__ = "organisation"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    system_name = db.Column(db.String(50), nullable=False)
    small_logo = db.Column(db.String(100), nullable=False)
    large_logo = db.Column(db.String(100), nullable=False)
    icon_logo = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    email_from = db.Column(db.String(100), nullable=True)
    system_url = db.Column(db.String(100), nullable=False)
    privacy_policy = db.Column(db.String(100), nullable=False)
    languages = db.Column(db.JSON(), nullable=False)
    iso_currency_code = db.Column(db.String(3), nullable=True)
    stripe_api_publishable_key = db.Column(db.String(200), nullable=True)
    stripe_api_secret_key = db.Column(db.String(200), nullable=True)
    stripe_webhook_secret_key = db.Column(db.String(200), nullable=True)


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    mena = Organisation(name='MenaML', system_name='MenaML Application Portal', small_logo='menaml_logo_small.png', large_logo='menaml_logo_large.png',
        icon_logo='menaml_logo_small.png', domain='mena', url='https://www.mena.ml', email_from='applications@mena.ml', system_url='https://apply.mena.ml',
        privacy_policy='https://www.mena.ml/about/privacy-policy', languages=['en'], iso_currency_code='USD')

    session.add(mena)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.query(Organisation).filter_by(name='MenaML').delete()
    session.commit()