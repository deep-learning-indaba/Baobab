from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with, marshal
from app import db, LOGGER
from app.attendance.mixins import AttendanceMixin
from app.attendance.models import Attendance
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.attendance.repository import IndemnityRepository as indemnity_repository
from app.registration.repository import OfferRepository as offer_repository
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.registrationResponse.repository import RegistrationRepository as registration_response_repository
from app.guestRegistrations.repository import GuestRegistrationRepository as guest_registration_repository
from app.events.repository import EventRepository as event_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.emailer import email_user
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, ATTENDANCE_NOT_FOUND, EVENT_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, INDEMNITY_NOT_FOUND, INDEMNITY_NOT_SIGNED, NOT_A_GUEST
from app.registration.models import Offer
from app.registration.models import get_registration_answer_based_headline
from app.invitedGuest.models import InvitedGuest

attendance_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'user_id': fields.Integer,
    'timestamp': fields.DateTime('iso8601'),
    'signed_indemnity_form': fields.Boolean,
    'updated_by_user_id': fields.Integer,
    'accommodation_award': fields.Boolean,
    'shirt_size': fields.String,
    'is_invitedguest': fields.Boolean,
    'bringing_poster': fields.Boolean,
    'message': fields.String,
    'invitedguest_role': fields.String,
    'confirmed': fields.Boolean
}


class AttendanceUser():
    def __init__(self, attendance, accommodation_award, shirt_size, is_invitedguest, bringing_poster, invitedguest_role, confirmed):
        self.id = attendance.id if attendance is not None else None
        self.event_id = attendance.event_id if attendance is not None else None
        self.user_id = attendance.user_id if attendance is not None else None
        self.timestamp = attendance.timestamp if attendance is not None else None
        self.signed_indemnity_form = attendance.indemnity_signed if attendance is not None else None
        self.updated_by_user_id = attendance.updated_by_user_id if attendance is not None else None
        self.accommodation_award = accommodation_award
        self.shirt_size = shirt_size
        self.is_invitedguest = is_invitedguest
        self.bringing_poster = bringing_poster
        self.invitedguest_role = invitedguest_role
        self.confirmed = confirmed


def _get_registration_answer(user_id, event_id, headline, is_invited_guest):
    if is_invited_guest:
        answer = guest_registration_repository.get_guest_registration_answer_by_headline(user_id, event_id, headline)
    else:
        answer = get_registration_answer_based_headline(user_id, event_id, headline)
    
    if answer is None:
        return None
    else:
        return answer.value


