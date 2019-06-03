from datetime import datetime
import traceback

from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from flask import g, request

from sqlalchemy.exc import SQLAlchemyError

from app.utils import errors, emailer, strings
from app import LOGGER
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.models import Offer
from app.registration.mixins import RegistrationFormMixin
from app.events.models import Event

from app.utils.auth import auth_required

from app import db, bcrypt


def registration_form_info(registration_form):
    return {
        'registration_form_id': registration_form.id,
        'event_id': registration_form.event_id
    }


class RegistrationFormAPI(RegistrationFormMixin, restful.Resource):

    registration_form_fields = {
        'eventId': fields.Integer,
        'isOpen': fields.Boolean,
        'sections': RegistrationSection
    }

    @auth_required
    @marshal_with(registration_form_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        offer_id = args['offer_id']

        try:

            offer = db.session.query(Offer).filter(Offer.id == offer_id).first()
            LOGGER.error("Offer object {}".format(offer))
            if offer and offer.expiry_date >= datetime.now():
                registration_form = db.session.query(RegistrationForm).filter(RegistrationForm.event_id == event_id).\
                    first()
                if not registration_form:
                    return errors.REGISTRATION_FORM_NOT_FOUND

                return registration_form
            else:
                return errors.OFFER_EXPIRED

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
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


class RegistrationSectionAPI(restful.Resource):
    registration_section_fields = {
        'sectionId': fields.Integer,
        'name': fields.Boolean,
        'description': fields.String,
        'order': fields.String,
        'questions': RegistrationQuestion,
    }

    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        section_id = args['event_id']

        try:

            registration_section = db.session.query(RegistrationSection).filter(RegistrationSection.id == section_id).first()

            if not registration_section:
                return errors.REGISTRATION_SECTION_NOT_FOUND
            else:
                return registration_section

        except SQLAlchemyError as e:
            # LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            # LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
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
            # LOGGER.error(
            #     "Failed to add registration section with form id : {}".format(registration_form_id))
            return errors.ADD_REGISTRATION_SECTION_FAILED

        return registration_section_info(registration_section), 201


def registration_question_info(registration_quesiton):
    return {
        'registration_form_id': registration_quesiton.registration_form_id,
        'section_id': registration_quesiton.section_id,
        'type': registration_quesiton.type,
        'description': registration_quesiton.description,
        'headline': registration_quesiton.headline,
        'placeholder': registration_quesiton.placeholder,
        'validation_regex': registration_quesiton.validation_regex,
        'validation_text': registration_quesiton.validation_text,
        'order': registration_quesiton.order,
        'options': registration_quesiton.options,
        'is_required': registration_quesiton.is_required
    }


class RegistrationQuestionAPI(restful.Resource):
    registration_section_fields = {
        'description': fields.String,
        'type': fields.String,
        'required': fields.Boolean,
        'order': fields.Integer,
    }

    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        question_id = args['question_id']

        try:

            question = db.session.query(RegistrationQuestion).filter(RegistrationQuestion.id == question_id).first()

            if not question:
                return errors.REGISTRATION_QUESTION_NOT_FOUND
            else:
                return question

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
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

        registration_section= db.session.query(RegistrationSection).filter(
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
