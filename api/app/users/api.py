from datetime import datetime

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError


from app.users.mixins import SignupMixin, AuthenticateMixin
from app.users.models import AppUser, PasswordReset
from app.events.models import EventRole

from app.utils.auth import auth_required, admin_required, generate_token
from app.utils.errors import EMAIL_IN_USE, RESET_PASSWORD_CODE_NOT_VALID, BAD_CREDENTIALS, EMAIL_NOT_VERIFIED, EMAIL_VERIFY_CODE_NOT_VALID, USER_NOT_FOUND, RESET_PASSWORD_CODE_EXPIRED, USER_DELETED

from app import db, bcrypt, LOGGER
from app.utils.emailer import send_mail

from config import BOABAB_HOST


VERIFY_EMAIL_BODY = """
Dear {} {} {},

Thank you for creating a new Baobab account. Please following link to verify your email address:

{}/verifyEmail?token={}

Kind Regards,
The Baobab Team
"""

RESET_EMAIL_BODY = """
Dear {} {} {},

You recently requested a password reset on Baobab, please use the following link to reset you password:
{}/resetPassword?resetToken={}

If you did not request a password reset, please ignore this email and contact the Deep Learning Indaba organisers.

Kind Regards,
The Baobab Team
"""

user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String,
    'nationality_country_id': fields.Integer,
    'nationality_country': fields.String(attribute='nationality_country.name'),
    'residence_country_id': fields.Integer,
    'residence_country': fields.String(attribute='residence_country.name'),
    'user_gender': fields.String,
    'user_dateOfBirth': fields.DateTime('iso8601'),
    'user_primaryLanguage': fields.String,
    'affiliation': fields.String,
    'department': fields.String,
    'user_disability': fields.String,
    'user_category_id': fields.Integer,
    'user_category': fields.String(attribute='user_category.name')
}


def user_info(user, roles):
    return {
        'id': user.id,
        'token': generate_token(user),
        'firstname': user.firstname,
        'lastname': user.lastname,
        'title': user.user_title,
        'roles': [{'event_id': event_role.event_id, 'role': event_role.role} for event_role in roles]
    }


def get_baobab_host():
    return BOABAB_HOST[:-1] if BOABAB_HOST.endswith('/') else BOABAB_HOST


class UserAPI(SignupMixin, restful.Resource):

    @auth_required
    @marshal_with(user_fields)
    def get(self):
        user = db.session.query(AppUser).filter(
            AppUser.id == g.current_user['id']).first()
        return user

    def post(self):
        args = self.req_parser.parse_args()

        email = args['email']
        firstname = args['firstname']
        lastname = args['lastname']
        user_title = args['user_title']
        nationality_country_id = args['nationality_country_id']
        residence_country_id = args['residence_country_id']
        user_gender = args['user_gender']
        affiliation = args['affiliation']
        department = args['department']
        user_disability = args['user_disability']
        user_category_id = args['user_category_id']
        password = args['password']
        user_dateOfBirth = datetime.strptime(
            (args['user_dateOfBirth']), '%Y-%m-%dT%H:%M:%S.%fZ')
        user_primaryLanguage = args['user_primaryLanguage']

        LOGGER.info("Registering email: {}".format(email))

        user = AppUser(
            email=email,
            firstname=firstname,
            lastname=lastname,
            user_title=user_title,
            nationality_country_id=nationality_country_id,
            residence_country_id=residence_country_id,
            user_gender=user_gender,
            affiliation=affiliation,
            department=department,
            user_disability=user_disability,
            user_category_id=user_category_id,
            user_dateOfBirth=user_dateOfBirth,
            user_primaryLanguage=user_primaryLanguage,
            password=password)

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error("email: {} already in use".format(email))
            return EMAIL_IN_USE

        send_mail(recipient=user.email,
                  subject='Baobab Email Verification',
                  body_text=VERIFY_EMAIL_BODY.format(
                      user_title, firstname, lastname,
                      get_baobab_host(),
                      user.verify_token))

        LOGGER.debug("Sent verification email to {}".format(user.email))

        return user_info(user, []), 201

    @auth_required
    def put(self):
        args = self.req_parser.parse_args()

        email = args['email']
        firstname = args['firstname']
        lastname = args['lastname']
        user_title = args['user_title']
        nationality_country_id = args['nationality_country_id']
        residence_country_id = args['residence_country_id']
        user_gender = args['user_gender']
        affiliation = args['affiliation']
        department = args['department']
        user_disability = args['user_disability']
        user_category_id = args['user_category_id']

        user = db.session.query(AppUser).filter(
            AppUser.id == g.current_user['id']).first()

        user.email = email
        user.firstname = firstname
        user.lastname = lastname
        user.user_title = user_title
        user.nationality_country_id = nationality_country_id
        user.residence_country_id = residence_country_id
        user.user_gender = user_gender
        user.affiliation = affiliation
        user.department = department
        user.user_disability = user_disability
        user.user_category_id = user_category_id

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error("email {} already in use".format(email))
            return EMAIL_IN_USE

        roles = db.session.query(EventRole).filter(EventRole.user_id == user.id).all()

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
            LOGGER.debug("Successfully deleted user {}".format(g.current_user['id']))
        else:
            LOGGER.debug("No user for id {}".format(g.current_user['id']))        
        
        return {}, 200


