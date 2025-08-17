"""add_template email journal

Revision ID: 0a7b0ee0693a
Revises: 4b881c1c6dc2
Create Date: 2025-03-03 09:12:51.876903

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

depends_on = "4b881c1c6dc2"

# Revision identifiers, used by Alembic.
revision = "0a7b0ee0693a"
down_revision = "4b881c1c6dc2"

Base = declarative_base()

class EmailTemplate(Base):
    __tablename__ = "email_template"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer(), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    template = db.Column(db.String(), nullable=False)
    subject = db.Column(db.String(), nullable=False)

def upgrade():
    Base.metadata.bind = op.get_bind()
    session = orm.Session(bind=Base.metadata.bind)

    template = """Dear {title} {firstname} {lastname},

    Thank you for your submission of **{submission_title}** to {event_name}. 
    Please find below a meta review summary, followed by the reviewer(s)’s feedback.

    **Meta-review**

    {summary}

    **Decision**

    {outcome}

    **Review(s)**

    {reviewers_contents}

    Kind regards,
    The {event_name} editorial board"""

    session.add(
        EmailTemplate(
            key="response-journal",
            event_id=None,
            subject="{submission_title} Decision",
            template=template,
            language="en"
        )
    )

    template = """Cher/Cher(e) {title} {firstname} {lastname},

    Merci pour votre soumission de {submission_title} au {event_name}. 
    Vous trouverez ci-dessous un résumé de la méta-évaluation, suivi des commentaires des réviseurs.  

    **Méta-évaluation**  
    {summary}  

    **Décision**  
    {outcome}  

    **Commentaires des relecteurs**  
    {reviewers_contents}  

    Cordialement,  
    Le comité de redaction du {event_name}"""

    session.add(
        EmailTemplate(
            key="response-journal",
            event_id=None,
            subject="{submission_title} Decision",
            template=template,
            language="fr"
        )
    )
    session.commit()

def downgrade():
    op.execute("""DELETE FROM email_template WHERE key = 'response-journal'""")



