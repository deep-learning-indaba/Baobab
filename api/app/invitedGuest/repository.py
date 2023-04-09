from app import db
from app.invitedGuest.models import InvitedGuest, GuestRegistration, InvitedGuestTag
from app.registration.models import RegistrationForm

class InvitedGuestRepository():

    @staticmethod
    def get_by_id(invited_guest_id):
        return (db.session.query(InvitedGuest)
                .filter_by(id=invited_guest_id)
                .first())
    
    @staticmethod
    def get_for_event_and_user(event_id, user_id):
        return (db.session.query(InvitedGuest)
                .filter(InvitedGuest.event_id == event_id, InvitedGuest.user_id == user_id)
                .first())

    @staticmethod
    def get_registration_for_event_and_user(event_id, user_id):
        return (db.session.query(GuestRegistration)
                .filter(GuestRegistration.user_id == user_id)
                .join(RegistrationForm, GuestRegistration.registration_form_id == RegistrationForm.id)
                .filter(RegistrationForm.event_id == event_id)
                .first())

    @staticmethod
    def tag_invited_guest(invited_guest_id, tag_id):
        invited_guest_tag = InvitedGuestTag(invited_guest_id, tag_id)
        db.session.add(invited_guest_tag)
        db.session.commit()
        return invited_guest_tag

    @staticmethod
    def remove_tag_from_invited_guest(invited_guest_id, tag_id):
        (db.session.query(InvitedGuestTag)
         .filter_by(invited_guest_id=invited_guest_id, tag_id=tag_id)
         .delete())
        db.session.commit()