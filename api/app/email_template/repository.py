from app import db

from app.email_template.models import EmailTemplate

class EmailRepository():

    @staticmethod
    def get(id, key):
        return db.session.query(EmailTemplate).filter_by(id=id, key=key).first()