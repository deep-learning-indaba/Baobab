from datetime import datetime, timedelta

from app import db, bcrypt
from app.utils.misc import make_code


def expiration_date():
    return datetime.now() + timedelta(days=1)


class AppUser(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    user_title_id = db.Column(db.Integer(), db.ForeignKey('user_title.id'), nullable=False)
    nationality_country_id = db.Column(db.Integer(), db.ForeignKey('country.id'), nullable=False)
    residence_country_id = db.Column(db.Integer(), db.ForeignKey('country.id'), nullable=False)
    user_ethnicity_id = db.Column(db.Integer(), db.ForeignKey('user_ethnicity.id'), nullable=False)
    user_gender_id = db.Column(db.Integer(), db.ForeignKey('user_gender.id'), nullable=False)
    affiliation = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(255), nullable=False)
    user_disability_id = db.Column(db.Integer(), db.ForeignKey('user_disability.id'), nullable=False)
    user_category_id = db.Column(db.Integer(), db.ForeignKey('user_category.id'), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    is_deleted = db.Column(db.Boolean(), nullable=False)
    deleted_datetime_utc = db.Column(db.DateTime(), nullable=True)

    def __init__(self,
                 email,
                 firstname,
                 lastname,
                 user_title_id,
                 nationality_country_id,
                 residence_country_id,
                 user_ethnicity_id,
                 user_gender_id,
                 affiliation,
                 department,
                 user_disability_id,
                 user_category_id,
                 password,
                 is_admin=False):
        self.email = email
        self.firstname = firstname,
        self.lastname = lastname,
        self.user_title_id = user_title_id,
        self.nationality_country_id = nationality_country_id,
        self.residence_country_id = residence_country_id,
        self.user_ethnicity_id = user_ethnicity_id,
        self.user_gender_id = user_gender_id,
        self.affiliation = affiliation,
        self.department = department,
        self.user_disability_id = user_disability_id,
        self.user_category_id = user_category_id
        self.set_password(password)
        self.active = True
        self.is_admin = is_admin
        self.is_deleted = False
        self.deleted_datetime_utc = None

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

class UserTitle(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(10), nullable=False)

class Country(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class UserEthnicity(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class UserGender(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(10), nullable=False)

class UserCategory(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    group = db.Column(db.String(100))
    
class UserDisability(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)