from app import db
from app.invitedGuest.models import InvitedGuest, GuestRegistration
from app.users.models import AppUser
from app.events.models import Event
from app.registration.models import RegistrationForm
from app.attendance.models import Attendance
from sqlalchemy.sql import exists
from app import LOGGER
from sqlalchemy import and_, func, cast, Date


class GuestRegistrationRepository():
    @staticmethod
    def get_all_unsigned_guests(event_id):
        """Get all guests who have not signed in"""
        stmt = ~ exists().where(Attendance.user_id == AppUser.id)
        return db.session.query(InvitedGuest, AppUser,GuestRegistration).join(
            AppUser, InvitedGuest.user_id == AppUser.id
        ).filter(
            InvitedGuest.event_id == event_id
        ).outerjoin(
            GuestRegistration, InvitedGuest.user_id == GuestRegistration.user_id
        ).filter(stmt).all()

    @staticmethod
    def get_all_guests(event_id):
        """Get all guests."""
        return db.session.query(InvitedGuest, AppUser,GuestRegistration).join(
            AppUser, InvitedGuest.user_id == AppUser.id
        ).filter(
            InvitedGuest.event_id == event_id
        ).outerjoin(
            GuestRegistration, InvitedGuest.user_id == GuestRegistration.user_id
        ).all()

    @staticmethod
    def get_confirmed_guest_for_event(event_id, confirmed):
        """Get confirmed guests."""
        return db.session.query(GuestRegistration, InvitedGuest, AppUser).filter(
            GuestRegistration.confirmed == confirmed
        ).join(
            InvitedGuest, InvitedGuest.user_id == GuestRegistration.user_id
        ).filter(
            InvitedGuest.event_id == event_id
        ).join(
            AppUser, InvitedGuest.user_id == AppUser.id
        ).all()

    @staticmethod
    def get_unsigned_in_comfirmed_guest_attendees(event_id, confirmed):
        """Get guests who have confirmed they will attend and have not already signed in."""
        stmt = ~ exists().where(Attendance.user_id == AppUser.user_id)
        return db.session.query(GuestRegistration, InvitedGuest, AppUser).filter(
            GuestRegistration.confirmed == confirmed
        ).join(
            InvitedGuest, InvitedGuest.user_id == GuestRegistration.user_id
        ).filter(
            InvitedGuest.event_id == event_id
        ).join(
            AppUser, InvitedGuest.user_id == AppUser.id
        ).filter(stmt).all()

    @staticmethod
    def count_guests(event_id):
        count = (db.session.query(InvitedGuest)
                        .filter_by(event_id=event_id)
                        .count())
        return count

    @staticmethod
    def count_registered_guests(event_id):
        count = (db.session.query(GuestRegistration)
                        .join(RegistrationForm, GuestRegistration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .count())
        return count
    
    @staticmethod
    def timeseries_guest_registrations(event_id):
        timeseries = (db.session.query(cast(GuestRegistration.created_at, Date), func.count(GuestRegistration.created_at))
                        .join(RegistrationForm, GuestRegistration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .group_by(cast(GuestRegistration.created_at, Date))
                        .order_by(cast(GuestRegistration.created_at, Date))
                        .all())
        return timeseries
