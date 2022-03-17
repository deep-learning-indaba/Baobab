"""Add Neuroscience Imbizo organisation.

Revision ID: 1afd8dfc8d05
Revises: 07d536b58953
Create Date: 2021-08-09 19:49:19.789293

"""

# revision identifiers, used by Alembic.
revision = "1afd8dfc8d05"
down_revision = "07d536b58953"

import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from app import db

Base = declarative_base()


class Organisation(Base):

    __tablename__ = "organisation"
    __table_args__ = {"extend_existing": True}

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

    def __init__(
        self,
        name,
        system_name,
        small_logo,
        large_logo,
        icon_logo,
        domain,
        url,
        email_from,
        system_url,
        privacy_policy,
        languages,
    ):
        self.name = name
        self.small_logo = small_logo
        self.large_logo = large_logo
        self.icon_logo = icon_logo
        self.domain = domain
        self.system_name = system_name
        self.url = url
        self.email_from = email_from
        self.system_url = system_url
        self.privacy_policy = privacy_policy
        self.languages = languages


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    imbizo = Organisation(
        name="IBRO-Simons Computational Neuroscience Imbizo",
        system_name="Baobab",
        small_logo="imbizo_logo_small.png",
        large_logo="imbizo_logo_large.png",
        icon_logo="imbizo_favicon.png",
        domain="imbizo",
        url="http://imbizo.africa",
        email_from="baobab@imbizo.africa",
        system_url="https://baobab.imbizo.africa",
        privacy_policy="PrivacyPolicy_Imbizo.pdf",
        languages=[{"code": "en", "description": "English"}],
    )

    session.add(imbizo)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.query(Organisation).filter_by(
        name="IBRO-Simons Computational Neuroscience Imbizo"
    ).delete()
    session.commit()
