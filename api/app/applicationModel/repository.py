from app import db
from app.applicationModel.models import ApplicationForm, Question, Section
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

    @staticmethod
    def get_questions_for_event(event_id):
        return (db.session.query(Question)
                    .join(ApplicationForm, Question.application_form_id == ApplicationForm.id)
                    .filter_by(event_id=event_id)
                    .join(Section, Question.section_id == Section.id)
                    .order_by(Section.order, Question.order)
                    .all())
