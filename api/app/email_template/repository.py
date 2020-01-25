from app import db

from app.email_template.models import EmailTemplate

class EmailRepository():

    @staticmethod
    def get(event_id, key):
        email_template = db.session.query(EmailTemplate).filter_by(event_id=event_id, key=key).first()
        if email_template is None:
            email_template = db.session.query(EmailTemplate).filter_by(event_id=None, key=key).first()
        return email_template