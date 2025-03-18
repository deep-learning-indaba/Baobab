"""add_template_email_journal_submission

Revision ID: 40ed07fdb75a
Revises: 0a7b0ee0693a
Create Date: 2025-03-06 00:05:43.764947

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from app import db

# revision identifiers, used by Alembic.
revision = '40ed07fdb75a'
down_revision = '0a7b0ee0693a'


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

Thank you for submitting to The Journal of Artificial Intelligence for Sustainable Development. Your article is being reviewed by our committee and we will get back to you as soon as possible. Included below is a copy of your responses.

{question_answer_summary}

Kind Regards,
The JAISD editorial board"""


    session.add(
        EmailTemplate(
            key="submitting-article-journal",
            event_id=None,
            subject="{submission_title} Submission",
            template=template,
            language="en"
        )
    )

    template = """Cher/Cher(e) {title} {firstname} {lastname},  

    Merci d'avoir soumis votre article à The Journal of Artificial Intelligence for Sustainable Development. Votre article est actuellement en cours d’examen par notre comité, et nous reviendrons vers vous dès que possible. Vous trouverez ci-dessous un récapitulatif de vos réponses.  

    {question_answer_summary}  

    Cordialement,  
    Le comité de redaction du JAISD
    """


    session.add(
        EmailTemplate(
            key="submitting-article-journal",
            event_id=None,
            subject="{submission_title} Submission",
            template=template,
            language="fr"
        )
    )
    session.commit()

def downgrade():
    op.execute("""DELETE FROM email_template WHERE key = 'submitting-article-journal'""")
