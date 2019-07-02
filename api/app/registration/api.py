from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.applicationModel.models import Question
from app.responses.models import Answer, Response
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.mixins import RegistrationFormMixin, RegistrationSectionMixin, RegistrationQuestionMixin
from app.utils.auth import verify_token
import traceback
from flask import g, request
from flask_restful import  fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError
from app.events.models import Event
from app.registration.models import Offer
from app.registration.mixins import OfferMixin
from app.users.models import AppUser
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required, admin_required
from app.utils.emailer import send_mail
from config import BOABAB_HOST

OFFER_EMAIL_BODY = """
Dear {user_title} {first_name} {last_name},

Congratulations! You've been selected to attend the {event_name}!

Please follow the link below to see details and accept your offer: {host}/offer
You have up until the {expiry_date} to accept the offer, otherwise we will automatically allocate your spot to someone else.

If you are unable to accept the offer for any reason, please do let us know by visiting {host}/offer, clicking "Reject" and filling in the reason. 
We will read all of these and if there is anything we can do to accommodate you (for example if more funding for travel becomes available), we may extend you a new offer in a subsequent round.

If you have any queries, please forward them to info@deeplearningindaba.com  

Kind Regards,
The Deep Learning Indaba Team
"""

def get_baobab_host():
    return BOABAB_HOST[:-1] if BOABAB_HOST.endswith('/') else BOABAB_HOST

def offer_info(offer_entity, requested_travel=None):
    return {
        'id': offer_entity.id,
        'user_id': offer_entity.user_id,
        'event_id': offer_entity.event_id,
        'offer_date': offer_entity.offer_date.strftime('%Y-%m-%d'),
        'expiry_date': offer_entity.expiry_date.strftime('%Y-%m-%d'),
        'responded_at': offer_entity.responded_at and offer_entity.responded_at.strftime('%Y-%m-%d'),
        'candidate_response': offer_entity.candidate_response,
        'payment_required': offer_entity.payment_required,
        'travel_award': offer_entity.travel_award,
        'accommodation_award': offer_entity.accommodation_award,
        'accepted_accommodation_award': offer_entity.accepted_accommodation_award,
        'accepted_travel_award': offer_entity.accepted_travel_award,
        'requested_travel': requested_travel and (requested_travel.value == 'transport' or requested_travel.value == 'transport-accommodation'),
        'requested_accommodation': requested_travel and (requested_travel.value == 'accommodation' or requested_travel.value == 'transport-accommodation'),
        'rejected_reason': offer_entity.rejected_reason
    }


def offer_update_info(offer_entity):
    return {
        'id': offer_entity.id,
        'user_id': offer_entity.user_id,
        'event_id': offer_entity.event_id,
        'offer_date': offer_entity.offer_date.strftime('%Y-%m-%d'),
        'expiry_date': offer_entity.expiry_date.strftime('%Y-%m-%d'),
        'payment_required': offer_entity.payment_required,
        'travel_award': offer_entity.travel_award,
        'accommodation_award': offer_entity.accommodation_award,
        'accepted_accommodation_award': offer_entity.accepted_accommodation_award,
        'accepted_travel_award': offer_entity.accepted_travel_award,
        'rejected_reason': offer_entity.rejected_reason,
        'candidate_response': offer_entity.candidate_response,
        'responded_at': offer_entity.responded_at.strftime('%Y-%m-%d')
    }


