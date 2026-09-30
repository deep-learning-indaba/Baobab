"""Add offer reset email template

Revision ID: 4b7d2c91e5a8
Revises: 7ee0f8e22237
Create Date: 2026-09-30 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = '4b7d2c91e5a8'
down_revision = '7ee0f8e22237'

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

    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")

    template_en = """Dear {title} {firstname} {lastname},

Your offer for {event_name} has been reset, so you can respond to it again.
Please visit the link below to accept or decline your offer by {expiry_date}:
{host}/{event_key}/offer

If you have any questions, contact us at {event_email_from}.

Kind Regards,
The {event_name} organisers
"""
    template_fr = """Cher {title} {firstname} {lastname},

Votre offre pour {event_name} a été réinitialisée, vous pouvez donc y répondre à nouveau.
Veuillez visiter le lien ci-dessous pour accepter ou refuser votre offre avant le {expiry_date} :
{host}/{event_key}/offer

Si vous avez des questions, contactez-nous à {event_email_from}.

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('offer-reset', None, '{event_name} Offer Reset', template_en, 'en'))
    session.add(EmailTemplate('offer-reset', None, '{event_name} Offre réinitialisée', template_fr, 'fr'))
    session.commit()


def downgrade():
    op.execute("""DELETE FROM email_template WHERE key='offer-reset'""")
    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")
