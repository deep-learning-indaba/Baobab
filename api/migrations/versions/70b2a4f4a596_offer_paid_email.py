"""Add offer paid email template

Revision ID: 70b2a4f4a596
Revises: c1871115c32d
Create Date: 2024-05-19 16:28:24.393772

"""

# revision identifiers, used by Alembic.
revision = '70b2a4f4a596'
down_revision = 'c1871115c32d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
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

Thank you for your payment.
We have now received your registration fee for {event_name}. You may proceed to complete your registration by visiting the link below:
{host}/{event_key}/registration 

Kind Regards,
The {event_name} organisers
"""
    template_fr = """Cher {title} {firstname} {lastname},

Merci pour votre paiement.
Nous avons bien reçu votre frais d'inscription pour {event_name}. Vous pouvez maintenant compléter votre inscription en visitant le lien ci-dessous:
{host}/{event_key}/registration

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('offer-paid', None, '{event_name} Payment Received', template_en, 'en'))
    session.add(EmailTemplate('offer-paid', None, '{event_name} Paiement reçu', template_fr, 'fr'))
    session.commit()


def downgrade():
    op.execute("""DELETE FROM email_template WHERE key='offer-paid'""")
    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")
