"""Add IndabaX South Africa Organisation

Revision ID: 0462d1a06d40
Revises: cebfdfef31cd
Create Date: 2023-04-30 17:59:15.333615

"""

# revision identifiers, used by Alembic.
revision = '0462d1a06d40'
down_revision = 'cebfdfef31cd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

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

    def __init__(self, name, system_name, small_logo, large_logo, icon_logo, domain, url, email_from, system_url, privacy_policy, languages):
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

    aims = Organisation(
        name='Deep Learning IndabaX South Africa',
        system_name='Baobab',
        small_logo='dlxza_logo_white.png',
        large_logo='dlxza_logo_white.png',
        icon_logo='dlxza_logo_white.png',
        domain='indabax',
        url='https://indabax.co.za',
        email_from='apply@indabax.co.za', 
        system_url='https://apply.indabax.co.za',
        privacy_policy='PrivacyPolicy.pdf', 
        languages=[{"code": "en", "description": "English"}]
    )

    session.add(aims)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.query(Organisation).filter_by(name='Deep Learning IndabaX South Africa').delete()
    session.commit()
