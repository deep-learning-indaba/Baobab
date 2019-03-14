from datetime import datetime, timedelta

from app import db, bcrypt, LOGGER
from app.utils.misc import make_code


def expiration_date():
    return datetime.now() + timedelta(days=1)


class AppUser(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    user_title = db.Column(db.String(20), nullable=False)
    nationality_country_id = db.Column(
        db.Integer(), db.ForeignKey('country.id'), nullable=False)
    residence_country_id = db.Column(
        db.Integer(), db.ForeignKey('country.id'), nullable=False)
    user_ethnicity = db.Column(db.String(50), nullable=False)
    user_gender = db.Column(db.String(20), nullable=False)
    affiliation = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=False)
    user_disability = db.Column(db.String(255), nullable=False)
    user_category_id = db.Column(db.Integer(), db.ForeignKey(
        'user_category.id'), nullable=False)
    user_dateOfBirth = db.Column(db.DateTime(), nullable=True)
    user_primaryLanguage = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    is_deleted = db.Column(db.Boolean(), nullable=False)
    deleted_datetime_utc = db.Column(db.DateTime(), nullable=True)
    verified_email = db.Column(db.Boolean(), nullable=True)
    verify_token = db.Column(
        db.String(255), nullable=True, unique=True, default=make_code)
    

    nationality_country = db.relationship(
        'Country', foreign_keys=[nationality_country_id])
    residence_country = db.relationship(
        'Country', foreign_keys=[residence_country_id])
    user_category = db.relationship('UserCategory')

    def __init__(self,
                 email,
                 firstname,
                 lastname,
                 user_title,
                 nationality_country_id,
                 residence_country_id,
                 user_ethnicity,
                 user_gender,
                 affiliation,
                 department,
                 user_disability,
                 user_category_id,
                 user_dateOfBirth,
                 user_primaryLanguage,
                 password,
                 is_admin=False):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.user_title = user_title
        self.nationality_country_id = nationality_country_id
        self.residence_country_id = residence_country_id
        self.user_ethnicity = user_ethnicity
        self.user_gender = user_gender
        self.affiliation = affiliation
        self.department = department
        self.user_disability = user_disability
        self.user_category_id = user_category_id
        self.user_dateOfBirth = user_dateOfBirth
        self.user_primaryLanguage = user_primaryLanguage
        self.set_password(password)
        self.active = True
        self.is_admin = is_admin
        self.is_deleted = False
        self.deleted_datetime_utc = None
        self.verified_email = False

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)

    def deactivate(self):
        self.active = False


class PasswordReset(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'))
    code = db.Column(db.String(255), unique=True, default=make_code)
    date = db.Column(db.DateTime(), default=expiration_date)

    user = db.relationship(AppUser)

    db.UniqueConstraint('user_id', 'code', name='uni_user_code')

    def __init__(self, user):
        self.user = user


class Country(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __init__(self, name):
        self.name = name


class UserCategory(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    group = db.Column(db.String(100))

    def __init__(self, name, description=None, group=None):
        self.name = name
        self.description = description
        self.group = group
