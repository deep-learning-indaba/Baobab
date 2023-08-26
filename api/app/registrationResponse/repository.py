from app import db
from app.registration.models import Offer, Registration
from app.tags.models import Tag
from app.users.models import AppUser
from app.attendance.models import Attendance
from sqlalchemy.sql import exists

class RegistrationRepository():

    @staticmethod
    def get_by_id_with_offer(registration_id):
        """Get a registration by its id."""
        return db.session.query(Registration, Offer).filter(
            Registration.id == registration_id).join(
                Offer, Offer.id == Registration.offer_id
        ).one_or_none()

    @staticmethod
    def get_by_user_id(user_id, event_id):
        """Get the registration for a given user id."""
        return db.session.query(Registration).join(
            Offer, Registration.offer_id == Offer.id
        ).filter(
            Offer.user_id == user_id,
            Offer.event_id == event_id
        ).first()

    @staticmethod
    def get_all_for_event(event_id):
        """Get all registrations for an event"""
        return db.session.query(Registration, Offer, AppUser).join(
            Offer, Registration.offer_id == Offer.id
        ).join(
            AppUser, Offer.user_id == AppUser.id
        ).filter(
            Offer.event_id == event_id
        ).all()

    @staticmethod
    def get_confirmed_for_event(event_id, confirmed):
        """Get registrations for an event according to confirmed status."""
        return (db.session.query(Registration, Offer, AppUser)
                .filter(Registration.confirmed == confirmed)
                .join(Offer, Registration.offer_id == Offer.id)
                .join(AppUser, Offer.user_id == AppUser.id)
                .filter(Offer.event_id == event_id, Offer.candidate_response == True)
                .all())

    @staticmethod
    def get_unsigned_in_attendees(event_id, confirmed):
        """Get attendees who have confirmed they will attend and have not already signed in."""
        stmt = ~ exists().where(Attendance.user_id == AppUser.id)

        registration_stmt = db.session.query(Registration, Offer, AppUser).join(
            Offer, Registration.offer_id == Offer.id
        ).join(
            AppUser, Offer.user_id == AppUser.id
        ).filter(
            Offer.event_id == event_id
        ).filter(stmt)

        
        if confirmed is not None: 
            registration_stmt = registration_stmt.filter(
                Registration.confirmed == confirmed)

        reg = registration_stmt.all()
        return reg
