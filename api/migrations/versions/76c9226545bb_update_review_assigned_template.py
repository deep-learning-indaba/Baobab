# -*- coding: utf-8 -*-
"""Update reviews assigned email template

Revision ID: 76c9226545bb
Revises: 303140b3cefb
Create Date: 2020-12-09 11:15:20.840913

"""

# revision identifiers, used by Alembic.
revision = '76c9226545bb'
down_revision = '303140b3cefb'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from app import db
import datetime

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
    en = db.session.query(EmailTemplate).filter_by(language='en', key='reviews-assigned').first()
    en.template = """Dear {title} {firstname} {lastname},

You have been assigned {num_reviews} reviews on {system_name}. Please visit {baobab_host}/{event_key}/reviewlist to begin.

Thank you for assisting us review applications for {event_name}!

Kind Regards,
The {event_name} Organisers"""

    fr = db.session.query(EmailTemplate).filter_by(language='fr', key='reviews-assigned').first()
    fr.template = """Madame / Monsieur {lastname},

{num_reviews} tâches de révision vous ont été attribuées dans {system_name}. Veuillez consulter {baobab_host}/{event_key}/reviewlist pour commencer.

Merci de nous aider à passer en revue les demandes pour {event_name} !

Cordialement,
Les organisateurs de {event_name}
"""

    db.session.commit()


def downgrade():
    en = db.session.query(EmailTemplate).filter_by(language='en', key='reviews-assigned')
    en.template = """Dear {title} {firstname} {lastname},

You have been assigned {num_reviews} reviews on {system_name}. Please visit {baobab_host}/{event_key}/review to begin.
Note that if you were already logged in to {system_name}, you will need to log out and log in again to pick up the changes to your profile. 

Thank you for assisting us review applications for {event_name}!

Kind Regards,
The {event_name} Organisers"""

    fr = db.session.query(EmailTemplate).filter_by(language='fr', key='reviews-assigned')
    fr.template = """Madame / Monsieur {lastname},

{num_reviews} tâches de révision vous ont été attribuées dans {system_name}. Veuillez consulter {baobab_host}/{event_key}/review pour commencer.

Veuillez noter que si vous avez déjà ouvert une session sur {system_name}, vous devrez vous déconnecter et vous reconnecter pour que les modifications apportées à votre profil soient prises en compte.

Merci de nous aider à passer en revue les demandes pour {event_name} !

Cordialement,
Les organisateurs de {event_name}"""

    db.session.commit()
