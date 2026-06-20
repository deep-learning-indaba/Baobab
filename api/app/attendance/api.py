from datetime import datetime
from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal
from app.attendance.mixins import AttendanceMixin
from app.attendance.models import Attendance
from app.tags.models import TagType
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.attendance.repository import IndemnityRepository as indemnity_repository
from app.attendance.repository import QRTokenRepository as qr_token_repository
from app.attendance.repository import CheckinRepository as checkin_repository
from app.events.repository import EventRepository as event_repository
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.offer.repository import OfferRepository as offer_repository
from app.users.repository import UserRepository as user_repository
from app.registration.repository import RegistrationRepository as registration_repository
from app.utils.auth import auth_required
from app.utils.emailer import email_user
from app.utils.misc import get_baobab_host
from app.utils.datetime_utils import event_local_date
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, ATTENDANCE_NOT_FOUND, EVENT_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, INDEMNITY_NOT_FOUND, INDEMNITY_NOT_SIGNED, NOT_A_GUEST, INVALID_QR, NOT_ON_GUEST_LIST, MISSING_FIELDS

attendance_fields = {
    'id': fields.Integer,
    'fullname': fields.String,
    'event_id': fields.Integer,
    'user_id': fields.Integer,
    'timestamp': fields.DateTime('iso8601'),
    'signed_indemnity_form': fields.Boolean,
    'updated_by_user_id': fields.Integer,
    'is_invitedguest': fields.Boolean,
    'message': fields.String,
    'invitedguest_role': fields.String,
    'confirmed': fields.Boolean,
    'registration_metadata': fields.List(fields.Nested({
        'name': fields.String,
        'response': fields.String
    })),
    'offer_metadata': fields.List(fields.Nested({
        'name': fields.String
    })),
    'tags': fields.List(fields.String)
}

_attendee_fields = {
        'id': fields.Integer,
        'email': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'user_title': fields.String
    }


class AttendanceUser():
    def __init__(self, user, attendance, is_invitedguest, invitedguest_role, confirmed, tags, registration=None):
        self.id = attendance.id if attendance is not None else None
        self.fullname = user.full_name  
        self.event_id = attendance.event_id if attendance is not None else None
        self.user_id = user.id
        self.timestamp = attendance.timestamp if attendance is not None else None
        self.signed_indemnity_form = attendance.indemnity_signed if attendance is not None else None
        self.updated_by_user_id = attendance.updated_by_user_id if attendance is not None else None
        self.is_invitedguest = is_invitedguest
        self.invitedguest_role = invitedguest_role
        self.confirmed = confirmed
        self.tags = [tag.tag.stringify_tag_name() for tag in tags
            if tag.tag.tag_type == TagType.CHECKIN]
        self.offer_metadata = [
            {'name': tag.tag.get_translation('en').name}
            for tag in tags
            if tag.tag.tag_type != TagType.CHECKIN
        ]
        if registration:
            self.registration_metadata = [
                {'name': qt.tag.get_translation('en').name, 'response': answer.value}
                for answer in registration.answers
                for qt in answer.registration_question.tags
            ]
        else:
            self.registration_metadata = []


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
        
        # Check if invited guest
        invited_guest = attendance_repository.get_invited_guest(event_id, user_id)
        registration = None
        
        if (invited_guest):
            is_invited_guest = True
            invitedguest_role = invited_guest.role
            confirmed = True
            tags = invited_guest.invited_guest_tags
        else:
            offer = attendance_repository.get_offer(event_id, user_id)
            confirmed = offer.is_confirmed
            invitedguest_role = "General Attendee"
            is_invited_guest = False
            tags = offer.offer_tags
            registration = registration_repository.from_offer(offer.id)
        
        attendance_user = AttendanceUser(user, attendance, is_invitedguest=is_invited_guest, 
                                         invitedguest_role=invitedguest_role,
                                         confirmed=confirmed, tags=tags, registration=registration)
        return marshal(attendance_user, attendance_fields), 200

    @auth_required
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
        if attendance and attendance.confirmed:
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

        # Undo the check-in: remove the canonical Checkin record(s) and the
        # Attendance record so both stores stay consistent.
        checkin_repository.delete_for_event_user(event_id, user_id)
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
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        registration_user_id = g.current_user["id"]
        
        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        all_attendees = attendance_repository.get_all_guests_for_event(event_id)

        if event.is_daily_checkin:
            day = event_local_date(datetime.utcnow(), event.timezone)
        else:
            day = None
        checked_in_ids = checkin_repository.checked_in_user_ids(event_id, day)

        guest_list_with_status = [{
            'id': u.AppUser.id,
            'email': u.AppUser.email,
            'firstname': u.AppUser.firstname,
            'lastname': u.AppUser.lastname,
            'user_title': u.AppUser.user_title,
            'checked_in': u.AppUser.id in checked_in_ids
        } for u in all_attendees]

        return guest_list_with_status


class ConfirmedGuestAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']
        is_guest = attendance_repository.is_confirmed_guest(event_id, user_id)
        return {'is_confirmed_guest': is_guest}


