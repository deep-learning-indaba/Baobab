"""Add AI4D Organsation

Revision ID: 88cc4397bdf5
Revises: 742a2a556eb9
Create Date: 2020-08-03 21:53:40.835824

"""

# revision identifiers, used by Alembic.
revision = '88cc4397bdf5'
down_revision = '742a2a556eb9'

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

    ai4d = Organisation('AI4D Africa', 'Baobab', small_logo='ai4d_square_logo.png', large_logo='ai4d_logo.png',
        icon_logo='ai4d_white.png', domain='ai4d', url='http://www.ai4d.ai', email_from='calls@ai4d.ai', 
        system_url='https://baobab.ai4d.ai', privacy_policy='AI4D_privacy_policy_en_fr.pdf', 
        languages=[{"code": "en", "description": "English"}, {"code": "fr", "description": "French"}])

    session.add(ai4d)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.query(Organisation).filter_by(name='AI4D Africa').delete()
    session.commit()
