"""add offer with grants email template

Revision ID: 15d51e2866ce
Revises: '3e271c360a92'
Create Date: 2023-05-06 07:20:45.567230

"""

# revision identifiers, used by Alembic.
revision = '15d51e2866ce'
down_revision = '3e271c360a92'

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

    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}! We are also pleased to award you the following grants:
{grants}.

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers
"""
    session.add(EmailTemplate('offer-award', None, '{event_name} Application Status Update', template, 'en'))
    template = """Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} ! Nous sommes heureux de vous accorder les bourses suivantes :
{grants}.

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}

"""
    session.add(EmailTemplate('offer-award', None, 'Mise à jour de l’état de la demande pour {event_name}', template, 'fr'))
    session.commit()

def downgrade():
    op.execute("""DELETE FROM email_template WHERE key='offer-award'""")
    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")