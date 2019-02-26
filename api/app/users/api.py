from datetime import datetime

from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError


from app.users.mixins import SignupMixin, AuthenticateMixin
from app.users.models import AppUser, PasswordReset

from app.utils.auth import auth_required, admin_required, generate_token
from app.utils.errors import EMAIL_IN_USE, CODE_NOT_VALID, BAD_CREDENTIALS

from app import db, bcrypt
from app.utils.emailer import send_mail
from app import LOGGER


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
    'user_ethnicity': fields.String,
    'user_gender': fields.String,
    'affiliation': fields.String,
    'department': fields.String,
    'user_disability': fields.String,
    'user_category_id': fields.Integer,
    'user_category': fields.String(attribute='user_category.name')
}


def user_info(user):
    return {
        'id': user.id,
        'token': generate_token(user),
        'firstname': user.firstname,
        'lastname': user.lastname,
        'title': user.user_title
    }


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
        user_ethnicity = args['user_ethnicity']
        user_gender = args['user_gender']
        affiliation = args['affiliation']
        department = args['department']
        user_disability = args['user_disability']
        user_category_id = args['user_category_id']
        password = args['password']

        user = AppUser(
            email=email,
            firstname=firstname,
            lastname=lastname,
            user_title=user_title,
            nationality_country_id=nationality_country_id,
            residence_country_id=residence_country_id,
            user_ethnicity=user_ethnicity,
            user_gender=user_gender,
            affiliation=affiliation,
            department=department,
            user_disability=user_disability,
            user_category_id=user_category_id,
            password=password)

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            return EMAIL_IN_USE

        return user_info(user), 201


class AuthenticationAPI(AuthenticateMixin, restful.Resource):

    def post(self):
        args = self.req_parser.parse_args()

        user = db.session.query(AppUser).filter(
            AppUser.email == args['email']).first()
        if user and bcrypt.check_password_hash(user.password, args['password']):
            return user_info(user)

        return BAD_CREDENTIALS


class PasswordResetRequestAPI(restful.Resource):

    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('email', type=str, required=True)
        args = req_parser.parse_args()

        user = db.session.query(AppUser).filter(
            AppUser.email == args['email']).first()
        if user:
            password_reset = PasswordReset(user=user)
            db.session.add(password_reset)
            db.session.commit()
            # Once the SMTP credentials are set, this piece of code can be uncommented
            '''
            send_mail(recipient=args['email'],
                      subject='Password Reset for IndabaDeepLearning portal',
                      body_text='Dear user, Please use the following link to successfully reset your password : www.placeholder.com/ResetPassword?resetToken=[reset_password_token].')
            '''

        return {}, 201


class PasswordResetConfirmAPI(restful.Resource):

    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('code', type=str, required=True)
        req_parser.add_argument('password', type=str, required=True)
        args = req_parser.parse_args()

        password_reset = db.session.query(PasswordReset
                                          ).filter(PasswordReset.code == args['code']
                                                   ).filter(PasswordReset.date > datetime.now()).first()

        if not password_reset:
            return CODE_NOT_VALID

        password_reset.user.set_password(args['password'])
        db.session.delete(password_reset)
        db.session.commit()

        return {}, 200


class AdminOnlyAPI(restful.Resource):

    @admin_required
    def get(self):
        return {}, 200
