# -*- coding: latin-1 -*-

"""Add French Email Templates

Revision ID: 62c7711123a8
Revises: ca538998737f
Create Date: 2020-08-27 15:37:45.224404

"""

# revision identifiers, used by Alembic.
revision = '62c7711123a8'
down_revision = 'ca538998737f'

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
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    template = u"""Madame / Monsieur {lastname},
    
Malheureusement, votre candidature à {event_name} a échoué.
Veuillez réessayer l'année prochaine!
    
Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('outcome-rejected', None, u'Mise à jour de l’état de la demande pour {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},
    
Ce courriel sert à vous informer que vous êtes maintenant sur la liste d'attente pour {event_name}.
Nous vous contacterons si une place se libère.
    
Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('outcome-waitlist', None, u'Mise à jour de l’état de la demande pour {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Bienvenue sur {event_name}! Nous sommes tellement excités que vous ayez réussi.

Si vous avez des questions ou des problèmes, veuillez discuter avec l'un des organisateurs.

Cordialement,
Les organisateurs de {event_name}
"""

    session.add(EmailTemplate('attendance-confirmation', None, u'Bienvenue à {event_name}!', template, 'fr'))

#########

    template = u"""Madame / Monsieur {lastname},

Merci d’avoir rempli le formulaire d’inscription pour les invités. Vous trouverez ci-dessous
une copie de vos réponses à des fins de consultation ultérieure.

{summary}

Cordialement, 
l’équipe {event_name}
"""

    session.add(EmailTemplate('guest-registration-confirmation', None, u'Inscription à {event_name}', template, 'fr'))

