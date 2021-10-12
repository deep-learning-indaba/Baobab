from app import db
from app.invitedGuest.models import GuestRegistration, InvitedGuest
from app.registration.models import RegistrationForm


class InvitedGuestRepository:
    @staticmethod
    def get_for_event_and_user(event_id, user_id):
        return (
            db.session.query(InvitedGuest)
            .filter(InvitedGuest.event_id == event_id, InvitedGuest.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_registration_for_event_and_user(event_id, user_id):
        return (
            db.session.query(GuestRegistration)
            .filter(GuestRegistration.user_id == user_id)
            .join(
                RegistrationForm,
                GuestRegistration.registration_form_id == RegistrationForm.id,
            )
            .filter(RegistrationForm.event_id == event_id)
            .first()
        )
