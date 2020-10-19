from app import db
from app.applicationModel.models import ApplicationForm
from app.events.models import Event


class ApplicationFormRepository():

    @staticmethod
    def get_by_id(id):
        return db.session.query(ApplicationForm).get(id)

    @staticmethod
    def get_by_event_id(event_id):
        return db.session.query(ApplicationForm)\
            .filter_by(event_id=event_id)\
            .first()

    def add_form(application_form):
        db.session.add(application_form)
        db.session.commit()
        return application_form