from app import db
from app.tags.models import Tag

class InvitedGuest(db.Model):
    __tablename__ = "invited_guest"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        "app_user.id"), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    invited_guest_tags = db.relationship('InvitedGuestTag')


    def __init__(self, event_id, user_id, role):
        self.event_id = event_id
        self.user_id = user_id
        self.role = role

class InvitedGuestTag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)

    invited_guest = db.relationship('InvitedGuest', foreign_keys=[user_id])
    tag = db.relationship('Tag', foreign_keys=[tag_id])

    def __init__(self, user_id, tag_id):
        self.user_id = user_id
        self.tag_id = tag_id


class GuestRegistration(db.Model):
    __tablename__ = "guest_registration"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        "app_user.id"), nullable=False)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    confirmed = db.Column(db.Boolean(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=True)
    confirmation_email_sent_at = db.Column(db.DateTime(), nullable=True)

    def confirm(self, timestamp):
        self.confirmed = True
        self.confirmation_email_sent_at = timestamp


class GuestRegistrationAnswer(db.Model):
    __tablename__ = "guest_registration_answer"

    id = db.Column(db.Integer(), primary_key=True)
    guest_registration_id = db.Column(db.Integer(), db.ForeignKey(
        'guest_registration.id'), nullable=False)
    registration_question_id = db.Column(db.Integer(), db.ForeignKey(
        'registration_question.id'), nullable=False)
    value = db.Column(db.String(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
