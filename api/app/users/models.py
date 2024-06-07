from datetime import datetime, timedelta

from app import db, bcrypt, LOGGER
from app.utils.misc import make_code
from flask_login import UserMixin
from sqlalchemy.schema import UniqueConstraint

def expiration_date():
    return datetime.now() + timedelta(days=1)


class AppUser(db.Model, UserMixin):

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    user_title = db.Column(db.String(20), nullable=False)
    nationality_country_id = db.Column(db.Integer(), db.ForeignKey('country.id'), nullable=True)
    residence_country_id = db.Column(db.Integer(), db.ForeignKey('country.id'), nullable=True)
    user_gender = db.Column(db.String(20), nullable=True)
    affiliation = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(255), nullable=True)
    user_disability = db.Column(db.String(255), nullable=True)
    user_category_id = db.Column(db.Integer(), db.ForeignKey('user_category.id'), nullable=True)
    user_dateOfBirth = db.Column(db.DateTime(), nullable=True)
    user_primaryLanguage = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=False)
    is_deleted = db.Column(db.Boolean(), nullable=False)
    deleted_datetime_utc = db.Column(db.DateTime(), nullable=True)
    verified_email = db.Column(db.Boolean(), nullable=True)
    verify_token = db.Column(db.String(255), nullable=True, unique=True, default=make_code)
    policy_agreed_datetime = db.Column(db.DateTime(), nullable=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)

    __table_args__ = (UniqueConstraint('email', 'organisation_id', name='org_email_unique'),)

    nationality_country = db.relationship('Country', foreign_keys=[nationality_country_id])
    residence_country = db.relationship('Country', foreign_keys=[residence_country_id])
    user_category = db.relationship('UserCategory')
    event_roles = db.relationship('EventRole')

    def __init__(self,
                 email,
                 firstname,
                 lastname,
                 user_title,
                 password,
                 organisation_id,
                 is_admin=False):
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.user_title = user_title
        self.set_password(password)
        self.organisation_id = organisation_id
        self.active = True
        self.is_admin = is_admin
        self.is_deleted = False
        self.deleted_datetime_utc = None
        self.verified_email = False
        self.agree_to_policy()
        

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def deactivate(self):
        self.active = False
    
    def verify(self):
        self.verified_email = True

    def agree_to_policy(self):
        self.policy_agreed_datetime = datetime.now()
    
    def has_agreed(self):
        return self.policy_agreed_datetime is not None

    def update_email(self, new_email):
        self.verified_email = False
        self.verify_token = make_code()
        self.email = new_email
    
    def delete(self):
        self.is_deleted = True
        self.deleted_datetime_utc = datetime.now()
    
    def _has_admin_role(self, event_id, admin_role_name):
        if self.is_admin:
            return True
        
        if self.event_roles is None:
            return False

        for event_role in self.event_roles:
            if event_role.event_id == event_id and event_role.role == admin_role_name:
                return True
        
        return False
    
    def _has_read_only_role(self, event_id):
        if self.event_roles is None:
            return False
        for event_role in self.event_roles:
            if self.is_admin and event_role.event_id == event_id and (event_role.role == "read_only" or event_role.role == "response_viewer" or event_role.role == "response_editor"):
                return True
        
        return False

    def is_event_admin(self, event_id):
        return self._has_admin_role(event_id, 'admin')
    
    def is_event_response_viewer(self, event_id):
        return self._has_read_only_role(event_id, 'response_viewer')
    
    def is_event_response_editor(self, event_id):
        return self._has_read_only_role(event_id, 'response_editor')
    
    def is_event_admin(self, event_id):
        return self._has_admin_role(event_id, 'admin')

    def is_event_treasurer(self, event_id):
        return self._has_admin_role(event_id, 'treasurer')

    def is_registration_admin(self, event_id):
        # An event admin is also a registration admin
        return self._has_admin_role(event_id, 'registration-admin') or self._has_admin_role(event_id, 'admin')
    
    def is_reviewer(self, event_id):
        if self.event_roles is None:
            return False

        for event_role in self.event_roles:
            if event_role.event_id == event_id and event_role.role == 'reviewer':
                return True

        return False

    def is_registration_volunteer(self, event_id):
        # An event admin is also a registration admin
        return (
            self._has_admin_role(event_id, 'registration-admin') 
            or self._has_admin_role(event_id, 'admin')
            or self._has_admin_role(event_id,'registration-volunteer')
        )
         
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


class UserComment(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    comment_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    comment = db.Column(db.String(2000))

    event = db.relationship('Event')
    user = db.relationship('AppUser', foreign_keys=[user_id])
    comment_by_user = db.relationship('AppUser', foreign_keys=[comment_by_user_id])

    def __init__(self, event_id, user_id, comment_by_user_id, timestamp, comment):
        self.event_id = event_id
        self.user_id = user_id
        self.comment_by_user_id = comment_by_user_id
        self.timestamp = timestamp
        self.comment = comment
