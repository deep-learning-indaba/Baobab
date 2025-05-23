"""Add remove guest email template

Revision ID: 49663ad38428
Revises: e8eafcfe7800
Create Date: 2025-03-15 09:53:50.120937

"""

# revision identifiers, used by Alembic.
revision = '49663ad38428'
down_revision = 'e8eafcfe7800'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""INSERT INTO email_template (key, subject, template, language) 
    VALUES ('guest-removal', 'Guest Removal', 
    'Dear {title} {firstname} {lastname},
    
This email serves to inform you that you have been removed from the guest list for {event_name}.

If you believe this was done in error, please get in touch with the organisers at {event_email}.

Kind regards,
The {event_name} Organisers', 'en')""")

    op.execute("""INSERT INTO email_template (key, subject, template, language) 
    VALUES ('guest-removal', 'Guest Removal', 
    'Cher/Chèr(e) {title} {firstname} {lastname}, 

Cet e-mail a pour but de vous informer que vous avez été retiré(e) de la liste des invités pour {event_name}. 

Si vous pensez qu''il s''agit d''une erreur, veuillez contacter les organisateurs à l''adresse {event_email}. 

Cordialement, 
Les organisateurs de {event_name}', 'fr')""")

def downgrade():
    op.execute("DELETE FROM email_template WHERE key = 'guest-removal'")

