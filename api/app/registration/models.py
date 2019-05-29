
from app import db



class Offer(db.Model):

    __tablename__ = "offer"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),  db.ForeignKey("app_user.id"), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey("event.id"), nullable=False)
    offer_date = db.Column(db.DateTime(), nullable=False)
    expiry_date = db.Column(db.DateTime(), nullable=False)
    payment_required = db.Column(db.String(50), nullable=False)
    travel_award = db.Column(db.String(50), nullable=False)
    accommodation_award = db.Column(db.String(50), nullable=True)
    rejected = db.Column(db.String(50), nullable=True)
    rejected_reason = db.Column(db.String(50), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False)

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
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)

