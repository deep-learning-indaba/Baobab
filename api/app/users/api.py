import random
import string
from datetime import datetime
import copy

import flask_restful as restful
from flask import g, request
from flask_restful import fields, marshal, marshal_with, reqparse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import LOGGER, bcrypt, db
from app.events.models import EventRole
import app.events.status as event_status
from app.users.mixins import (AuthenticateMixin, PrivacyPolicyMixin,
                              SignupMixin, UserProfileListMixin,
                              UserProfileMixin, EventAttendeeMixin)
from app.users.models import AppUser, PasswordReset, UserComment
from app.users.repository import UserRepository as user_repository
from app.utils import errors, misc
from app.utils.auth import admin_required, auth_required, generate_token, get_user_from_request
from app.utils.emailer import email_user, send_mail
from app.utils.errors import (ADD_VERIFY_TOKEN_FAILED, BAD_CREDENTIALS,
                              EMAIL_IN_USE, EMAIL_NOT_VERIFIED,
                              EMAIL_VERIFY_CODE_NOT_VALID,
                              ERROR_UPDATING_USER_PROFILE, FORBIDDEN,
                              MISSING_PASSWORD, POLICY_ALREADY_AGREED,
                              POLICY_NOT_AGREED, RESET_PASSWORD_CODE_EXPIRED,
                              RESET_PASSWORD_CODE_NOT_VALID, USER_DELETED,
                              USER_NOT_FOUND, VERIFY_EMAIL_INVITED_GUEST)
from app.utils.misc import make_code
from app.utils.errors import UNAUTHORIZED


user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String,
}


user_comment_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'user_id': fields.Integer,
    'comment_by_user_firstname':  fields.String(attribute='comment_by_user.firstname'),
    'comment_by_user_lastname':  fields.String(attribute='comment_by_user.lastname'),
    'timestamp': fields.DateTime('iso8601'),
    'comment': fields.String
}


def user_info(user, roles):
    return {
        'id': user.id,
        'token': generate_token(user),
        'firstname': user.firstname,
        'lastname': user.lastname,
        'email': user.email,
        'title': user.user_title,
        'is_admin': user.is_admin,
        'is_read_only': user.is_read_only,
        'primary_language': user.user_primaryLanguage,
        'roles': [{'event_id': event_role.event_id, 'role': event_role.role} for event_role in roles]
    }


