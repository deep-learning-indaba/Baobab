"""Add AIMS organisation.

Revision ID: ec9886a36eab
Revises: f4402dcafde3
Create Date: 2023-01-05 11:48:48.260376

"""

# revision identifiers, used by Alembic.
revision = 'ec9886a36eab'
down_revision = 'f4402dcafde3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
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

    # TODO: Upload and use AIMS privacy policy.
    aims = Organisation('AIMS South Africa', 'AIMS Application Centre', small_logo='aims_sa_logo_square.png', large_logo='aims_sa_logo.png',
        icon_logo='aims_sa_logo_square.png', domain='aims', url='http://www.aims.ac.za', email_from='apply@aims.ac.za', 
        system_url='https://apply.aims.ac.za', privacy_policy='PrivacyPolicy.pdf', 
        languages=[{"code": "en", "description": "English"}])

    session.add(aims)
    session.commit()


def downgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    session.query(Organisation).filter_by(name='AIMS South Africa').delete()
    session.commit()
