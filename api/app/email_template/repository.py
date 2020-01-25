from app import db

from app.email_template.models import EmailTemplate

class EmailRepository():

    @staticmethod
    def get(event_id, key):
        return db.session.query(EmailTemplate).filter_by(event_id=event_id, key=key).first()