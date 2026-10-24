"""Add form response deleted email template

Revision ID: c3f81a6e2d47
Revises: b7e4d2a91c35
Create Date: 2026-09-27 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'c3f81a6e2d47'
down_revision = 'b7e4d2a91c35'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""INSERT INTO email_template (key, subject, template, language)
    VALUES ('form-response-deleted', 'Your response to {form_name} has been deleted',
    'Dear {title} {firstname} {lastname},

This email is to let you know that your response to the form "{form_name}" for {event_name} has been deleted by the organisers.

If you believe this was a mistake, please get in touch with the organisers at {event_email}.

Kind regards,
The {event_name} Organisers', 'en')""")

    op.execute("""INSERT INTO email_template (key, subject, template, language)
    VALUES ('form-response-deleted', 'Votre réponse au formulaire {form_name} a été supprimée',
    'Cher/Chère {title} {firstname} {lastname},

Cet e-mail a pour but de vous informer que votre réponse au formulaire « {form_name} » pour {event_name} a été supprimée par les organisateurs.

Si vous pensez qu''il s''agit d''une erreur, veuillez contacter les organisateurs à l''adresse {event_email}.

Cordialement,
Les organisateurs de {event_name}', 'fr')""")


def downgrade():
    op.execute("DELETE FROM email_template WHERE key = 'form-response-deleted'")
