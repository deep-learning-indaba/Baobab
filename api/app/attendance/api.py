from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from app import db

from app.attendance.emails import ATTENDANCE_EMAIL_BODY
from app.attendance.mixins import AttendanceMixin
from app.attendance.models import Attendance
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.events.repository import EventRepository as event_repository
from app.users.repository import UserRepository as user_repository
from app.utils.auth import auth_required
from app.utils.emailer import send_mail
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, ATTENDANCE_NOT_FOUND, EVENT_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, OFFER_NOT_FOUND, REGISTRATION_NOT_FOUND
from app.registration.models import RegistrationQuestion
from app.registration.models import Offer
from app.invitedGuest.models import GuestRegistration
from app.registration.models import RegistrationForm
from app.registration.models import Registration
from app.registration.models import get_registration_answer_based_headline

attendance_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'user_id': fields.Integer,
    'timestamp': fields.DateTime('iso8601'),
    'updated_by_user_id': fields.Integer,
    'accommodation_award': fields.Boolean,
    'shirt_size': fields.String,
    'is_invitedguest': fields.Boolean,
    'bringing_poster': fields.Boolean,
    'message': fields.String
}


class AttendanceUser():
    def __init__(self, attendance, accommodation_award, shirt_size, is_invitedguest, bringing_poster):
        self.id = attendance.id
        self.event_id = attendance.event_id
        self.user_id = attendance.user_id
        self.timestamp = attendance.timestamp
        self.updated_by_user_id = attendance.updated_by_user_id
        self.accommodation_award = accommodation_award
        self.shirt_size = shirt_size
        self.is_invitedguest = is_invitedguest
        self.bringing_poster = bringing_poster


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

        # Other Fields
        offer = db.session.query(Offer).filter(
            Offer.user_id == 1).filter(Offer.event_id == event_id).first()

        if not offer:
            # Check if Guest Registration
            registration = None
            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.event_id == event_id).first()
            if(registration_form):
                registration = db.session.query(GuestRegistration).filter(
                    GuestRegistration.user_id == user_id).filter(GuestRegistration.registration_form_id == registration_form.id).first()

            if not registration:
                return OFFER_NOT_FOUND
        else:
            # Normal registration
            registration = db.session.query(Registration).filter(
                Registration.offer_id == offer.id).first()

            if not registration:
                return REGISTRATION_NOT_FOUND

        is_guest_registration = (not offer and registration)

        # Accom award
        has_accepted_accom_award = (
            offer.accommodation_award and offer.accepted_accommodation_award)

        # Shirt Size
        shirt_answer = get_registration_answer_based_headline(
            user_id, "T-Shirt Size") or "N\A"
        # Poster registration
        bringing_poster = False
        poster_answer = get_registration_answer_based_headline(
            user_id, "Will you be bringing a poster?")
        if (poster_answer is not None and poster_answer.value == 'yes'):
            bringing_poster = True

        attendance_user = AttendanceUser(
            attendance, has_accepted_accom_award, shirt_answer, is_guest_registration, poster_answer)
        return attendance_user, 201

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
