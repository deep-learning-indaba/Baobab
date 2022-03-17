from app import db
from app.email_template.models import EmailTemplate


class EmailRepository:
    @staticmethod
    def get(event_id, key, language):
        email_template = (
            db.session.query(EmailTemplate)
            .filter_by(event_id=event_id, key=key, language=language)
            .first()
        )
        if email_template is None:
            email_template = (
                db.session.query(EmailTemplate)
                .filter_by(event_id=None, key=key, language=language)
                .first()
            )
            if email_template is None:
                email_template = (
                    db.session.query(EmailTemplate)
                    .filter_by(event_id=None, key=key, language="en")
                    .first()
                )
        return email_template