class OfferAPI(OfferMixin, restful.Resource):
    offer_fields = {
        'id': fields.Integer,
        'user_id': fields.Integer,
        'event_id': fields.Integer,
        'offer_date': fields.DateTime('iso8601'),
        'expiry_date': fields.DateTime('iso8601'),
        'payment_required': fields.Boolean,
        'travel_award': fields.Boolean,
        'accommodation_award': fields.Boolean,
        'accepted_accommodation_award': fields.Boolean,
        'accepted_travel_award': fields.Boolean,
        'rejected_reason': fields.String,
        'candidate_response': fields.Boolean,
        'responded_at': fields.DateTime('iso8601')
    }

    @auth_required
    def put(self):
        # update existing offer
        args = self.req_parser.parse_args()
        offer_id = args['offer_id']
        candidate_response = args['candidate_response']
        accepted_accommodation_award = args['accepted_accommodation_award']
        accepted_travel_award = args['accepted_travel_award']
        rejected_reason = args['rejected_reason']
        offer = db.session.query(Offer).filter(Offer.id == offer_id).first()

        LOGGER.info('Updating offer {} with values: candidate response: {}, Accepted accommodation: {}, '
        'Accepted travel: {}, Rejected Reason: {}'.format(offer_id, candidate_response, accepted_accommodation_award,
        accepted_travel_award, rejected_reason))

        if not offer:
            return errors.OFFER_NOT_FOUND

        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            if offer and offer.user_id != user_id:
                return errors.FORBIDDEN

            offer.responded_at = datetime.now()
            offer.candidate_response = candidate_response
            offer.accepted_accommodation_award = accepted_accommodation_award
            offer.accepted_travel_award = accepted_travel_award
            offer.rejected_reason = rejected_reason

            db.session.commit()

        except Exception as e:
            LOGGER.error("Failed to update offer with id {} due to {}".format(args['offer_id'], e))
            return errors.ADD_OFFER_FAILED
        return offer_update_info(offer), 201

    @admin_required
    def post(self):
        args = self.req_parser.parse_args()
        user_id = args['user_id']
        event_id = args['event_id']
        offer_date = datetime.strptime((args['offer_date']), '%Y-%m-%dT%H:%M:%S.%fZ')
        expiry_date = datetime.strptime((args['expiry_date']), '%Y-%m-%dT%H:%M:%S.%fZ')
        payment_required = args['payment_required']
        travel_award = args['travel_award']
        accommodation_award = args['accommodation_award']
        user = db.session.query(AppUser).filter(AppUser.id == user_id).first()
        event_name = db.session.query(Event).filter(Event.id == event_id).first().name

        existing_offer = db.session.query(Offer).filter(Offer.user_id == user_id, Offer.event_id == event_id).first()
        if existing_offer:
            return errors.DUPLICATE_OFFER

        offer_entity = Offer(
            user_id=user_id,
            event_id=event_id,
            offer_date=offer_date,
            expiry_date=expiry_date,
            payment_required=payment_required,
            travel_award=travel_award,
            accommodation_award=accommodation_award
        )

        db.session.add(offer_entity)
        db.session.commit()

        if user.email:
            send_mail(recipient=user.email, subject='{} Application Status Update'.format(event_name),
                      body_text=OFFER_EMAIL_BODY.format(
                            user_title=user.user_title, first_name=user.firstname, last_name=user.lastname,
                            event_name=event_name, host=get_baobab_host(),
                            expiry_date=offer_entity.expiry_date.strftime("%Y-%m-%d")))

            LOGGER.debug("Sent an offer email to {}".format(user.email))

        return offer_info(offer_entity), 201

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        try:
            offer = db.session.query(Offer).filter(Offer.event_id == event_id).filter(Offer.user_id == user_id).filter().first()

            request_travel = db.session.query(Answer).join(
                Question, Question.id == Answer.question_id
            ).filter(
                Question.headline == 'Would you like to be considered for a travel award?'
            ).join(Response, Answer.response_id == Response.id).filter(
                Response.user_id == user_id, Response.is_submitted == True
            ).first()

            if not offer:
                return errors.OFFER_NOT_FOUND
            else:
                return offer_info(offer, request_travel), 200

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE


def registration_form_info(registration_form):
    return {
        'registration_form_id': registration_form.id,
        'event_id': registration_form.event_id
    }


class RegistrationFormAPI(RegistrationFormMixin, restful.Resource):

    option_fields = {
        'value': fields.String,
        'label': fields.String
    }

    registration_question_fields = {
        'id': fields.Integer,
        'description': fields.String,
        'headline': fields.String,
        'placeholder': fields.String,
        'validation_regex': fields.String,
        'validation_text': fields.String,
        'depends_on_question_id': fields.String,
        'hide_for_dependent_value': fields.String,
        'type': fields.String,
        'is_required': fields.Boolean,
        'order': fields.Integer,
        'options': fields.List(fields.Nested(option_fields))
    }

    registration_section_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'order': fields.Integer,
        'registration_questions': fields.List(fields.Nested(registration_question_fields))
    }

    registration_form_fields = {
        'id':fields.Integer,
        'event_id': fields.Integer,
        'registration_sections': fields.List(fields.Nested(registration_section_fields))
    }

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        offer_id = args['offer_id']
        try:
            offer = db.session.query(Offer).filter(
                Offer.id == offer_id).first()

            user_id = verify_token(request.headers.get('Authorization'))['id']

            if offer and (not offer.user_id == user_id):
                return errors.FORBIDDEN
            
            if not offer.candidate_response:
                return errors.OFFER_NOT_ACCEPTED

            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.event_id == event_id).first()

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            sections = db.session.query(RegistrationSection).filter(
                RegistrationSection.registration_form_id == registration_form.id).all()

            if not sections:
                LOGGER.warn(
                    'Sections not found for event_id: {}'.format(args['event_id']))
                return errors.SECTION_NOT_FOUND

            included_sections = []

            for section in sections:

                if (section.show_for_travel_award is None) and (section.show_for_accommodation_award is None) and  \
                        (section.show_for_payment_required is None):
                    included_sections.append(section)

                elif (section.show_for_travel_award and offer.travel_award and offer.accepted_travel_award) or \
                        (section.show_for_accommodation_award and offer.accommodation_award and offer.accepted_accommodation_award) or \
                        (section.show_for_payment_required and offer.payment_required):
                    included_sections.append(section)

            registration_form.registration_sections = included_sections

            questions = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.registration_form_id == registration_form.id).all()

            if not questions:
                LOGGER.warn(
                    'Questions not found for  event_id: {}'.format(args['event_id']))
                return errors.QUESTION_NOT_FOUND

            for s in registration_form.registration_sections:
                s.registration_questions = []
                for q in questions:
                    if q.section_id == s.id:
                        s.registration_questions.append(q)

            return marshal(registration_form, self.registration_form_fields), 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @admin_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']

        event = db.session.query(Event).filter(
            Event.id == event_id).first()

        if not event:
            return errors.EVENT_NOT_FOUND

        registration_form = RegistrationForm(

            event_id=event_id
        )

        db.session.add(registration_form)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add registration form for event : {}".format(event_id))
            return errors.ADD_REGISTRATION_FORM_FAILED

        return registration_form_info(registration_form), 201


