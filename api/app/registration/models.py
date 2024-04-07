from datetime import datetime, date, time
from sqlalchemy import func

from app import db
from app.invoice.models import PaymentStatus
from app.tags.models import Tag

class Offer(db.Model):

    __tablename__ = "offer"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),  db.ForeignKey(
        "app_user.id"), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)
    offer_date = db.Column(db.DateTime(), nullable=False)
    expiry_date = db.Column(db.DateTime(), nullable=False)
    payment_required = db.Column(db.Boolean(), nullable=False)
    rejected_reason = db.Column(db.String(5000), nullable=True)
    candidate_response = db.Column(db.Boolean(), nullable=True)
    responded_at = db.Column(db.DateTime(), nullable=True)
    payment_amount = db.Column(db.String(), nullable=True)

    user = db.relationship('AppUser', foreign_keys=[user_id])
    offer_tags = db.relationship('OfferTag')
    offer_invoices = db.relationship('OfferInvoice')

    def is_expired(self):
        end_of_today = datetime.combine(date.today(), time())
        return (self.candidate_response is None) and (self.expiry_date < end_of_today)
    
    def has_valid_invoice(self):
        valid_payment_statuses = [
            PaymentStatus.UNPAID.value,
            PaymentStatus.PAID.value,
            PaymentStatus.FAILED.value
        ]
        for offer_invoice in self.offer_invoices:
            if offer_invoice.invoice.current_payment_status.payment_status in valid_payment_statuses:
                return True
        return False

class OfferTag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    offer_id = db.Column(db.Integer(), db.ForeignKey('offer.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    accepted = db.Column(db.Boolean(), nullable=True)

    offer = db.relationship('Offer', foreign_keys=[offer_id])
    tag = db.relationship('Tag', foreign_keys=[tag_id])

    def __init__(self, offer_id, tag_id, accepted=None):
        self.offer_id = offer_id
        self.tag_id = tag_id
        self.accepted = accepted

class RegistrationForm(db.Model):

    __tablename__ = "registration_form"

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey(
        "event.id"), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    registration_sections = db.relationship('RegistrationSection')

    def __init__(self, event_id):
        self.event_id = event_id


class RegistrationSection(db.Model):

    __tablename__ = "registration_section"

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    show_for_tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=True)
    show_for_invited_guest = db.Column(db.Boolean(), nullable=True)

    registration_questions = db.relationship('RegistrationQuestion')

    def __init__(self, registration_form_id, name, description, order, show_for_tag_id=None, show_for_invited_guest=None):
        self.registration_form_id = registration_form_id
        self.name = name
        self.description = description
        self.order = order
        self.show_for_tag_id = show_for_tag_id
        self.show_for_invited_guest = show_for_invited_guest

def get_registration_answer_by_question_id(user_id, event_id, question_id):
        answer = (
            db.session.query(RegistrationAnswer)
            .join(Registration, RegistrationAnswer.registration_id == Registration.id)
            .join(Offer, Offer.id == Registration.offer_id)
            .filter_by(user_id=user_id, event_id=event_id)
            .join(RegistrationQuestion, RegistrationAnswer.registration_question_id == RegistrationQuestion.id)
            .filter_by(id=question_id)
            .first())
        return answer

class RegistrationQuestion(db.Model):

    __tablename__ = "registration_question"

    id = db.Column(db.Integer(), primary_key=True)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_section.id"), nullable=False)
    type = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    headline = db.Column(db.String(), nullable=False)
    placeholder = db.Column(db.String(), nullable=False)
    validation_regex = db.Column(db.String(), nullable=True)
    validation_text = db.Column(db.String(), nullable=True)
    order = db.Column(db.Integer(), nullable=False)
    options = db.Column(db.JSON(), nullable=True)
    is_required = db.Column(db.Boolean(), nullable=False)
    required_value = db.Column(db.String(), nullable=True)
    depends_on_question_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_question.id"), nullable=True)
    hide_for_dependent_value = db.Column(db.String(), nullable=True)

    tags = db.relationship('RegistrationQuestionTag')

    def __init__(self, registration_form_id, section_id, headline, placeholder, order, type, validation_regex, validation_text=None, is_required=True, description=None, options=None):
        self.registration_form_id = registration_form_id
        self.section_id = section_id
        self.headline = headline
        self.placeholder = placeholder
        self.order = order
        self.type = type
        self.description = description
        self.options = options
        self.is_required = is_required
        self.validation_regex = validation_regex
        self.validation_text = validation_text

class RegistrationQuestionTag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    registration_question_id = db.Column(db.Integer(), db.ForeignKey('registration_question.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)

    registration_question = db.relationship('RegistrationQuestion', foreign_keys=[registration_question_id])
    tag = db.relationship('Tag', foreign_keys=[tag_id])

    def __init__(self, registration_question_id, tag_id):
        self.registration_question_id = registration_question_id
        self.tag_id = tag_id

# Registration

class Registration(db.Model):
    __tablename__ = "registration"

    id = db.Column(db.Integer(), primary_key=True)
    offer_id = db.Column(db.Integer(), db.ForeignKey(
        "offer.id"), nullable=False)
    registration_form_id = db.Column(db.Integer(), db.ForeignKey(
        "registration_form.id"), nullable=False)
    confirmed = db.Column(db.Boolean(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=True)
    confirmation_email_sent_at = db.Column(db.DateTime(), nullable=True)

    def __init__(self, offer_id, registration_form_id, confirmed=False, confirmation_email_sent_at=None):
        self.offer_id = offer_id
        self.registration_form_id = registration_form_id
        self.confirmed = confirmed
        self.created_at = date.today()
        self.confirmation_email_sent_at = confirmation_email_sent_at

    def confirm(self):
        self.confirmed = True


class RegistrationAnswer(db.Model):
    __tablename__ = "registration_answer"
    __table_args__ = tuple([
        db.Index("registration_answer_lookup", "registration_id", "registration_question_id"),
    ])

    id = db.Column(db.Integer(), primary_key=True)
    registration_id = db.Column(db.Integer(), db.ForeignKey(
        'registration.id'), nullable=False)
    registration_question_id = db.Column(db.Integer(), db.ForeignKey(
        'registration_question.id'), nullable=False)
    value = db.Column(db.String(), nullable=False)
