
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from sqlalchemy.exc import IntegrityError

from app.utils.auth import auth_required, event_admin_required
from app import LOGGER
from app import db
from flask import g

from app.users.models import AppUser, PasswordReset
from app.invitedGuest.models import InvitedGuest
from app.utils.errors import EVENT_NOT_FOUND, USER_NOT_FOUND, ADD_INVITED_GUEST_FAILED, INVITED_GUEST_FOR_EVENT_EXISTS, FORBIDDEN, INVITED_GUEST_EMAIL_FAILED, INVITED_GUEST_NOT_FOUND, DELETE_INVITED_GUEST_FAILED
from app.invitedGuest.mixins import InvitedGuestListMixin, InvitedGuestTagMixin
from app.users import api as UserAPI
from app.users.mixins import SignupMixin
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.utils import misc
from app.utils.emailer import email_user

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
    'role': fields.String,
    'tags': fields.Raw
}

def invitedGuest_info(invitedGuest, user):
    return {
        'invitedGuest_id': invitedGuest.id,
        'event_id': invitedGuest.event_id,
        'user_id': invitedGuest.user_id,
        'role': invitedGuest.role,
        'fullname': '{} {} {}'.format(user.user_title, user.firstname, user.lastname)
    }

def _serialize_tag(tag, language):
    translation = tag.get_translation(language)
    if translation is None:
        LOGGER.warn('Could not find {} translation for tag id {}'.format(language, tag.id))
        translation = tag.get_translation('en')
    return {
        'id': tag.id,
        'event_id': tag.event_id,
        'tag_type': tag.tag_type.value.upper(),
        'name': translation.name,
        'description': translation.description
    }

