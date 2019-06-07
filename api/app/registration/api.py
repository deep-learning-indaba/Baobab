from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.mixins import RegistrationFormMixin, RegistrationSectionMixin, RegistrationQuestionMixin
from app.utils.auth import verify_token
import traceback
from flask import g, request
from flask_restful import  fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError
from app.events.models import Event
from app.registration.models import Offer
from app.registration.mixins import RegistrationMixin
from app.users.models import AppUser
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required, admin_required

OFFER_EMAIL_BODY = """
Dear {} {} {},

Congratulations on you offer

Offer Details \n
user_id {} \n
event_id {} \n
offer_date {} \n
expiry_date {} \n
payment_required {} \n
travel_award {} \n
accommodation_award {} \n

Kind Regards,
The Baobab Team
"""

def offer_info(offerEntity):
    return {
        'user_id': offerEntity.user_id,
        'event_id': offerEntity.event_id,
        'offer_date': offerEntity.offer_date,
        'expiry_date': offerEntity.expiry_date,
        'payment_required': offerEntity.payment_required,
        'travel_award': offerEntity.travel_award,
        'accommodation_award': offerEntity.accommodation_award
    }

class OfferAPI(RegistrationMixin, restful.Resource):
    put_offer_fields = {
        'user_id': fields.Integer,
        'accepted': fields.Boolean,
        'rejected': fields.Boolean,
        'rejected_reason': fields.String
    }

    @auth_required
    @marshal_with(put_offer_fields)
    def put(self):
        # update existing offer
        args = self.req_parser.parse_args()
        offer_id = args['id']
        accepted = args['accepted']
        rejected = args['rejected']
        rejected_reason = args['rejected_reason']

        offer = db.session.query(Offer).filter(Offer.id == offer_id).first()

        if not offer:
            return errors.OFFER_NOT_FOUND
        else:
            return

        offerValues = Offer(
            accepted = accepted,
            rejected = rejected,
            rejected_reason = rejected_reason
            
        )
     
        try:
            offer = db.session.query(Offer).filter(Offer.id == offer_id).first()
            offer.updated_at = datetime.now()
            user_id = verify_token(request.headers.get('Authorization'))['id']

            if offer and (not offer.user_id == user_id):
                return errors.FORBIDDEN
            else:
                db.session.add(offerValues)
                db.session.commit()

        except:
            LOGGER.error("Failed to add offer with id {}".format(args['id']))
            return errors.ADD_OFFER_FAILED
        return offer(offerValues), 201

    @admin_required
    def post(self):
        args = self.req_parser.parse_args()
        user_id = args['user_id']
        email = g.current_user['email']
        event_id = args['event_id']
        offer_date = args['offer_date']
        expiry_date = args['expiry_date']
        payment_required = args['payment_required']
        travel_award = args['travel_award']
        accommodation_award = args['accommodation_award']

        user = db.session.query(AppUser).filter(AppUser.email == email).first()

        offerEntity = Offer(
            user_id=user_id,
            event_id=event_id,
            offer_date=offer_date,
            expiry_date=expiry_date,
            payment_required=payment_required,
            travel_award=travel_award,
            accommodation_award=accommodation_award
        )

        db.session.add(offerEntity)

        try:
            db.session.add(offerEntity)
            db.session.commit()
            if user.email:
                send_mail(recipient=user.email,
                    subject='Offer from Deep Learning Indaba',
                    body_text= OFFER_EMAIL_BODY.format( 
                                user.user_title, user.firstname, user.lastname,
                                user_id, event_id, offer_date, 
                                expiry_date, payment_required, 
                                travel_award, accommodation_award))

                LOGGER.debug("Sent an offer email to {}".format(user.email))
            else:
                user.verified_email = True
                try:
                    db.session.commit()
                except IntegrityError:
                    LOGGER.error("Unable to verify email: {}".format(email))
                    return VERIFY_EMAIL_OFFER

        except :
            LOGGER.error("Failed to add offer")
            return errors.FORBIDDEN, 404
        
        return self.offer_info(offerEntity), 201

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        try:
            offer = db.session.query(Offer).filter(Offer.event_id == event_id and Offer.user_id == user_id).first()
            if not offer:
                LOGGER.warn(
                    "Offer not found for event_id: {}".format(args['event_id']))
                return errors.EVENT_NOT_FOUND, 404
            else:
                return offer

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

    registration_question_fields = {
        'description': fields.String,
        'type': fields.String,
        'is_required': fields.Boolean,
        'order': fields.Integer
    }

    registration_section_fields = {
        'id': fields.Integer,
        'name': fields.String,
        'description': fields.String,
        'order': fields.Integer,
        'registration_questions': fields.List(fields.Nested(registration_question_fields))
    }

    registration_form_fields = {
        'event_id': fields.Integer,
        'registration_sections': fields.List(fields.Nested(registration_section_fields))
    }

    @auth_required
    @marshal_with(registration_form_fields)
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

            if offer and offer.expiry_date >= datetime.now():

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

                    if (section.show_for_travel_award is None) and (section.show_for_accomodation_award is None) and  \
                            (section.show_for_payment_required is None):
                        included_sections.append(section)

                    elif (section.show_for_travel_award and offer.travel_award) or \
                            (section.show_for_accomodation_award and offer.accomodation_award) or \
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

                return registration_form, 201
            else:
                return errors.OFFER_EXPIRED

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
