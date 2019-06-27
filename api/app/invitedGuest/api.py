
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

from app.users.models import AppUser
from app.invitedGuest.models import InvitedGuest
from app.utils.errors import USER_NOT_FOUND, ADD_INVITED_GUEST_FAILED, INVITED_GUEST_FOR_EVENT_EXISTS, FORBIDDEN
from app.invitedGuest.mixins import InvitedGuestMixin, InvitedGuestListMixin
from app.users import api as UserAPI
from app.users.mixins import SignupMixin
from app.users.repository import UserRepository as user_repository
from sqlalchemy import func


def invitedGuest_info(invitedGuest, user):
    return {
        'invitedGuest_id': invitedGuest.id,
        'event_id': invitedGuest.event_id,
        'user_id': invitedGuest.user_id,
        'role': invitedGuest.role,
        'fullname': '{} {} {}'.format(user.user_title, user.firstname, user.lastname)
    }


class InvitedGuestAPI(InvitedGuestMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        email = args['email']
        role = args['role']

        user = db.session.query(AppUser).filter(
            func.lower(AppUser.email) == func.lower(email)).first()

        if not user:
            return USER_NOT_FOUND

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

        return invitedGuest_info(invitedGuest, user), 201


class CreateUser(SignupMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        user_api = UserAPI.UserAPI()
        user, status = user_api.post(True)
        if status != 201:
            return user, status

        invited_guest_api = InvitedGuestAPI()
        return invited_guest_api.post()


class InvitedGuestView():
    def __init__(self, invitedGuest):
        self.invited_guest_id = invitedGuest.InvitedGuest.id
        self.event_id = invitedGuest.InvitedGuest.event_id
        self.role = invitedGuest.InvitedGuest.role
        self.user_id = invitedGuest.AppUser.id
        self.email = invitedGuest.AppUser.email
        self.affiliation = invitedGuest.AppUser.affiliation
        self.department = invitedGuest.AppUser.department
        self.firstname = invitedGuest.AppUser.firstname
        self.lastname = invitedGuest.AppUser.lastname
        self.nationality_country = invitedGuest.AppUser.nationality_country.name
        self.residence_country = invitedGuest.AppUser.residence_country.name
        self.user_category = invitedGuest.AppUser.user_category.name
        self.user_disability = invitedGuest.AppUser.user_disability
        self.user_gender = invitedGuest.AppUser.user_gender
        self.user_title = invitedGuest.AppUser.user_title
        self.user_dateOfBirth = invitedGuest.AppUser.user_dateOfBirth
        self.user_primaryLanguage = invitedGuest.AppUser.user_primaryLanguage


class InvitedGuestList(InvitedGuestListMixin, restful.Resource):

    user_profile_list_fields = {
        'user_id': fields.Integer,
        'email': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'user_title': fields.String,
        'nationality_country': fields.String,
        'residence_country': fields.String,
        'user_gender': fields.String,
        'user_dateOfBirth': fields.DateTime('iso8601'),
        'user_primaryLanguage': fields.String,
        'affiliation': fields.String,
        'department': fields.String,
        'user_disability': fields.String,
        'user_category_id': fields.Integer,
        'user_category': fields.String,
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
