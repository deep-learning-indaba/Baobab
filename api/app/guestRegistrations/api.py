from datetime import date
import traceback
from flask_restful import reqparse
import flask_restful as restful
from flask import request
from sqlalchemy.exc import SQLAlchemyError
from app.utils.auth import verify_token
from app.guestRegistrations.mixins import GuestRegistrationMixin, GuestRegistrationFormMixin
from app.invitedGuest.models import GuestRegistration, GuestRegistrationAnswer
from flask_restful import fields, marshal_with, marshal
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.users.models import AppUser
from app.events.models import Event
from app.utils.auth import auth_required
from app.utils import errors, emailer, strings
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app import LOGGER

from app import db


def _get_answer_value(answer, question):
    if question.type == 'multi-choice' and question.options is not None:
        value = [o for o in question.options if o['value'] == answer.value]
        if not value:
            return answer.value
        return value[0]['label']

    if question.type == 'file' and answer.value:
        return 'Uploaded File'

    return answer.value


class GuestRegistrationApi(GuestRegistrationMixin, restful.Resource):
    answer_fields = {
        'id': fields.Integer,
        'guest_registration_id': fields.Integer,
        'registration_question_id': fields.Integer,
        'value': fields.String
    }

    registration_fields = {
        'id': fields.Integer,
        'registration_form_id': fields.Integer,
        'confirmed': fields.Boolean,
        'created_at': fields.DateTime,
        'confirmation_email_sent_at': fields.DateTime,
        'user_id': fields.Integer

    }
    update_registration_fields = {
        'guest_registration_id': fields.Integer,
        'registration_form_id': fields.Integer,
        'confirmed': fields.Boolean,
        'created_at': fields.DateTime,
        'confirmation_email_sent_at': fields.DateTime

    }
    response_fields = {
        'id': fields.Integer,
        'guest_registration_id': fields.Integer,
        'registration_form_id': fields.Integer,
        'answers': fields.List(fields.Nested(answer_fields))
    }

    @marshal_with(response_fields)
    @auth_required
    def get(self):

        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            registration = db.session.query(GuestRegistration).filter(GuestRegistration.user_id == user_id).first()

            if registration is None:
                return 'no Registration', 404
            registration_form = db.session.query(RegistrationForm).filter(RegistrationForm.id == registration.
                                                                          registration_form_id).first()

            if registration_form is None:
                return errors.REGISTRATION_FORM_NOT_FOUND
            db_answers = db.session.query(GuestRegistrationAnswer).filter(
                GuestRegistrationAnswer.guest_registration_id ==
                registration.id, GuestRegistrationAnswer.is_active == True).all()

            response = {
                'guest_registration_id': registration.id,
                'registration_form_id': registration_form.id,
                'answers': db_answers
            }

            return response

        except Exception as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    @marshal_with(registration_fields)
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        args = self.req_parser.parse_args()

        try:

            user_id = verify_token(request.headers.get('Authorization'))['id']
            if not user_id:
                return errors.USER_NOT_FOUND
            current_user = db.session.query(AppUser).filter(AppUser.id == user_id).first()

            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.id == args['registration_form_id']).first()

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            registration = GuestRegistration(
                registration_form_id=args['registration_form_id'],
                user_id=user_id,
                confirmed=True,
                created_at=date.today(),
                confirmation_email_sent_at=date.today()  # None
            )

            db.session.add(registration)
            db.session.commit()

            event = event_repository.get_by_id(registration_form.event_id)
            for answer_args in args['answers']:
                if db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).first():
                    answer = GuestRegistrationAnswer(guest_registration_id=registration.id,
                                                     registration_question_id=answer_args['registration_question_id'],
                                                     value=answer_args['value'], is_active=True)
                    db.session.add(answer)
            db.session.commit()

            registration_answers = db.session.query(GuestRegistrationAnswer).filter(
                GuestRegistrationAnswer.guest_registration_id == registration.id,
                GuestRegistrationAnswer.is_active == True).all()
            registration_questions = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.registration_form_id == args['registration_form_id']).all()

            email_sent = self.send_confirmation(current_user, registration_questions, registration_answers, event)
            if email_sent:
                registration.confirmation_email_sent_at = date.today()
                db.session.commit()

            return registration, 201  # 201 is 'CREATED' status code
        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except Exception as e:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def put(self):
        # Update an existing response for the logged-in user.
        args = self.req_parser.parse_args()
        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']
            registration = db.session.query(GuestRegistration).filter(
                GuestRegistration.id == args['guest_registration_id']).one_or_none()
            if registration is None:
                return 'Registration not found', 404
            registration.registration_form_id = args['registration_form_id']
            db.session.commit()

            for answer_args in args['answers']:
                answer = db.session.query(GuestRegistrationAnswer).filter(
                    GuestRegistrationAnswer.registration_question_id == answer_args['registration_question_id'],
                    GuestRegistrationAnswer.guest_registration_id == args['guest_registration_id'],
                    GuestRegistrationAnswer.is_active == True).one_or_none()
                if answer is not None:
                    answer.is_active = False
                    db.session.merge(answer)
                    new_answer = GuestRegistrationAnswer(guest_registration_id=registration.id,
                                                         registration_question_id=answer_args['registration_question_id'],
                                                         value=answer_args['value'],
                                                         is_active=True)
                    db.session.add(new_answer)

                elif db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).one():

                    answer = GuestRegistrationAnswer(guest_registration_id=registration.id,
                                                         registration_question_id=answer_args['registration_question_id'],
                                                         value=answer_args['value'],
                                                         is_active=True)

                    db.session.add(answer)
            db.session.commit()

            current_user = user_repository.get_by_id(user_id)

            registration_answers = db.session.query(GuestRegistrationAnswer).filter(
                GuestRegistrationAnswer.guest_registration_id == registration.id,
                GuestRegistrationAnswer.is_active == True).all()

            registration_questions = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.registration_form_id == args['registration_form_id']).all()

            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.id == args['registration_form_id']).first()

            event = event_repository.get_by_id(registration_form.event_id)

            email_sent = self.send_confirmation(current_user, registration_questions, registration_answers, event)
            if email_sent:
                registration.confirmation_email_sent_at = date.today()
                db.session.commit()

            return 200
        except Exception as e:
            return 'Could not access DB', 400

    def send_confirmation(self, user, questions, answers, event):
        if answers is None:
            LOGGER.warn(
                'Found no answers associated with response with id {response_id}'.format(response_id=user.id))
        if questions is None:
            LOGGER.warn(
                'Found no questions associated with application form with id {form_id}'.format(form_id=user.id))
        try:
            # Building the summary, where the summary is a dictionary whose key is the question headline, and the value
            # is the relevant answer
            summary = ""
            for answer in answers:
                for question in questions:
                    if answer.registration_question_id == question.id:
                        summary += "Question:" + question.headline + "\nAnswer:" + _get_answer_value(
                            answer, question) + "\n"

            if len(summary) <= 0:
                summary = '\nNo valid questions were answered'

            emailer.email_user(
                'guest-registration-confirmation',
                template_parameters=dict(
                    summary=summary,
                ),
                event=event,
                user=user,
            )

            return True

        except:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(
                response_id=user.id))
            return False


class GuestRegistrationFormAPI(GuestRegistrationFormMixin, restful.Resource):
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
        'id': fields.Integer,
        'event_id': fields.Integer,
        'registration_sections': fields.List(fields.Nested(registration_section_fields))
    }

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        try:
            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.event_id == event_id).first()

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            sections = (db.session.query(RegistrationSection)
                        .filter(RegistrationSection.registration_form_id == registration_form.id)
                        .filter(RegistrationSection.show_for_travel_award == None)
                        .filter(RegistrationSection.show_for_accommodation_award == None)
                        .filter(RegistrationSection.show_for_payment_required == None)
                        .all())

            if not sections:
                LOGGER.warn(
                    'Sections not found for event_id: {}'.format(args['event_id']))
                return errors.SECTION_NOT_FOUND

            registration_form.registration_sections = sections

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
