from datetime import datetime, timedelta

from app import db, bcrypt
from app.utils.misc import make_code


def expiration_date():
    return datetime.now() + timedelta(days=1)


class AppUser(db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    is_admin = db.Column(db.Boolean())

    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.active = True
        self.is_admin = is_admin
        self.set_password(password)

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
