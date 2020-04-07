from app import db
from app.applicationModel.models import ApplicationForm, Section, Question
from app.users.models import AppUser
from app.events.models import Event
from app.attendance.models import Attendance
from sqlalchemy.sql import exists
from app import LOGGER


class ApplicationFormRepository():

    @staticmethod
    def get_by_id(id):
        return db.session.query(ApplicationForm)\
            .filter_by(id=id)\
            .first()

    @staticmethod
    def get_by_event_id(event_id):
        return db.session.query(ApplicationForm)\
            .filter_by(event_id=event_id)\
            .first()

    @staticmethod
    def get_sections_by_app_id(app_id):
        return db.session.query(Section)\
            .filter_by(application_form_id=app_id)\
            .all()

    @staticmethod
    def get_section_by_app_id_and_section_name(app_id, section_name):
        # TODO: replace "name" with "key" to make this more robust (independent of "name" change)
        return db.session.query(Section)\
            .filter_by(application_form_id=app_id, name=section_name)\
            .first()

    @staticmethod
    def get_section_by_id(section_id):
        return db.session.query(Section).get(section_id)

    @staticmethod
    def get_question_by_id(question_id):
        return db.session.query(Question).get(question_id)
