from app import db
from app.registration.models import Registration, RegistrationForm, RegistrationQuestion
from app.tags.models import Tag
from sqlalchemy import func, cast, Date


class RegistrationRepository():
    @staticmethod
    def from_offer(offer_id):
        return (db.session.query(Registration)
                .filter_by(offer_id=offer_id)
                .first())

    @staticmethod
    def count_registrations(event_id):
        count = (db.session.query(Registration)
                        .join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .count())
        return count

    @staticmethod
    def timeseries_registrations(event_id):
        timeseries = (db.session.query(cast(Registration.created_at, Date), func.count(Registration.created_at))
                        .join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .group_by(cast(Registration.created_at, Date))
                        .order_by(cast(Registration.created_at, Date))
                        .all())
        return timeseries

    @staticmethod
    def get_form_for_event(event_id):
        return (db.session.query(RegistrationForm).filter_by(event_id=event_id)).first()

class RegistrationFormRepository():
    @staticmethod
    def get_by_event_id(event_id):
        return (db.session.query(RegistrationForm)
                .filter_by(event_id=event_id)
                .first())
    
    @staticmethod
    def get_by_id(id):
        return db.session.query(RegistrationForm).get(id)

    @staticmethod
    def get_registration_questions_with_tags(event_id):
        """Get all questions with active tags in a registration form."""
        return db.session.query(RegistrationQuestion).join(
                RegistrationForm, RegistrationQuestion.registration_form_id == RegistrationForm.id).filter(
                    RegistrationForm.event_id == event_id).filter(
                    RegistrationQuestion.tags != None).join(
                    Tag, RegistrationQuestion.tags.any(Tag.active == True)
            ).all()
    
    