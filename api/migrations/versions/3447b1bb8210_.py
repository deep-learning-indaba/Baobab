"""empty message

Revision ID: 3447b1bb8210
Revises: d2c160b0cbe5
Create Date: 2024-09-21 11:30:45.546768

"""

# revision identifiers, used by Alembic.
revision = '3447b1bb8210'
down_revision = 'd2c160b0cbe5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    
    op.execute("""INSERT INTO email_template (id, key, template, language, subject)
VALUES (71, 'outcome-desk-rejected', 'Dear {title} {firstname} {lastname},

Thank you very much for submitting the application, with submission number {response_id}, to the {event_name}.

We regret to inform you that your submission is desk rejected, with the following motivation by the editors:

{reason}

Best wishes,
The {event_name} Editors', 'en', '{event_name} Application Status Update')""")
    
    op.execute("""INSERT INTO email_template (id, key, template, language, subject)
VALUES (72, 'outcome-journal-desk-rejected', 'Dear {title} {firstname} {lastname},

Thank you very much for submitting your paper with submission number {response_id} to the {event_name}.

We regret to inform you that your submission is desk rejected, with the following motivation by the editors:

{reason}

Best wishes,
The {event_name} Editors', 'en', '{event_name} Application Status Update')""")
    
    op.execute("""INSERT INTO email_template (id, key, template, language, subject)
VALUES (73, 'outcome-journal-rejected', 'Dear {title} {firstname} {lastname},

Thank you very much for submitting your paper with submission number {response_id} to the {event_name}.

We regret to inform you that your submission is rejected, with the following motivation by the editors:

{reason}

Best wishes,
The {event_name} Editors', 'en', '{event_name} Application Status Update')""")

def downgrade():
    # Remove the added email template rows
    op.execute("DELETE FROM email_template WHERE key IN ('outcome-journal-rejected', 'outcome-journal-desk-rejected', 'outcome-desk-rejected')")