class AttendanceAPI(AttendanceMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        user = user_repository.get_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND

        attendance = attendance_repository.get(event_id, user_id)

        invitedguest_role = None
        is_invited_guest = False
        has_accepted_accom_award = False

        offer = db.session.query(Offer).filter(
            Offer.user_id == user_id).filter(Offer.event_id == event_id).first()
        if offer:
            has_accepted_accom_award = (
                offer.accommodation_award and offer.accepted_accommodation_award)
        
        # Check if invited guest
        invited_guest = db.session.query(InvitedGuest).filter(
                    InvitedGuest.event_id == event_id).filter(InvitedGuest.user_id == user.id).first()
        if(invited_guest):
            is_invited_guest = True
            invitedguest_role = invited_guest.role
            confirmed = True
        else:
            registration = registration_response_repository.get_by_user_id(user.id, event_id)
            confirmed = registration.confirmed if registration is not None else True
        # Shirt Size
        shirt_answer = _get_registration_answer(user_id, event_id, "T-Shirt Size", is_invited_guest)

        # Poster registration
        bringing_poster = _get_registration_answer(user_id, event_id, "Will you be bringing a poster?", is_invited_guest) == 'yes'

        attendance_user = AttendanceUser(attendance, accommodation_award=has_accepted_accom_award, 
                                         shirt_size=shirt_answer, is_invitedguest=is_invited_guest, 
                                         bringing_poster=bringing_poster, invitedguest_role=invitedguest_role,
                                         confirmed=confirmed)
        return marshal(attendance_user, attendance_fields), 200

    @auth_required
    @marshal_with(attendance_fields)
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('user_id', type=int, required=True)
        req_parser.add_argument('indemnity_signed', type=bool, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        indemnity_signed = args['indemnity_signed']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        user = user_repository.get_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND

        if not indemnity_signed:
            return INDEMNITY_NOT_SIGNED

        attendance = attendance_repository.get(event_id, user_id)
        if attendance and attendance.is_confirmed:
            return ATTENDANCE_ALREADY_CONFIRMED
        
        if not attendance:
            attendance = Attendance(event_id, user_id, registration_user_id)
            attendance_repository.add(attendance)
        attendance.sign_indemnity()
        attendance.confirm()
        attendance_repository.save()

        email_user(
            'attendance-confirmation',
            event=event,
            user=user
        )

        return None, 201

    @auth_required
    def delete(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        user = user_repository.get_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND

        attendance = attendance_repository.get(event_id, user_id)
        if attendance is None:
            return ATTENDANCE_NOT_FOUND

        attendance_repository.delete(attendance)

        return 200


class IndemnityAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        indemnity = indemnity_repository.get(event_id)
        if not indemnity:
            return INDEMNITY_NOT_FOUND

        invited_guest = invited_guest_repository.get_for_event_and_user(event_id, user_id)
        if invited_guest is None:
            offer = offer_repository.get_by_user_id_for_event(user_id, event_id)
            if offer is None or not offer.candidate_response:
                return NOT_A_GUEST

        attendance = attendance_repository.get(event_id, user_id)
        event = event_repository.get_by_id(event_id)
        user = user_repository.get_by_id(user_id)

        return {
            'indemnity_form': indemnity.indemnity_form.format(attendee_name=user.full_name),
            'signed': attendance.indemnity_signed if attendance is not None else False,
            'event_name': event.get_name("en"),
            'date': attendance.timestamp.isoformat() if attendance is not None else None,
        }, 200

    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        LOGGER.info(f"Received indemnity signature for event {event_id}, user {current_user_id}")

        indemnity = indemnity_repository.get(event_id)
        if not indemnity:
            LOGGER.error(f"Indemnity form not found")
            return INDEMNITY_NOT_FOUND

        event = event_repository.get_by_id(event_id)
        user = user_repository.get_by_id(current_user_id)
        attendance = Attendance(event_id, current_user_id, current_user_id)
        attendance.sign_indemnity()
        LOGGER.info(f"Created attendance and signed")
        
        attendance_repository.add(attendance)
        attendance_repository.save()
        LOGGER.info(f"Saved")

        email_user(
            'indemnity-signed',
            event=event,
            user=user,
            template_parameters={
                "indemnity_form": indemnity.indemnity_form.format(attendee_name=user.full_name)
            })  
        LOGGER.info(f"Emailed")

        return {
            'indemnity_form': indemnity.indemnity_form.format(attendee_name=user.full_name),
            'signed': attendance.indemnity_signed if attendance is not None else False,
            'event_name': event.get_name("en"),
            'date': attendance.timestamp.isoformat() if attendance is not None else None,
        }, 201


class GuestListApi(restful.Resource):
    _attendee_fields = {
        'id': fields.Integer,
        'email': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'user_title': fields.String
    }

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('exclude_already_checked_in', type=bool, required=True)
        args = req_parser.parse_args()
        exclude_already_checked_in = args['exclude_already_checked_in']
        event_id = args['event_id']
        registration_user_id = g.current_user["id"]
        
        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        all_attendees = attendance_repository.get_all_guests_for_event(event_id)

        if exclude_already_checked_in:
            checked_in = attendance_repository.get_confirmed_attendees(event_id)
            checked_in = [u.user_id for u in checked_in]
            # TODO(avishkar): Check that this scales (n^2) appropriately.
            all_attendees = [u for u in all_attendees if u.id not in checked_in]

        return marshal(all_attendees, self._attendee_fields)
