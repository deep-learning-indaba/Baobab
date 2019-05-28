
from app import db


class RegistrationForm(db.Model):

    __tablename__ = "registration_form"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)


class RegistrationSection(db.Model):

    __tablename__ = "registration_section"

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey("registration_form.id"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    show_for_travel_award = db.Column(db.Boolean(), nullable=False)
    show_for_accommodation_award = db.Column(db.Boolean(), nullable=False)
    show_for_payment_required = db.Column(db.Boolean(), nullable=False)


class RegistrationQuestion(db.Model):

    __tablename__ = "registration_question"

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey("registration_form.id"), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey("registration_section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=False)
    validation_regex = db.Column(db.String(), nullable=False)
    validation_text = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False)

