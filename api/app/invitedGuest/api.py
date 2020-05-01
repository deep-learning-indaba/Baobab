
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from sqlalchemy.exc import IntegrityError

from app.applicationModel.mixins import ApplicationFormMixin
from app.utils.auth import auth_required
from app import LOGGER
from app import db, bcrypt
from flask import g, request
import random
import string

from app.users.models import AppUser, PasswordReset
from app.invitedGuest.models import InvitedGuest
from app.utils.errors import EVENT_NOT_FOUND, USER_NOT_FOUND, ADD_INVITED_GUEST_FAILED, INVITED_GUEST_FOR_EVENT_EXISTS, FORBIDDEN, INVITED_GUEST_EMAIL_FAILED
from app.invitedGuest.mixins import InvitedGuestMixin, InvitedGuestListMixin
from app.users import api as UserAPI
from app.users.mixins import SignupMixin
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from sqlalchemy import func
from app.utils import misc
from app.utils.emailer import send_mail


def invitedGuest_info(invitedGuest, user):
    return {
        'invitedGuest_id': invitedGuest.id,
        'event_id': invitedGuest.event_id,
        'user_id': invitedGuest.user_id,
        'role': invitedGuest.role,
        'fullname': '{} {} {}'.format(user.user_title, user.firstname, user.lastname)
    }

GUEST_EMAIL_TEMPLATE = """Dear {user_title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 
To assist with our planning process, please complete our guest registration form in {system_name}, by visiting {host}/{event_key}/registration 

Please reply to this email should you have any questions or concerns.  

Kind Regards,
The {event_name} Organisers
"""

NEW_GUEST_EMAIL_TEMPLATE = """Dear {user_title} {firstname} {lastname},

We are pleased to invite you to attend {event_name} as a {role}. 
To assist with our planning process, please complete our guest registration form in our portal, {system_name}, by following these instructions:

1. Visit {host}/resetPassword?resetToken={reset_code} to set your account password.
2. Log in using your email address (the one you received this email on!) and new password.
3. Visit {host}/{event_key}registration to complete the registration form.

Please reply to this email should you have any questions or concerns. 

Kind Regards,
The {event_name} Organisers
"""


class InvitedGuestAPI(InvitedGuestMixin, restful.Resource):

    @auth_required
    def post(self, send_email=True):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        email = args['email']
        role = args['role']

        user = user_repository.get_by_email(email, g.organisation.id)

        if not user:
            return USER_NOT_FOUND

        event = event_repository.get_by_id(event_id)
        if not event:
            return EVENT_NOT_FOUND

        existingInvitedGuest = db.session.query(InvitedGuest).filter(
            InvitedGuest.event_id == event_id).filter(InvitedGuest.user_id == user.id).first()

        if existingInvitedGuest:
            return INVITED_GUEST_FOR_EVENT_EXISTS

        invitedGuest = InvitedGuest(
            event_id=event_id,
            user_id=user.id,
            role=role
        )

        db.session.add(invitedGuest)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add invited guest: {}".format(email))
            return ADD_INVITED_GUEST_FAILED

        if send_email:
            try:
                send_mail(
                    recipient=user.email,
                    subject='Your invitation to {}'.format(event.name),
                    body_text=GUEST_EMAIL_TEMPLATE.format(
                        user_title=user.user_title, 
                        firstname=user.firstname, 
                        lastname=user.lastname,
                        role=role,
                        event_name=event.name,
                        event_key=event.key,
                        system_name=g.organisation.system_name,
                        host=misc.get_baobab_host()))
            except Exception as e:
                LOGGER.error('Failed to send email to invited guest with user Id {}, due to {}'.format(user.id, e))
                return INVITED_GUEST_EMAIL_FAILED

        return invitedGuest_info(invitedGuest, user), 201


class CreateUser(SignupMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        user_api = UserAPI.UserAPI()
        user, status = user_api.post(invitedGuest=True)
        if status != 201:
            return user, status

        invited_guest_api = InvitedGuestAPI()
        invited_guest_info, status = invited_guest_api.post(send_email=False)

        if status == 201:
            event_id = invited_guest_info['event_id']
            role = invited_guest_info['role']
            user = user_repository.get_by_id(user['id'])
            event = event_repository.get_by_id(event_id)
            
            reset_code = misc.make_code()
            password_reset=PasswordReset(user=user)
            db.session.add(password_reset)
            db.session.commit()

            try:
                send_mail(
                        recipient=user.email,
                        subject='Your invitation to {}'.format(event.name),
                        body_text=NEW_GUEST_EMAIL_TEMPLATE.format(
                            user_title=user.user_title, 
                            firstname=user.firstname, 
                            lastname=user.lastname,
                            role=role,
                            event_name=event.name,
                            event_key=event.key,
                            system_name=g.organisation.system_name,
                            host=misc.get_baobab_host(),
                            reset_code=password_reset.code))
            except Exception as e:
                LOGGER.error('Failed to send email for invited guest with user Id {} due to: {}'.format(user.id, e))
                return INVITED_GUEST_EMAIL_FAILED

        return invited_guest_info, status


class InvitedGuestView():
    def __init__(self, invitedGuest):
        self.invited_guest_id = invitedGuest.InvitedGuest.id
        self.event_id = invitedGuest.InvitedGuest.event_id
        self.role = invitedGuest.InvitedGuest.role
        self.user_id = invitedGuest.AppUser.id
        self.email = invitedGuest.AppUser.email
        self.firstname = invitedGuest.AppUser.firstname
        self.lastname = invitedGuest.AppUser.lastname
        self.user_title = invitedGuest.AppUser.user_title
        # TODO re-add this using information given from some form of questionnaire
        # self.affiliation = invitedGuest.AppUser.affiliation
        # self.department = invitedGuest.AppUser.department
        # self.nationality_country = invitedGuest.AppUser.nationality_country.name
        # self.residence_country = invitedGuest.AppUser.residence_country.name
        # self.user_category = invitedGuest.AppUser.user_category.name
        # self.user_disability = invitedGuest.AppUser.user_disability
        # self.user_gender = invitedGuest.AppUser.user_gender
        # self.user_dateOfBirth = invitedGuest.AppUser.user_dateOfBirth
        # self.user_primaryLanguage = invitedGuest.AppUser.user_primaryLanguage


class InvitedGuestList(InvitedGuestListMixin, restful.Resource):

    user_profile_list_fields = {
        'user_id': fields.Integer,
        'email': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'user_title': fields.String,
    }

    invited_guest = {
        'invited_guest_id': fields.Integer,
        'event_id': fields.Integer,
        'user': user_profile_list_fields,
        'role': fields.String
    }

    @marshal_with(invited_guest)
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)
        if not (current_user.is_event_admin(event_id) or current_user.is_admin):
            return FORBIDDEN

        invited_guests = db.session.query(InvitedGuest, AppUser).filter_by(event_id=event_id).join(
            AppUser, InvitedGuest.user_id == AppUser.id).all()

        views = [InvitedGuestView(invited_guest)
                 for invited_guest in invited_guests]
        return views


class CheckIfInvitedGuest(InvitedGuestListMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        existing_invited_guest = db.session.query(InvitedGuest).filter(
            InvitedGuest.event_id == event_id).filter(InvitedGuest.user_id == current_user_id).first()

        try:

            if existing_invited_guest is None:
                return "Not an invited guest", 404
            else:
                return "Invited Guest", 200
        except Exception as e:
            return 'Could not access DB', 400
