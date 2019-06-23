from datetime import date
import traceback
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from flask import g, request
from sqlalchemy.exc import SQLAlchemyError
from app.utils.auth import verify_token
from app.guestRegistration.mixins import GuestRegistrationMixin
from app.registration.models import RegistrationForm, RegistrationQuestion
from app.invitedGuest.models import GuestRegistration, GuestRegistrationAnswer
from app.users.models import AppUser
from app.events.models import Event
from app.utils.auth import auth_required
from app.utils import errors, emailer, strings
from app import LOGGER
from app.users.repository import UserRepository as user_repository


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
        'registration_id': fields.Integer,
        'registration_question_id': fields.Integer,
        'value': fields.String
    }

    registration_fields = {
        'id':fields.Integer,
        'registration_form_id': fields.Integer,
        'confirmed': fields.Boolean,
        'created_at': fields.DateTime,
        'confirmation_email_sent_at': fields.DateTime

    }

    response_fields = {
        'id': fields.Integer,
        'registration_id': fields.Integer,
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
            db_answers = db.session.query(GuestRegistrationAnswer).filter(GuestRegistrationAnswer.registration_id ==
                                                                     registration.id).all()

            response = {
                'registration_id': registration.id,
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
                confirmation_email_sent_at=date.today()
            )

            db.session.add(registration)
            db.session.commit()

            event_name = db.session.query(Event).filter(Event.id == registration_form.event_id).first().name

            for answer_args in args['answers']:
                if db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).first():

                    answer = GuestRegistrationAnswer(registration_id=registration.id,
                                                    registration_question_id=answer_args['registration_question_id'],
                                                    value=answer_args['value'])

                    db.session.add(answer)
            db.session.commit()

            registration_answers = db.session.query(GuestRegistrationAnswer).filter(
                GuestRegistrationAnswer.registration_id == registration.id).all()
            registration_questions = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.registration_form_id == args['registration_form_id']).all()

            self.send_confirmation(current_user, registration_questions, registration_answers, registration.confirmed,
                                   event_name)

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except Exception as e:
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
        finally:
            return registration, 201  # 201 is 'CREATED' status code

    @auth_required
    def put(self):
        # Update an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        args = self.req_parser.parse_args()
        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            registration = db.session.query(GuestRegistration).filter(GuestRegistration.id == args['registration_id']).first()
            registration = db.session.query(GuestRegistration).all()
            if registration is None:
                return 'Registration not found', 404
            else:
                return len(registration),200

            registration.registration_form_id = args['registration_form_id']
            db.session.commit()

            for answer_args in args['answers']:
                answer = db.session.query(GuestRegistrationAnswer).filter(GuestRegistrationAnswer.registration_question_id
                                                                     == answer_args['registration_question_id']).first()
                if answer is not None:
                    answer.value = answer_args['value']

                elif db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).first():

                    answer = GuestRegistrationAnswer(registration_id=registration.id,
                                                        registration_question_id=answer_args['registration_question_id'],
                                                        value=answer_args['value'])

                    db.session.add(answer)
            db.session.commit()
            return 200
        except Exception as e:
            return 'Could not access DB', 400

    def send_confirmation(self, user, questions, answers, confirmed, event_name):
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
                        summary += "Question heading :" + question.headline + "\nQuestion Description :" + \
                           question.description + "\nAnswer :" + _get_answer_value(
                                answer, question) + "\n"

            subject = event_name + ' Registration'
            greeting = strings.build_response_email_greeting(user.user_title, user.firstname, user.lastname)
            if len(summary) <= 0:
                summary = '\nNo valid questions were answered'
            body_text = greeting + self.get_confirmed_message(confirmed) + '\n\n' + summary

            emailer.send_mail(user.email, subject, body_text=body_text)

        except Exception as e:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(
                response_id=user.id))

    def get_confirmed_message(self, confirmed):
        if not confirmed:
            return '\nregistration is pending confirmation on receipt of payment.\n\n'
        else:
            return ''