class AttendeesApi(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        registration_user_id = g.current_user["id"]
        
        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        confirmed = attendance_repository.get_confirmed_attendee_users(event_id)

        return marshal(confirmed, _attendee_fields)


class MyTicketAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        if not attendance_repository.is_confirmed_guest(event_id, current_user_id):
            return NOT_A_GUEST

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        user = user_repository.get_by_id(current_user_id)
        token = qr_token_repository.get_or_create(event_id, current_user_id)
        host = get_baobab_host()
        qr_url = '{}/{}/connect?t={}'.format(host, event.key, token.token)

        invited_guest = attendance_repository.get_invited_guest(event_id, current_user_id)
        role = invited_guest.role if invited_guest else 'General Attendee'

        latest_checkin = checkin_repository.get_latest(event_id, current_user_id)

        return {
            'token': token.token,
            'qr_url': qr_url,
            'fullname': user.full_name,
            'role': role,
            'event_name': event.get_name('en'),
            'checked_in': latest_checkin is not None,
            'checked_in_at': latest_checkin.checked_in_at.isoformat() + 'Z' if latest_checkin else None,
        }, 200


class CheckinResolveAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('t', type=str, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        token_str = args['t']
        volunteer_id = g.current_user['id']

        volunteer = user_repository.get_by_id(volunteer_id)
        if not volunteer.is_registration_volunteer(event_id):
            return FORBIDDEN

        qr = qr_token_repository.resolve(token_str)
        if qr is None or qr.event_id != event_id:
            return INVALID_QR

        if not attendance_repository.is_confirmed_guest(event_id, qr.user_id):
            return NOT_ON_GUEST_LIST

        user = user_repository.get_by_id(qr.user_id)
        invited_guest = attendance_repository.get_invited_guest(event_id, qr.user_id)
        role = invited_guest.role if invited_guest else 'General Attendee'
        attendance = attendance_repository.get(event_id, qr.user_id)
        indemnity_signed = attendance.indemnity_signed if attendance else False

        event = event_repository.get_by_id(event_id)
        if event.is_daily_checkin:
            day = event_local_date(datetime.utcnow(), event.timezone)
        else:
            day = None
        already_checked_in = checkin_repository.is_checked_in(event_id, qr.user_id, day)

        return {
            'user_id': qr.user_id,
            'token': token_str,
            'fullname': user.full_name,
            'role': role,
            'indemnity_signed': indemnity_signed,
            'already_checked_in': already_checked_in,
        }, 200


class CheckinAPI(restful.Resource):
    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('token', type=str, required=False)
        req_parser.add_argument('user_id', type=int, required=False)
        req_parser.add_argument('indemnity_signed', type=bool, required=False)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        current_user = user_repository.get_by_id(current_user_id)
        if not current_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        # Resolve the target user from either a scanned QR token or a manual
        # name/email selection (user_id fallback). Both paths funnel through
        # the same eligibility, idempotency and Checkin-creation logic.
        if args['token']:
            qr = qr_token_repository.resolve(args['token'])
            if qr is None or qr.event_id != event_id:
                return INVALID_QR
            target_user_id = qr.user_id
            method = 'scan'
        elif args['user_id']:
            target_user_id = args['user_id']
            method = 'manual'
        else:
            return MISSING_FIELDS

        by_user_id = current_user_id

        if not attendance_repository.is_confirmed_guest(event_id, target_user_id):
            return NOT_ON_GUEST_LIST

        if event.is_daily_checkin:
            day = event_local_date(datetime.utcnow(), event.timezone)
        else:
            day = None

        if checkin_repository.is_checked_in(event_id, target_user_id, day):
            user = user_repository.get_by_id(target_user_id)
            return {'already_checked_in': True, 'fullname': user.full_name}, 200

        checkin = checkin_repository.create(event_id, target_user_id, by_user_id, method, day)

        attendance = attendance_repository.get(event_id, target_user_id)
        if attendance is None:
            attendance = Attendance(event_id, target_user_id, current_user_id)
            attendance_repository.add(attendance)
        if args['indemnity_signed']:
            attendance.sign_indemnity()
        is_first_checkin = not attendance.confirmed
        if not attendance.confirmed:
            attendance.confirm()
        attendance_repository.save()

        user = user_repository.get_by_id(target_user_id)

        if is_first_checkin:
            email_user(
                'attendance-confirmation',
                event=event,
                user=user
            )

        return {
            'checked_in': True,
            'fullname': user.full_name,
            'checked_in_at': checkin.checked_in_at.isoformat() + 'Z',
        }, 201


class BadgeExportAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)
        if not current_user.is_registration_volunteer(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        guests = attendance_repository.get_all_guests_for_event(event_id)
        host = get_baobab_host()

        result = []
        for row in guests:
            user = row.AppUser
            token = qr_token_repository.get_or_create(event_id, user.id)
            qr_url = '{}/{}/connect?t={}'.format(host, event.key, token.token)
            invited_guest = attendance_repository.get_invited_guest(event_id, user.id)
            role = invited_guest.role if invited_guest else 'General Attendee'
            result.append({
                'user_id': user.id,
                'fullname': user.full_name,
                'role': role,
                'token': token.token,
                'qr_url': qr_url,
            })

        return result, 200
