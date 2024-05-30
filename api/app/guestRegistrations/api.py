from datetime import date, datetime
import traceback
from flask_restful import reqparse
import flask_restful as restful
from flask import request, g
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from app.utils.auth import verify_token
from app.guestRegistrations.mixins import GuestRegistrationFormMixin
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
from app.registration.repository import RegistrationRepository as registration_repository
from app.registration.repository import RegistrationFormRepository as registration_form_repository
from app.guestRegistrations.repository import GuestRegistrationRepository as guest_registration_repository
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
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


class GuestRegistrationApi(restful.Resource):
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

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()

        try:
            user_id = g.current_user['id']
            event_id = args['event_id']
            registration_form = registration_repository.get_form_for_event(event_id)
            if registration_form is None:
                return errors.REGISTRATION_FORM_NOT_FOUND

            registration = guest_registration_repository.get_guest_registration(user_id, event_id)
            if registration is None:
                return 'no Registration', 404

            answers = guest_registration_repository.get_answers(registration.id)

            response = {
                'guest_registration_id': registration.id,
                'registration_form_id': registration_form.id,
                'answers': answers
            }

            return marshal(response, self.response_fields), 200

        except Exception as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    @marshal_with(registration_fields)
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('guest_registration_id', type=int, required=False)
        req_parser.add_argument('registration_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        try:
            user_id = g.current_user['id']
            current_user = user_repository.get_by_id(user_id)
            registration_form = registration_form_repository.get_by_id(args['registration_form_id'])

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
                                                     value=answer_args['value'], is_active=True,
                                                     created_on=datetime.now())
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
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('guest_registration_id', type=int, required=False)
        req_parser.add_argument('registration_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()
        
        try:
            user_id = g.current_user['id']
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
                                                         is_active=True,
                                                         created_on=datetime.now())
                    db.session.add(new_answer)

                elif db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).one():

                    answer = GuestRegistrationAnswer(guest_registration_id=registration.id,
                                                     registration_question_id=answer_args['registration_question_id'],
                                                     value=answer_args['value'],
                                                     is_active=True,
                                                     created_on=datetime.now())

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
    def _serialize_question(self, question, baobab_id):
        return {
            'id': question.id,
            'description': question.description.replace('{-baobab_id-}', baobab_id),
            'headline': question.headline,
            'placeholder': question.placeholder,
            'validation_regex': question.validation_regex,
            'validation_text': question.validation_text,
            'depends_on_question_id': question.depends_on_question_id,
            'hide_for_dependent_value': question.hide_for_dependent_value,
            'type': question.type,
            'is_required': question.is_required,
            'order': question.order,
            'options': question.options
        }

    def _serialize_section(self, section, baobab_id):
        return {
            'id': section.id,
            'name': section.name,
            'description': section.description,
            'order': section.order,
            'registration_questions': [self._serialize_question(question, baobab_id) for question in section.registration_questions]
        }

    def _serialize_registration_form(self, registration_form, baobab_id):
        return {
            'id': registration_form.id,
            'event_id': registration_form.event_id,
            'registration_sections': [self._serialize_section(section, baobab_id) for section in registration_form.filtered_registration_sections]
        }


    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        try:
            registration_form = registration_repository.get_form_for_event(event_id)

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            invited_guest = invited_guest_repository.get_for_event_and_user(event_id, g.current_user['id'])
            if not invited_guest:
                return errors.INVITED_GUEST_NOT_FOUND

            included_sections = []
            for section in registration_form.registration_sections:
                if ((section.show_for_tag_id is None or section.show_for_tag_id in [it.tag_id for it in invited_guest.invited_guest_tags])
                    and ((section.show_for_invited_guest is None) or section.show_for_invited_guest)):
                    included_sections.append(section)

            registration_form.filtered_registration_sections = included_sections

            user = user_repository.get_by_id(g.current_user['id'])
            baobab_id = user.verify_token

            return self._serialize_registration_form(registration_form, baobab_id), 200

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except Exception as e:
            LOGGER.error("Encountered unknown error: {}".format(e))
            return errors.DB_NOT_AVAILABLE
