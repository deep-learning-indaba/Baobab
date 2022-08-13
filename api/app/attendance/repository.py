from api.app.invitedGuest.models import InvitedGuest
from app import db
from app.attendance.models import Attendance, EventIndemnity
from app.users.models import AppUser
from app.registration.models import Offer

class AttendanceRepository():

    @staticmethod
    def get(event_id, user_id):
        return db.session.query(Attendance)\
                         .filter_by(event_id=event_id, user_id=user_id)\
                         .first()

    @staticmethod
    def add(attendance):
        db.session.add(attendance)
    
    @staticmethod
    def save():
        db.session.commit()

    @staticmethod
    def delete(attendance):
        db.session.delete(attendance)
        db.session.commit()

    @staticmethod
    def get_all_guests_for_event(event_id):
        offers = (db.session.query(AppUser)
                    .join(Offer, Offer.user_id == AppUser.id)
                    .filter_by(event_id=event_id, candidate_response=True))
        invited = (db.session.query(AppUser)
                    .join(InvitedGuest, InvitedGuest.user_id == AppUser.id)
                    .filter_by(event_id=event_id))
        return offers.union(invited).all()

    @staticmethod
    def get_confirmed_attendees(event_id):
        return (db.session.query(Attendance)
                    .filter_by(event_id=event_id, confirmed=True))


class IndemnityRepository():
    @staticmethod
    def get(event_id):
        return (db.session.query(EventIndemnity)
                .filter_by(event_id=event_id)
                .first())