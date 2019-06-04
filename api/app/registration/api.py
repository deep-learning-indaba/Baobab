from datetime import datetime
import traceback
from flask_restful import fields, marshal_with
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from app.utils import errors
from app import LOGGER
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.models import Offer
from app.registration.mixins import RegistrationFormMixin, RegistrationSectionMixin, RegistrationQuestionMixin
from app.events.models import Event
from app import db


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

    @marshal_with(registration_form_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        offer_id = args['offer_id']

        try:
            offer = db.session.query(Offer).filter(Offer.id == offer_id).first()
            if offer and offer.expiry_date >= datetime.now():
                registration_form = db.session.query(RegistrationForm).filter(
                    RegistrationForm.event_id == event_id).first()

                if not registration_form:
                    return errors.REGISTRATION_FORM_NOT_FOUND

                sections = db.session.query(RegistrationSection).filter(
                    RegistrationSection.registration_form_id == registration_form.id).all()

                if not sections:
                    LOGGER.warn('Sections not found for event_id: {}'.format(args['event_id']))
                    return errors.SECTION_NOT_FOUND

                registration_form.registration_sections = sections

                questions = db.session.query(RegistrationQuestion).filter(
                    RegistrationQuestion.registration_form_id == registration_form.id).all()

                if not questions:
                    LOGGER.warn('Questions not found for  event_id: {}'.format(args['event_id']))
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
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

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

    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        section_id = args['section_id']

        try:

            registration_section = db.session.query(RegistrationSection).filter(RegistrationSection.id == section_id).first()

            if not registration_section:
                return errors.REGISTRATION_SECTION_NOT_FOUND
            else:
                return registration_section, 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

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

    @marshal_with(registration_section_fields)
    def get(self):
        args = self.req_parser.parse_args()
        question_id = args['question_id']

        try:

            question = db.session.query(RegistrationQuestion).filter(RegistrationQuestion.id == question_id).first()

            if not question:
                return errors.REGISTRATION_QUESTION_NOT_FOUND
            else:
                return question, 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

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