class InvitedGuestAPI(restful.Resource):

    @staticmethod
    def _serialize_invited_guest(invited_guest, language):
        return {
            'invited_guest_id': invited_guest.id,
            'event_id': invited_guest.event_id,
            'user_id': invited_guest.user_id,
            'role': invited_guest.role,
            'tags': [_serialize_tag(it.tag, language) for it in invited_guest.invited_guest_tags]
        }
    
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('invited_guest_id', type=int, required=True)
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        invited_guest_id = args['invited_guest_id']
        language = args['language']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)
        if not (current_user.is_event_admin(event_id) or current_user.is_admin):
            return FORBIDDEN
    
        invited_guest = invited_guest_repository.get_by_id(invited_guest_id)
        if not invited_guest:
            return INVITED_GUEST_NOT_FOUND

        return InvitedGuestAPI._serialize_invited_guest(invited_guest, language)
        
    @auth_required
    def post(self, send_email=True):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('email', type=str, required=True)
        req_parser.add_argument('role', type=str, required=True)
        req_parser.add_argument('tag_ids', type=list, required=False, location='json')
        args = req_parser.parse_args()
        event_id = args['event_id']
        email = args['email']
        role = args['role']
        tag_ids = args['tag_ids']

        user = user_repository.get_by_email(email, g.organisation.id)

        if not user:
            return USER_NOT_FOUND

        event = event_repository.get_by_id(event_id)
        if not event:
            return EVENT_NOT_FOUND

        existingInvitedGuest = invited_guest_repository.get_for_event_and_user(event_id, user.id)

        if existingInvitedGuest:
            return INVITED_GUEST_FOR_EVENT_EXISTS

        try:
            invitedGuest = invited_guest_repository.add_invited_guest(event_id, user.id, role, tag_ids)
        except IntegrityError:
            LOGGER.error(
                "Failed to add invited guest: {}".format(email))
            return ADD_INVITED_GUEST_FAILED

        if send_email:
            try:
                email_user(
                    'guest-invitation-with-registration' if event.is_registration_open else 'guest-invitation',
                    template_parameters=dict(
                        role=role,
                        system_name=g.organisation.system_name,
                        host=misc.get_baobab_host(),
                        event_key=event.key
                    ),
                    event=event,
                    user=user)

            except Exception as e:
                LOGGER.error('Failed to send email to invited guest with user Id {}, due to {}'.format(user.id, e))
                return INVITED_GUEST_EMAIL_FAILED

        return invitedGuest_info(invitedGuest, user), 201

    @auth_required
    @event_admin_required
    def delete(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('invited_guest_id', type=int, required=True)
        args = req_parser.parse_args()
        invited_guest_id = args['invited_guest_id']

        invited_guest = invited_guest_repository.get_by_id(invited_guest_id)
        role = invited_guest.role
        if not invited_guest:
            return INVITED_GUEST_NOT_FOUND

        event = event_repository.get_by_id(event_id)
        user = user_repository.get_by_id(invited_guest.user_id)

        try:
            invited_guest_repository.delete_invited_guest(invited_guest_id)
        except Exception as e:
            LOGGER.error('Failed to delete invited guest with user Id {}, due to {}'.format(user.id, e))
            return DELETE_INVITED_GUEST_FAILED

        try:
            email_user(
                'guest-removal',
                template_parameters=dict(
                    event_email=event.email_from,
                    role=role
                ),
                event=event,
                user=user)
        except Exception as e:
            LOGGER.error('Failed to send removal email to guest with user Id {}, due to {}'.format(user.id, e))

        return {"invited_guest_id": invited_guest_id}, 200

class InvitedGuestTagAPI(restful.Resource, InvitedGuestTagMixin):
    @event_admin_required
    def post(self, event_id):
        del event_id
        args = self.req_parser.parse_args()
        tag_id = args['tag_id']
        invited_guest_id = args['invited_guest_id']
        language = args['language']

        invited_guest_tag = invited_guest_repository.tag_invited_guest(invited_guest_id, tag_id)
        return _serialize_tag(invited_guest_tag.tag, language), 201

    @event_admin_required
    def delete(self, event_id):
        del event_id
        args = self.req_parser.parse_args()

        tag_id = args['tag_id']
        invited_guest_id = args['invited_guest_id']

        invited_guest_repository.remove_tag_from_invited_guest(invited_guest_id, tag_id)

        return {}, 200

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

                email_user(
                    'new-guest-registration' if event.is_registration_open else 'new-guest-no-registration',
                    template_parameters=dict(
                        event_key=event.key,
                        system_name=g.organisation.system_name,
                        host=misc.get_baobab_host(),
                        role=role,
                        reset_code=password_reset.code,
                    ),
                    event=event,
                    user=user
                )
            except Exception as e:
                LOGGER.error('Failed to send email for invited guest with user Id {} due to: {}'.format(user.id, e))
                return INVITED_GUEST_EMAIL_FAILED

        return invited_guest_info, status


class InvitedGuestView():
    def __init__(self, invitedGuest, language: str):
        self.invited_guest_id = invitedGuest.InvitedGuest.id
        self.event_id = invitedGuest.InvitedGuest.event_id
        self.role = invitedGuest.InvitedGuest.role
        self.user_id = invitedGuest.AppUser.id
        self.email = invitedGuest.AppUser.email
        self.firstname = invitedGuest.AppUser.firstname
        self.lastname = invitedGuest.AppUser.lastname
        self.user_title = invitedGuest.AppUser.user_title
        self.tags = [_serialize_tag(it.tag, language) for it in invitedGuest.InvitedGuest.invited_guest_tags]


class InvitedGuestList(InvitedGuestListMixin, restful.Resource):

    @marshal_with(invited_guest)
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        language = args['language']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)
        if not (current_user.is_event_admin(event_id) or current_user.is_admin):
            return FORBIDDEN

        invited_guests = db.session.query(InvitedGuest, AppUser).filter_by(event_id=event_id).join(
            AppUser, InvitedGuest.user_id == AppUser.id).all()

        views = [InvitedGuestView(invited_guest, language)
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