def registration_section_info(registration_section):
    return {
        'registration_form_id': registration_section.registration_form_id,
        'name': registration_section.name,
        'description': registration_section.description,
        'order': registration_section.order,
        'show_for_accommodation_award': registration_section.show_for_accommodation_award,
        'show_for_travel_award': registration_section.show_for_travel_award,
        'show_for_payment_required': registration_section.show_for_payment_required
    }


class RegistrationSectionAPI(RegistrationSectionMixin, restful.Resource):
    registration_section_fields = {
        'sectionId': fields.Integer,
        'name': fields.Boolean,
        'description': fields.String,
        'order': fields.String,
        'questions': RegistrationQuestion,
    }

    @auth_required
    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        section_id = args['section_id']

        try:

            registration_section = db.session.query(RegistrationSection).filter(
                RegistrationSection.id == section_id).first()

            if not registration_section:
                return errors.REGISTRATION_SECTION_NOT_FOUND
            else:
                return registration_section, 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @admin_required
    def post(self):
        args = self.req_parser.parse_args()
        registration_form_id = args['registration_form_id']
        name = args['name']
        description = args['description']
        order = args['order']
        show_for_travel_award = args['show_for_travel_award']
        show_for_accommodation_award = args['show_for_accommodation_award']
        show_for_payment_required = args['show_for_payment_required']

        registration_form = db.session.query(RegistrationForm).filter(
            RegistrationForm.id == registration_form_id).first()

        if not registration_form:
            return errors.REGISTRATION_FORM_NOT_FOUND

        registration_section = RegistrationSection(

            registration_form_id=registration_form_id,
            name=name,
            description=description,
            order=order,
            show_for_accommodation_award=show_for_accommodation_award,
            show_for_travel_award=show_for_travel_award,
            show_for_payment_required=show_for_payment_required
        )

        db.session.add(registration_section)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add registration section with form id : {}".format(registration_form_id))
            return errors.ADD_REGISTRATION_SECTION_FAILED

        return registration_section_info(registration_section), 201


def registration_question_info(registration_question):
    return {
        'registration_form_id': registration_question.registration_form_id,
        'section_id': registration_question.section_id,
        'type': registration_question.type,
        'description': registration_question.description,
        'headline': registration_question.headline,
        'placeholder': registration_question.placeholder,
        'validation_regex': registration_question.validation_regex,
        'validation_text': registration_question.validation_text,
        'order': registration_question.order,
        'options': registration_question.options,
        'is_required': registration_question.is_required
    }


class RegistrationQuestionAPI(RegistrationQuestionMixin, restful.Resource):
    registration_section_fields = {
        'description': fields.String,
        'type': fields.String,
        'required': fields.Boolean,
        'order': fields.Integer,
    }
    @auth_required
    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        question_id = args['question_id']

        try:

            question = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.id == question_id).first()

            if not question:
                return errors.REGISTRATION_QUESTION_NOT_FOUND
            else:
                return question, 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @admin_required
    def post(self):
        args = self.req_parser.parse_args()
        registration_form_id = args['registration_form_id']
        section_id = args['section_id']
        type = args['type']
        description = args['description']
        headline = args['headline']
        placeholder = args['placeholder']
        validation_regex = args['validation_regex']
        validation_text = args['validation_text']
        order = args['order']
        options = args['options']
        is_required = args['is_required']

        registration_form = db.session.query(RegistrationForm).filter(
            RegistrationForm.id == registration_form_id).first()

        registration_section = db.session.query(RegistrationSection).filter(
            RegistrationSection.id == section_id).first()

        if not registration_form:
            return errors.REGISTRATION_FORM_NOT_FOUND
        elif not registration_section:
            return errors.SECTION_NOT_FOUND

        registration_question = RegistrationQuestion(
            registration_form_id=registration_form_id,
            section_id=section_id,
            type=type,
            description=description,
            headline=headline,
            placeholder=placeholder,
            validation_regex=validation_regex,
            validation_text=validation_text,
            order=order,
            options=options,
            is_required=is_required
        )

        db.session.add(registration_question)

        try:
            db.session.commit()
        except IntegrityError:
            LOGGER.error(
                "Failed to add registration question with form id : {}".format(section_id))
            return errors.ADD_REGISTRATION_QUESTION_FAILED

        return registration_question_info(registration_question), 201
