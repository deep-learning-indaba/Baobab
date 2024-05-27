"""Add offer fee and nofee templates

Revision ID: 27422dc8a123
Revises: 21018201594d
Create Date: 2024-05-27 21:15:33.571251

"""

# revision identifiers, used by Alembic.
revision = '27422dc8a123'
down_revision = '21018201594d'

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

    ######## FEE, NO GRANTS ########

    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

Registration Fee:
- In order to confirm you place, you will need to pay a registration fee of {payment_amount} {payment_currency}.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers"""
    session.add(EmailTemplate('offer-fee', None, '{event_name} Application Status Update', template, 'en'))

    template = """Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} !

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Frais d'inscription :
Le paiement de {payment_amount} {payment_currency} est requis pour confirmer votre place. 

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('offer-fee', None, '{event_name} Application Status Update', template, 'fr'))

    ######## NO FEE, NO GRANTS ########
    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

Registration Fee:
- Your registration fee has been waived.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers"""
    session.add(EmailTemplate('offer-nofee', None, '{event_name} Application Status Update', template, 'en'))

    template = """Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} !

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Frais d'inscription :
- Vos frais d'inscription ont été dispensés.

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('offer-nofee', None, '{event_name} Application Status Update', template, 'fr'))

    ######## FEE, GRANTS ########

    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

In addition, we are pleased to offer you the following grants:
{grants}

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

Registration Fee:
- In order to confirm you place, you will need to pay a registration fee of {payment_amount} {payment_currency}.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers"""
    session.add(EmailTemplate('offer-fee-grants', None, '{event_name} Application Status Update', template, 'en'))

    template = """Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} !

Votre offre comprend également les subventions suivantes :
{grants}

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Frais d'inscription :
Le paiement de {payment_amount} {payment_currency} est requis pour confirmer votre place. 

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('offer-fee-grants', None, '{event_name} Application Status Update', template, 'fr'))

    ######## NO FEE, GRANTS ########
    template = """Dear {title} {firstname} {lastname},

Congratulations! You've been selected for {event_name}!

In addition, we are pleased to offer you the following grants:
{grants}

Please follow the link below to see details and accept your offer: {host}/offer
You have up until {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

Registration Fee:
- Your registration fee has been waived.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you, we may extend you a new offer in a subsequent round.

If you have any queries, please contact us at {event_email_from}

Kind Regards,
The {event_name} organisers"""
    session.add(EmailTemplate('offer-nofee-grants', None, '{event_name} Application Status Update', template, 'en'))

    template = """Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} !

Votre offre comprend également les subventions suivantes :
{grants}

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Frais d'inscription :
- Vos frais d'inscription ont été dispensés.

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('offer-nofee-grants', None, '{event_name} Application Status Update', template, 'fr'))


def downgrade():
    op.execute("""DELETE FROM email_template WHERE key in ('offer-fee', 'offer-nofee', 'offer-fee-grants', 'offer-nofee-grants')""")
    op.execute("""SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template));""")
