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


user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title_id': fields.Integer,
    'nationality_country_id': fields.Integer,
    'residence_country_id': fields.Integer,
    'user_ethnicity_id': fields.Integer,
    'user_gender_id': fields.Integer,
    'affiliation': fields.String,
    'department': fields.String,
    'user_disability_id': fields.Integer,
    'user_category_id': fields.Integer
}


class UserAPI(SignupMixin, restful.Resource):

    @auth_required
    @marshal_with(user_fields)
    def get(self):
        user = db.session.query(AppUser).filter(AppUser.id==g.current_user['id']).first()
        return user

    def post(self):
        args = self.req_parser.parse_args()

        email = args['email']
        firstname = args['firstname']
        lastname = args['lastname']
        user_title_id = args['user_title_id']
        nationality_country_id = args['nationality_country_id']
        residence_country_id = args['residence_country_id']
        user_ethnicity_id = args['user_ethnicity_id']
        user_gender_id = args['user_gender_id']
        affiliation = args['affiliation']
        department = args['department']
        user_disability_id = args['user_disability_id']
        user_category_id = args['user_category_id']
        password = args['password']

        user = AppUser(
            email=email,
            firstname=firstname,
            lastname=lastname,
            user_title_id=user_title_id,
            nationality_country_id=nationality_country_id,
            residence_country_id=residence_country_id,
            user_ethnicity_id=user_ethnicity_id,
            user_gender_id=user_gender_id,
            affiliation=affiliation,
            department=department,
            user_disability_id=user_disability_id,
            user_category_id=user_category_id,
            password=password)

        db.session.add(user)

        try:
            db.session.commit()
        except IntegrityError:
            return EMAIL_IN_USE

        return {
            'id': user.id,
            'token': generate_token(user)
        }, 201


class AuthenticationAPI(AuthenticateMixin, restful.Resource):

    def post(self):
        args = self.req_parser.parse_args()

        user = db.session.query(AppUser).filter(AppUser.email==args['email']).first()
        if user and bcrypt.check_password_hash(user.password, args['password']):

            return {
                'id': user.id,
                'token': generate_token(user)
            }

        return BAD_CREDENTIALS


class PasswordResetRequestAPI(restful.Resource):

    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('email', type=str, required=True)
        args = req_parser.parse_args()

        user = db.session.query(AppUser).filter(AppUser.email==args['email']).first()
        if user:
            password_reset = PasswordReset(user=user)
            db.session.add(password_reset)
            db.session.commit()
            # TODO: Send the email using any preferred method

        return {}, 201


class PasswordResetConfirmAPI(restful.Resource):

    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('code', type=str, required=True)
        req_parser.add_argument('password', type=str, required=True)
        args = req_parser.parse_args()

        password_reset = db.session.query(PasswordReset
                            ).filter(PasswordReset.code==args['code']
                            ).filter(PasswordReset.date>datetime.now()).first()

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
