from app import db

from app.email_template.models import EmailTemplate

class EmailRepository():

    @staticmethod
    def get_by_id(email_id):
        return db.session.query(EmailTemplate).get(email_id)

    @staticmethod
    def get_by_key(key):
        return db.session.query(EmailTemplate).filter_by(key=key).first()