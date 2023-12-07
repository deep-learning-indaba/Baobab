from app import db
from app.invitedGuest.models import InvitedGuest, GuestRegistration, GuestRegistrationAnswer
from app.users.models import AppUser
from app.events.models import Event
from app.applicationModel.models import ApplicationForm, Question, Section, QuestionTranslation, SectionTranslation
from app.responses.models import Response, Answer
from app.attendance.models import Attendance
from sqlalchemy.sql import exists
from app import LOGGER
from sqlalchemy import and_, func, cast, Date

class ReportingRepository():

    @staticmethod
    def get_applications_for_form(application_form_id: int, language: str):
        """Get all applications for an event."""
        responses = (
            db.session.query(Answer, Response, Question, QuestionTranslation, Section, SectionTranslation, AppUser)
            .filter_by(is_active=True)
            .join(Response, Answer.response_id == Response.id)
            .filter_by(application_form_id=application_form_id, is_submitted=True)
            .join(Question, Answer.question_id == Question.id)
            .join(QuestionTranslation, Question.id == QuestionTranslation.question_id)
            .filter_by(language=language)
            .join(Section, Question.section_id == Section.id)
            .join(SectionTranslation, Section.id == SectionTranslation.section_id)
            .filter_by(language=language)
            .join(AppUser, Response.user_id == AppUser.id)
            .all())

        return responses