#########

    template = u"""Madame / Monsieur {lastname},

Veuillez trouver ci-joint votre lettre d'invitation officielle à {event_name}.

Cordialement, 
l’équipe {event_name}
"""

    session.add(EmailTemplate('invitation-letter', None, u"Lettre d'invitation à {event_name}", template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Nous sommes heureux de vous inviter à {event_name} en qualité de {role}.

Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('guest-invitation', None, u'Votre invitation à {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Nous sommes heureux de vous inviter à {event_name} en qualité de {role}.

Pour faciliter l’organisation de l’événement, veuillez remplir notre formulaire d’inscription
réservé aux invités dans {system_name}, en cliquant sur le lien suivant
{host}/{event_key}/registration

Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {event_name}"""
    session.add(EmailTemplate('guest-invitation-with-registration', None, u'Votre invitation à {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Nous sommes heureux de vous inviter à {event_name} en qualité de {role}.
Veuillez suivre les instructions ci-dessous pour accéder à notre système de gestion des
événements {system_name} :

1. Cliquez sur ce lien {host}/resetPassword?resetToken={reset_code} pour créer votre mot de passe.
2. Ouvrez une session en utilisant votre adresse électronique (celle sur laquelle vous avez
reçu ce courriel) et un nouveau mot de passe.
3. Mettez à jour vos coordonnées dans {host}/profile

Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('new-guest-no-registration', None, u'Votre invitation à {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Nous sommes heureux de vous inviter à {event_name} en qualité de {role}.
Veuillez suivre les instructions ci-dessous pour accéder à notre système de gestion des
événements {system_name} :

1. Cliquez sur ce lien {host}/resetPassword?resetToken={reset_code} pour créer votre mot de passe.
2. Ouvrez une session en utilisant votre adresse électronique (celle sur laquelle vous avez
reçu ce courriel) et un nouveau mot de passe.
3. Cliquez ici {host}/{event_key}/registration pour remplir le formulaire d’inscription.
4. Mettez à jour vos coordonnées dans {host}/profile

Veuillez répondre à ce courriel si vous avez des questions ou des préoccupations.

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('new-guest-registration', None, u'Votre invitation à {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

{candidate} a présenté sa candidature pour participer à {event_name}({event_url}).

Pour que sa demande puisse être retenue, nous avons besoin d’une lettre de recommandation d’une personne qui connaît {candidate_firstname} à titre professionnel et qui a soutenu sa candidature.

Veuillez utiliser le lien de téléchargement ci-dessous pour soumettre votre lettre de recommandation pour {candidate_firstname} d’ici le {application_close_date}.

La lettre de référence doit décrire vos rapports avec {candidate_firstname}, indiquer depuis combien de temps vous vous connaissez et préciser le travail accompli par {candidate_firstname} et ce que sa participation apporterait à {event_name}.
Sa demande ne sera PAS prise en compte si cette lettre de recommandation n’est pas soumise dans les délais impartis.

Veuillez cliquer sur ce lien {link} pour télécharger votre lettre de recommandation d’ici le {application_close_date}.

Cordialement,
L’équipe de {event_name}

"""
    session.add(EmailTemplate('reference-request-self-nomination', None, u'DEMANDE DE RÉFÉRENCE – {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

{candidate} a été désigné(e) pour participer à {event_name}({event_url}).

Pour que sa demande puisse être retenue, nous avons besoin d’une lettre de recommandation d’une personne qui connaît {candidate_firstname} à titre professionnel et qui a soutenu sa candidature.

Veuillez utiliser le lien de téléchargement ci-dessous pour soumettre votre lettre de recommandation pour {candidate_firstname} d’ici le {application_close_date}.

La lettre de référence doit décrire vos rapports avec {candidate_firstname}, indiquer depuis combien de temps vous vous connaissez et préciser le travail accompli par {candidate_firstname} et ce que sa participation apporterait à {event_name}.
Sa demande ne sera PAS prise en compte si cette lettre de recommandation n’est pas soumise dans les délais impartis.

Veuillez cliquer sur ce lien {link} pour télécharger votre lettre de recommandation d’ici le {application_close_date}.

Cordialement,
L’équipe de {event_name}
"""
    session.add(EmailTemplate('reference-request', None, u'DEMANDE DE RÉFÉRENCE – {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Félicitations ! Votre candidature a été retenue pour {event_name} !

Veuillez consulter le lien ci-dessous pour en savoir plus et accepter votre offre : {host}/offer Vous avez jusqu’au {expiry_date} pour accepter l’offre. Dans le cas contraire, nous attribuerons automatiquement votre place à quelqu’un d’autre.

Si vous ne pouvez pas accepter l’offre pour quelque raison que ce soit, veuillez nous en informer en visitant la page {host}/offer. Cliquez sur le bouton de refus et précisez la raison de ce refus.
Tous vos commentaires seront lus. Nous ferons de notre mieux pour vous aider. Il est possible que nous vous fassions une nouvelle offre par la suite.

Si vous avez des questions, veuillez communiquer avec nous à l’adresse {event_email_from}.

Cordialement,
Les organisateurs de {event_name}

"""
    session.add(EmailTemplate('offer', None, u'Mise à jour de l’état de la demande pour {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Merci d’avoir rempli le formulaire d’inscription. 
Veuillez noter que votre place est en attente de confirmation à la réception du paiement. Vous recevrez une correspondance avec les instructions de paiement dans les prochains jours.

Voici une copie de vos réponses :

{summary}

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('registration-pending-confirmation', None, u'Inscription à {event_name}', template, 'fr'))
    
#########



    template = u"""Madame / Monsieur {lastname},

Merci d’avoir rempli le formulaire d’inscription. 
Votre place est maintenant confirmée et nous nous réjouissons de vous accueillir à l'événement!

Voici une copie de vos réponses :

{summary}

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('registration-with-confirmation', None, u'Inscription à {event_name}', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},
    
Votre inscription à {event_name} a été confirmée! Cela signifie que tous les paiements requis ont été effectués.

Nous attendons avec impatience de vous voir à l'événement!

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('registration-confirmed', None, u"La confirmation d'inscription à {event_name}", template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

{num_reviews} tâches de révision vous ont été attribuées dans {system_name}. Veuillez consulter {baobab_host}/{event_key}/review pour commencer.

Veuillez noter que si vous avez déjà ouvert une session sur {system_name}, vous devrez vous déconnecter et vous reconnecter pour que les modifications apportées à votre profil soient prises en compte.

Merci de nous aider à passer en revue les demandes pour {event_name} !

Cordialement,
Les organisateurs de {event_name}
"""
    session.add(EmailTemplate('reviews-assigned', None, u'Des tâches de révision vous ont été attribuées dans {system_name}', template, 'fr'))
    
    # Update the English template
    en_template = session.query(EmailTemplate).filter_by(key='reviews-assigned', language='en').first()
    en_template.template = u"""Dear {title} {firstname} {lastname},

You have been assigned {num_reviews} reviews on {system_name}. Please visit {baobab_host}/{event_key}/review to begin.
Note that if you were already logged in to {system_name}, you will need to log out and log in again to pick up the changes to your profile. 

Thank you for assisting us review applications for {event_name}!

Kind Regards,
The {event_name} Organisers
    """

#########


    template = u"""Madame / Monsieur {lastname},

Merci d’avoir créé un nouveau compte {system}. Veuillez cliquer sur le lien suivant pour
vérifier votre adresse électronique :

{host}/verifyEmail?token={token}

Cordialement,
{organisation}
"""
    session.add(EmailTemplate('verify-email', None, u'Courriel {system} Vérification', template, 'fr'))
    
#########


    template = u"""Madame / Monsieur {lastname},

Vous avez récemment demandé une réinitialisation de votre mot de passe sur {system_name}.
Pour ce faire, veuillez cliquer sur le lien suivant : {host}/resetPassword?resetToken={token}

Si vous n’avez pas demandé la réinitialisation de votre mot de passe, veuillez ignorer ce courriel et communiquer avec {organisation}.

Cordialement,
{organisation}
"""
    session.add(EmailTemplate('password-reset', None, u'Réinitialisation du mot de passe pour {system_name}', template, 'fr'))

    session.commit()


def downgrade():
    added_keys = ['outcome-rejected', 'outcome-waitlist', 'attendance-confirmation', 'guest-registration-confirmation',
            'invitation-letter', 'guest-invitation', 'guest-invitation-with-registration', 'new-guest-no-registration',
            'new-guest-registration', 'reference-request-self-nomination', 'reference-request', 'offer',
            'registration-pending-confirmation', 'registration-with-confirmation', 'registration-confirmed', 
            'reviews-assigned', 'verify-email', 'password-reset']
    op.execute("""DELETE FROM email_template WHERE language='fr' and key in ({})""".format(', '.join(["'" + k + "'" for k in added_keys])))
