from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal
from app.attendance.mixins import AttendanceMixin
from app.attendance.models import Attendance
from app.tags.models import TagType
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.attendance.repository import IndemnityRepository as indemnity_repository
from app.events.repository import EventRepository as event_repository
from app.offer.repository import OfferRepository as offer_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.emailer import email_user
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, ATTENDANCE_NOT_FOUND, EVENT_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, INDEMNITY_NOT_FOUND, INDEMNITY_NOT_SIGNED, NOT_A_GUEST

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
    def __init__(self, user, attendance, is_invitedguest, invitedguest_role, confirmed, tags):
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
        print("Tags:", tags)

        for tag in tags:
            print(tag.tag.stringify_tag_name(), tag.tag.tag_type)

        self.tags = [tag.tag.stringify_tag_name() for tag in tags
        if tag.tag.tag_type == TagType.CHECKIN]
        print("self.tags:", self.tags)


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
        
        attendance_user = AttendanceUser(user, attendance, is_invitedguest=is_invited_guest, 
                                         invitedguest_role=invitedguest_role,
                                         confirmed=confirmed, tags=tags)
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

        all_attendees = attendance_repository.get_all_guests_for_event(event_id)

        guest_list_with_status = [{
            'id': u.AppUser.id,
            'email': u.AppUser.email,
            'firstname': u.AppUser.firstname,
            'lastname': u.AppUser.lastname,
            'user_title': u.AppUser.user_title,
            'checked_in': u.Attendance is not None and u.Attendance.confirmed
        } for u in all_attendees]

        return guest_list_with_status


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