class UserAPI(SignupMixin, restful.Resource):

    def randomPassword(self, stringLength=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    @auth_required
    @marshal_with(user_fields)
    def get(self):
        user = db.session.query(AppUser).filter(
            AppUser.id == g.current_user['id']).first()
        return user

    def post(self, invitedGuest=False):
        args = self.req_parser.parse_args()
        email = args['email']
        firstname = args['firstname']
        lastname = args['lastname']
        user_title = args['user_title']
        policy_agreed = args['policy_agreed']
        user_primaryLanguage = args['language']

        if(invitedGuest):
            password = self.randomPassword()
        else:
            password = args['password']

        if(password is None):
            return MISSING_PASSWORD
        
        if not policy_agreed:
            return POLICY_NOT_AGREED

        LOGGER.info("Registering email: {}".format(email))

        user = AppUser(
            email=email,
            firstname=firstname,
            lastname=lastname,
            user_title=user_title,
            password=password,
            organisation_id=g.organisation.id)
        user.user_primaryLanguage = user_primaryLanguage

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error("email: {} already in use".format(email))
            return EMAIL_IN_USE

        if(not invitedGuest):
            email_user(
                'verify-email',
                template_parameters=dict(
                    system=g.organisation.system_name,
                    organisation=g.organisation.name,
                    host=misc.get_baobab_host(),
                    token=user.verify_token
                ),
                user=user,
                subject_parameters=dict(system=g.organisation.system_name))

            LOGGER.debug("Sent verification email to {}".format(user.email))
        else:
            user.verified_email = True
            try:
                db.session.commit()
            except IntegrityError:
                LOGGER.error("Unable to verify email: {}".format(email))
                return VERIFY_EMAIL_INVITED_GUEST

        return user_info(user, []), 201

    @auth_required
    def put(self):
        args = self.put_req_parser.parse_args()

        firstname = args['firstname']
        lastname = args['lastname']
        user_title = args['user_title']
        email = args['email']
        user_primaryLanguage = args['language']

        user = db.session.query(AppUser).filter(
            AppUser.id == g.current_user['id']).first()

        if user.email != email:
            user.update_email(email)

        user.firstname = firstname
        user.lastname = lastname
        user.user_title = user_title
        user.user_primaryLanguage = user_primaryLanguage

        try:
            db.session.commit()
        except Exception as e:
            LOGGER.error("Exception updating user profile - {}".format(e))
            return ERROR_UPDATING_USER_PROFILE

        if not user.verified_email:
            email_user(
                'verify-email',
                template_parameters=dict(
                    system=g.organisation.system_name,
                    organisation=g.organisation.name,
                    host=misc.get_baobab_host(),
                    token=user.verify_token
                ),
                user=user,
                subject_parameters=dict(system=g.organisation.system_name))

            LOGGER.debug("Sent re-verification email to {}".format(user.email))

        roles = db.session.query(EventRole).filter(
            EventRole.user_id == user.id).all()

        return user_info(user, roles), 200

    @auth_required
    def delete(self):
        '''
        The function that lets the user delete the account
        '''

        LOGGER.debug("Deleting user: {}".format(g.current_user['id']))

        user = db.session.query(AppUser).filter(
            AppUser.id == g.current_user['id']).first()
        if user:
            user.is_deleted = True
            db.session.commit()
            LOGGER.debug("Successfully deleted user {}".format(
                g.current_user['id']))
        else:
            LOGGER.debug("No user for id {}".format(g.current_user['id']))

        return {}, 200


class UserProfileView:
    def __init__(self, user_response):
        self.user_id = user_response.AppUser.id
        self.email = user_response.AppUser.email
        self.firstname = user_response.AppUser.firstname
        self.lastname = user_response.AppUser.lastname
        self.user_title = user_response.AppUser.user_title
        self.response_id = user_response.Response.id
        self.is_submitted = user_response.Response.is_submitted
        self.submitted_timestamp = user_response.Response.submitted_timestamp
        self.is_withdrawn = user_response.Response.is_withdrawn
        self.withdrawn_timestamp = user_response.Response.withdrawn_timestamp


class UserProfileListView:
    def __init__(self, user_response):
        self.user_id = user_response.AppUser.id
        self.email = user_response.AppUser.email
        self.firstname = user_response.AppUser.firstname
        self.lastname = user_response.AppUser.lastname
        self.user_title = user_response.AppUser.user_title

        if user_response.Response:
            self.response_id = user_response.Response.id
            self.is_submitted = user_response.Response.is_submitted
            self.submitted_timestamp = user_response.Response.submitted_timestamp
            self.is_withdrawn = user_response.Response.is_withdrawn
            self.withdrawn_timestamp = user_response.Response.withdrawn_timestamp
        else:
            self.response_id = -1
            self.is_submitted = None
            self.submitted_timestamp = None
            self.is_withdrawn = None
            self.withdrawn_timestamp = None

        self.type = 'Invited Guest' if user_response.InvitedGuest else 'Candidate'


user_profile_fields = {
    'user_id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String,
    'response_id': fields.Integer,
    'is_submitted': fields.Boolean,
    'submitted_timestamp': fields.DateTime('iso8601'),
    'is_withdrawn': fields.Boolean,
    'withdrawn_timestamp': fields.DateTime('iso8601')
}
user_profile_list_fields = copy.deepcopy(user_profile_fields)
user_profile_list_fields['type'] = fields.String


class UserProfileList(UserProfileListMixin, restful.Resource):

    @marshal_with(user_profile_list_fields)
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        user_responses = user_repository.get_all_with_responses_or_invited_guests_for(event_id)

        views = [UserProfileListView(user_response) for user_response in user_responses]
        return views


class UserProfile(UserProfileMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        user_id = args['user_id']
        current_user_id = g.current_user['id']

        current_user = user_repository.get_by_id(current_user_id)

        if current_user.is_admin or current_user.is_read_only:
            user = user_repository.get_by_id_with_response(user_id)
            if user is None:
                return USER_NOT_FOUND
            return marshal(UserProfileView(user), user_profile_fields)

        user = user_repository.get_by_event_admin(user_id, current_user_id)
        if user is None:
            return USER_NOT_FOUND
        return marshal(UserProfileView(user), user_profile_fields)


class AuthenticationAPI(AuthenticateMixin, restful.Resource):

    def post(self):
        args = self.req_parser.parse_args()

        user = user_repository.get_by_email(args['email'], g.organisation.id)

        LOGGER.debug("Authenticating user: {}".format(args['email']))

        if user:
            if user.is_deleted:
                LOGGER.debug(
                    "Failed to authenticate, user {} deleted".format(args['email']))
                return USER_DELETED

            if not user.verified_email:
                LOGGER.debug(
                    "Failed to authenticate, email {} not verified".format(args['email']))
                return EMAIL_NOT_VERIFIED

            if bcrypt.check_password_hash(user.password, args['password']):
                LOGGER.debug(
                    "Successful authentication for email: {}".format(args['email']))
                roles = db.session.query(EventRole).filter(
                    EventRole.user_id == user.id).all()
                return user_info(user, roles)

        else:
            LOGGER.debug("User not found for {}".format(args['email']))

        return BAD_CREDENTIALS


class AuthenticationRefreshAPI(restful.Resource):

    @auth_required
    def get(self):
        user_id = g.current_user['id']
        user = user_repository.get_by_id(user_id)
        if not user:
            return UNAUTHORIZED

        roles = db.session.query(EventRole).filter(EventRole.user_id == user.id).all()
        return user_info(user, roles)


class PasswordResetRequestAPI(restful.Resource):

    def post(self):

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('email', type=str, required=True)
        args = req_parser.parse_args()

        LOGGER.debug(
            "Requesting password reset for email {} and organisation {}".format(args['email'], g.organisation.name))

        user = user_repository.get_by_email(args['email'], g.organisation.id)

        if not user:
            LOGGER.debug("No user found for email {} and organisation {}".format(args['email'], g.organisation.name))
            return USER_NOT_FOUND

        password_reset = PasswordReset(user=user)
        db.session.add(password_reset)
        db.session.commit()

        email_user(
            'password-reset',
            template_parameters=dict(
                system_name=g.organisation.system_name, 
                organisation=g.organisation.name,
                host=misc.get_baobab_host(), 
                token=password_reset.code
            ),
            subject_parameters=dict(system_name=g.organisation.system_name),
            user=user)

        return {}, 201


class PasswordResetConfirmAPI(restful.Resource):

    def post(self):

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('code', type=str, required=True)
        req_parser.add_argument('password', type=str, required=True)
        args = req_parser.parse_args()

        LOGGER.debug(
            "Confirming password reset for code: {}".format(args['code']))

        password_reset = db.session.query(PasswordReset).filter(
            PasswordReset.code == args['code']).first()

        if not password_reset:
            LOGGER.debug(
                "Reset password code not valid: {}".format(args['code']))
            return RESET_PASSWORD_CODE_NOT_VALID

        if password_reset.date < datetime.now():
            LOGGER.debug(
                "Reset code expired for code: {}".format(args['code']))
            return RESET_PASSWORD_CODE_EXPIRED

        password_reset.user.set_password(args['password'])
        db.session.delete(password_reset)
        db.session.commit()

        LOGGER.debug("Password reset successfully")

        return {}, 201


class VerifyEmailAPI(restful.Resource):

    def get(self):

        token = request.args.get('token')

        LOGGER.debug("Verifying email for token: {}".format(token))

        user = db.session.query(AppUser).filter(
            AppUser.verify_token == token).first()

        if not user:
            LOGGER.debug("No user found for token: {}".format(token))
            return EMAIL_VERIFY_CODE_NOT_VALID

        user.verify()

        db.session.commit()

        LOGGER.debug("Email verified successfully for token: {}".format(token))

        return {}, 201


class ResendVerificationEmailAPI(restful.Resource):
    def get(self):
        email = request.args.get('email')

        LOGGER.debug("Resending verification email to: {}".format(email))
        
        user = user_repository.get_by_email(email, g.organisation.id)

        if not user:
            LOGGER.debug("User not found for email: {} in organisation: {}".format(email, g.organisation.name))
            return USER_NOT_FOUND

        if user.verify_token is None:
            user.verify_token = make_code()

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error("Adding verify token for {} failed. ".format(email))
            return ADD_VERIFY_TOKEN_FAILED

        email_user(
            'verify-email',
            template_parameters=dict(
                system=g.organisation.system_name,
                organisation=g.organisation.name,
                host=misc.get_baobab_host(),
                token=user.verify_token
            ),
            user=user,
            subject_parameters=dict(system=g.organisation.system_name))

        LOGGER.debug("Resent email verification to: {}".format(email))

        return {}, 201


class AdminOnlyAPI(restful.Resource):

    @admin_required
    def get(self):
        return {}, 200


class UserCommentAPI(restful.Resource):

    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=False)
        req_parser.add_argument('user_id', type=int, required=False)
        req_parser.add_argument('comment', type=str, required=False)
        args = req_parser.parse_args()

        current_user_id = g.current_user['id']
        comment = UserComment(args['event_id'], args['user_id'],
                              current_user_id, datetime.now(), args['comment'])

        db.session.add(comment)
        db.session.commit()

        return {}, 201

    @auth_required
    @marshal_with(user_comment_fields)
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('user_id', type=int, required=True)
        args = req_parser.parse_args()

        current_user = user_repository.get_by_id(g.current_user['id'])
        if not current_user.is_event_admin(args['event_id']):
            return FORBIDDEN

        comments = db.session.query(UserComment).filter(
            UserComment.event_id == args['event_id'],
            UserComment.user_id == args['user_id']).all()

        return comments


GENERIC_EMAIL_TEMPLATE = """Dear {user_title} {user_firstname} {user_lastname},

{body}
"""


class EmailerAPI(restful.Resource):

    @admin_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('user_id', type=int, required=True)
        req_parser.add_argument('email_subject', type=str, required=True)
        req_parser.add_argument('email_body', type=str, required=True)
        args = req_parser.parse_args()

        user = user_repository.get_by_id(args['user_id'])
        if user is None:
            return errors.USER_NOT_FOUND
        try:
            send_mail(recipient=user.email,
                      sender_name=g.organisation.name,
                      sender_email=g.organisation.email_from,
                      subject=args['email_subject'],
                      body_text=GENERIC_EMAIL_TEMPLATE.format(
                          user_title=user.user_title,
                          user_firstname=user.firstname,
                          user_lastname=user.lastname,
                          body=args['email_body'],
                      )
                      )
        except Exception as e:
            LOGGER.error('Error sending email: {}'.format(e))
            return errors.EMAIL_NOT_SENT


class PrivacyPolicyAPI(PrivacyPolicyMixin, restful.Resource):
    @auth_required
    def put(self):
        args = self.req_parser.parse_args()
        policy_agreed = args['policy_agreed']

        if not policy_agreed:
            return POLICY_NOT_AGREED
        
        current_user_id = g.current_user['id']
        current_user = user_repository.get_by_id(current_user_id)

        if current_user.has_agreed():
            return POLICY_ALREADY_AGREED

        current_user.agree_to_policy()
        db.session.commit()

        return {}, 200


class EventAttendeeAPI(EventAttendeeMixin, restful.Resource):
    # Check if User is an event attendee
    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user = get_user_from_request()
        status = event_status.get_event_status(event_id, user['id'])
        
        if(not status.is_event_attendee):
            return UNAUTHORIZED

        return 200