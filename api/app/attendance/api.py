from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with

from app.attendance.emails import ATTENDANCE_EMAIL_BODY
from app.attendance.mixins import AttendanceMixin
from app.attendance.models import Attendance
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.events.repository import EventRepository as event_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.emailer import send_mail
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, ATTENDANCE_NOT_FOUND, EVENT_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND

attendance_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'user_id': fields.Integer,
    'timestamp': fields.DateTime('iso8601'),
    'updated_by_user_id': fields.Integer
}

class AttendanceAPI(AttendanceMixin, restful.Resource):

    @auth_required
    @marshal_with(attendance_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_admin(event_id):
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

        return attendance, 200


    @auth_required
    @marshal_with(attendance_fields)
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_admin(event_id):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND
        
        user = user_repository.get_by_id(user_id)
        if user is None:
            return USER_NOT_FOUND

        if attendance_repository.exists(event_id, user_id):
            return ATTENDANCE_ALREADY_CONFIRMED

        attendance = Attendance(event_id, user_id, registration_user_id)
        attendance_repository.create(attendance)

        send_mail(
            recipient=user.email,
            subject='Welcome to {}'.format(event.name),
            body_text=ATTENDANCE_EMAIL_BODY.format(
                user_title=user.user_title,
                first_name=user.firstname,
                last_name=user.lastname,
                event_name=event.name)
        )

        return attendance, 201


    @auth_required
    def delete(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = args['user_id']
        registration_user_id = g.current_user['id']

        registration_user = user_repository.get_by_id(registration_user_id)
        if not registration_user.is_registration_admin(event_id):
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