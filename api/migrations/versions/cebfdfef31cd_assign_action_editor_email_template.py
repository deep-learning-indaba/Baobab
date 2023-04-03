"""Adding email templates for assigning an action editor to a journal application

Revision ID: cebfdfef31cd
Revises: 6a073dd1e30d
Create Date: 2023-03-02 14:03:29.661901

"""

# revision identifiers, used by Alembic.
revision = 'cebfdfef31cd'
down_revision = '6a073dd1e30d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

Base = declarative_base()



class EmailTemplate(Base):

    __tablename__ = 'email_template'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer(), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    template = db.Column(db.String(), nullable=False)
    subject = db.Column(db.String(), nullable=False)

    def __init__(self, key, event_id, subject, template, language):
        self.key = key
        self.event_id = event_id
        self.subject = subject
        self.template = template
        self.language = language


def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    template = """Dear {title} {firstname} {lastname},
    
A new application for {event_name} was received. Please assign an action editor to this application as soon as possible.

"""

    session.add(EmailTemplate('assign-action-editor', None, '{event_name} Response Receieved', template, 'en'))

    template = """Dear {title} {firstname} {lastname},
    
A new application for {event_name} was received but has not been assigned to an action editor yet. Please assign an action editor to this application as soon as possible.

"""

    session.add(EmailTemplate('action-editor-not-assigned', None, '{event_name} Action Editor ', template, 'en'))

    session.commit()



def downgrade():
    added_keys = ['assign-action-editor', 'action-editor-not-assigned']
    op.execute("""DELETE FROM email_template WHERE key in ({})""".format(', '.join(["'" + k + "'" for k in added_keys])))
    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")