class AuthenticationAPI(AuthenticateMixin, restful.Resource):

    def post(self):
        args = self.req_parser.parse_args()

        user = db.session.query(AppUser).filter(
            AppUser.email == args['email']).first()

        LOGGER.debug("Authenticating user: {}".format(args['email']))

        if user:
            if user.is_deleted:
                LOGGER.debug("Failed to authenticate, user {} deleted".format(args['email'])) 
                return USER_DELETED

            if not user.verified_email:
                LOGGER.debug("Failed to authenticate, email {} not verified".format(args['email']))
                return EMAIL_NOT_VERIFIED

            if bcrypt.check_password_hash(user.password, args['password']):
                LOGGER.debug("Successful authentication for email: {}".format(args['email']))
                roles = db.session.query(EventRole).filter(EventRole.user_id == user.id).all()
                return user_info(user, roles)

        else:
            LOGGER.debug("User not found for {}".format(args['email']))
        
        return BAD_CREDENTIALS


class PasswordResetRequestAPI(restful.Resource):

    def post(self):        

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('email', type=str, required=True)
        args = req_parser.parse_args()

        LOGGER.debug("Requesting password reset for email {}".format(args['email']))

        user = db.session.query(AppUser).filter(
            AppUser.email == args['email']).first()

        if not user:
            LOGGER.debug("No user found for email {}".format(args['email']))
            return USER_NOT_FOUND

        password_reset = PasswordReset(user=user)
        db.session.add(password_reset)
        db.session.commit()

        send_mail(recipient=args['email'],
                  subject='Password Reset for Deep Learning Indaba portal',
                  body_text=RESET_EMAIL_BODY.format(
            user.user_title, user.firstname, user.lastname,
            get_baobab_host(), password_reset.code))

        return {}, 201


class PasswordResetConfirmAPI(restful.Resource):

    def post(self):        
        
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('code', type=str, required=True)
        req_parser.add_argument('password', type=str, required=True)
        args = req_parser.parse_args()        

        LOGGER.debug("Confirming password reset for code: {}".format(args['code']))

        password_reset = db.session.query(PasswordReset).filter(
            PasswordReset.code == args['code']).first()

        if not password_reset:
            LOGGER.debug("Reset password code not valid: {}".format(args['code']))
            return RESET_PASSWORD_CODE_NOT_VALID

        if password_reset.date < datetime.now():
            LOGGER.debug("Reset code expired for code: {}".format(args['code']))
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

        LOGGER.debug("Resending verification email to: ".format(email))

        user = db.session.query(AppUser).filter(
            AppUser.email == email).first()

        if not user:
            LOGGER.debug("User not found for email: {}".format(email))
            return USER_NOT_FOUND

        send_mail(recipient=user.email,
                  subject='Baobab Email Verification',
                  body_text=VERIFY_EMAIL_BODY.format(
                      user.user_title, user.firstname, user.lastname,
                      get_baobab_host(),
                      user.verify_token))

        LOGGER.debug("Resent email verification to: {}".format(email))

        return {}, 201


class AdminOnlyAPI(restful.Resource):

    @admin_required
    def get(self):
        return {}, 200
