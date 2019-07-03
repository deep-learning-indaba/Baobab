from datetime import date, datetime
import traceback
from flask_restful import reqparse, fields, marshal_with, marshal
import flask_restful as restful
from flask import g, request
from sqlalchemy.exc import SQLAlchemyError
from app.utils.auth import verify_token
from app.registrationResponse.mixins import RegistrationResponseMixin, RegistrationAdminMixin, RegistrationConfirmMixin
from app.registration.models import Offer, Registration, RegistrationAnswer, RegistrationForm, RegistrationQuestion
from app.users.models import AppUser
from app.events.models import Event
from app.utils.auth import auth_required, admin_required
from app.users.repository import UserRepository
from app.events.repository import EventRepository
from app.utils import errors, emailer, strings
from app import LOGGER
from app.users.repository import UserRepository as user_repository
from app.registrationResponse.repository import RegistrationRepository


from app import db


REGISTRATION_MESSAGE = 'Thank you for completing our registration form.'
REGISTRATION_CONFIRMED_MESSAGE = """Your registration to {event_name} has been confirmed! This means that all required payment has been completed. 

We look forward to seeing you at the event!

Kind Regards,
The {event_name} Organisers
"""


def _get_answer_value(answer, question):
    if question.type == 'multi-choice' and question.options is not None:
        value = [o for o in question.options if o['value'] == answer.value]
        if not value:
            return answer.value
        return value[0]['label']

    if question.type == 'file' and answer.value:
        return 'Uploaded File'

    return answer.value


class RegistrationApi(RegistrationResponseMixin, restful.Resource):
    answer_fields = {
        'id': fields.Integer,
        'registration_id': fields.Integer,
        'registration_question_id': fields.Integer,
        'value': fields.String
    }

    registration_fields = {
        'id': fields.Integer,
        'offer_id': fields.Integer,
        'registration_form_id': fields.Integer,
        'confirmed': fields.Boolean,
        'created_at': fields.DateTime,
        'confirmation_email_sent_at': fields.DateTime

    }

    response_fields = {
        'registration_id': fields.Integer,
        'offer_id': fields.Integer,
        'registration_form_id': fields.Integer,
        'answers': fields.List(fields.Nested(answer_fields))
    }

    @auth_required
    def get(self):

        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            db_offer = db.session.query(Offer).filter(Offer.user_id == user_id).first()

            if db_offer is None:
                return errors.OFFER_NOT_FOUND
            registration = db.session.query(Registration).filter(Registration.offer_id == db_offer.id).first()

            if registration is None:
                return 'no Registration', 404
            registration_form = db.session.query(RegistrationForm).filter(RegistrationForm.id == registration.
                                                                          registration_form_id).first()

            if registration_form is None:
                return errors.REGISTRATION_FORM_NOT_FOUND
            db_answers = db.session.query(RegistrationAnswer).filter(RegistrationAnswer.registration_id ==
                                                                     registration.id).all()

            response = {
                'registration_id': registration.id,
                'offer_id': db_offer.id,
                'registration_form_id': registration_form.id,
                'answers': db_answers
            }

            return marshal(response, self.response_fields)

        except Exception as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        args = self.req_parser.parse_args()
        offer_id = args['offer_id']

        try:
            offer = db.session.query(Offer).filter(Offer.id == offer_id).first()

            if not offer:
                return errors.OFFER_NOT_FOUND

            user_id = verify_token(request.headers.get('Authorization'))['id']
            if not user_id:
                return errors.USER_NOT_FOUND
            current_user = db.session.query(AppUser).filter(AppUser.id == user_id).first()

            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.id == args['registration_form_id']).first()

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            registration = Registration(
                offer_id=args['offer_id'],
                registration_form_id=args['registration_form_id'],
                confirmed=True if (not offer.payment_required) else False,
                confirmation_email_sent_at=date.today()
            )

            db.session.add(registration)
            db.session.commit()

            event_name = db.session.query(Event).filter(Event.id == registration_form.event_id).first().name

            for answer_args in args['answers']:
                if db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).first():

                    answer = RegistrationAnswer(registration_id=registration.id,
                                                registration_question_id=answer_args['registration_question_id'],
                                                value=answer_args['value'])

                    db.session.add(answer)
            db.session.commit()

            registration_answers = db.session.query(RegistrationAnswer).filter(
                RegistrationAnswer.registration_id == registration.id).all()
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
            return marshal(registration, self.registration_fields), 201  # 201 is 'CREATED' status code

    @auth_required
    def put(self):
        # Update an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        args = self.req_parser.parse_args()
        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            registration = db.session.query(Registration).filter(
                Registration.id == args['registration_id']).one_or_none()
            if registration is None:
                return 'Registration not found', 404

            db_offer = db.session.query(Offer).filter(Offer.id == registration.offer_id).one_or_none()

            if db_offer is None:
                return errors.OFFER_NOT_FOUND

            if db_offer.user_id != user_id:
                return errors.FORBIDDEN

            registration.registration_form_id = args['registration_form_id']
            db.session.commit()

            for answer_args in args['answers']:
                answer = db.session.query(RegistrationAnswer).filter(
                    RegistrationAnswer.registration_question_id == answer_args['registration_question_id'],
                    RegistrationAnswer.registration_id == args['registration_id']).one_or_none()
                if answer is not None:
                    answer.value = answer_args['value']

                elif db.session.query(RegistrationQuestion).filter(
                        RegistrationQuestion.id == answer_args['registration_question_id']).one():

                    answer = RegistrationAnswer(registration_id=registration.id,
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
            body_text = greeting + '\n\n' + REGISTRATION_MESSAGE + self.get_confirmed_message(confirmed) + '\n\nHere is a copy of your responses:\n\n' + summary

            emailer.send_mail(user.email, subject, body_text=body_text)

        except Exception as e:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(
                response_id=user.id))

    def get_confirmed_message(self, confirmed):
        if not confirmed:
            return '\nPlease note that your spot is pending confirmation on receipt of payment of USD 350. You will receive correspondence with payment instructions in the next few days.\n\n'
        else:
            return 'Your spot is now confirmed and we look forward to welcoming you at the Indaba!'


def map_registration_info(registration_info):
    return {
        'registration_id': registration_info.Registration.id,
        'user_id': registration_info.AppUser.id,
        'firstname': registration_info.AppUser.firstname,
        'lastname': registration_info.AppUser.lastname,
        'email': registration_info.AppUser.email,
        'user_category': registration_info.AppUser.user_category.name,
        'affiliation': registration_info.AppUser.affiliation,
        'created_at': registration_info.Registration.created_at
    }

registration_admin_fields = {
    'registration_id': fields.Integer(),
    'user_id': fields.Integer(),
    'firstname': fields.String(),
    'lastname': fields.String(),
    'email': fields.String(),
    'user_category': fields.String(),
    'affiliation': fields.String(),
    'created_at': fields.DateTime('iso8601')
}


def _get_registrations(event_id, user_id, confirmed):
    try:
        current_user = UserRepository.get_by_id(user_id)
        if not current_user.is_registration_admin(event_id):
            return errors.FORBIDDEN

        registrations = RegistrationRepository.get_confirmed_for_event(event_id, confirmed=confirmed)
        registrations = [map_registration_info(info) for info in registrations]
        return marshal(registrations, registration_admin_fields)
    except Exception as e:
        LOGGER.error('Error occured while retrieving unconfirmed registrations: {}'.format(e))
        return errors.DB_NOT_AVAILABLE


class RegistrationUnconfirmedAPI(RegistrationAdminMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        return _get_registrations(event_id, user_id, confirmed=False)


class RegistrationConfirmedAPI(RegistrationAdminMixin, restful.Resource):
    
    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        return _get_registrations(event_id, user_id, confirmed=True)


def _send_registration_confirmation_mail(user, event_name):
    subject = event_name + ' Registration Confirmation'
    greeting = strings.build_response_email_greeting(user.user_title, user.firstname, user.lastname)
    body_text = greeting + '\n\n' + REGISTRATION_CONFIRMED_MESSAGE.format(event_name=event_name)
    
    try:
        emailer.send_mail(user.email, subject, body_text=body_text)
        return True
    except Exception as e:
        LOGGER.error('Error occured while sending email to {}: {}'.format(user.email, e))
        return False


class RegistrationConfirmAPI(RegistrationConfirmMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        registration_id = args['registration_id']
        user_id = g.current_user['id']

        try:
            current_user = UserRepository.get_by_id(user_id)
            registration, offer = RegistrationRepository.get_by_id_with_offer(registration_id)
            if not current_user.is_registration_admin(offer.event_id):
                return errors.FORBIDDEN

            registration.confirm()
            
            registration_user = UserRepository.get_by_id(offer.user_id)
            registration_event = EventRepository.get_by_id(offer.event_id)
            if _send_registration_confirmation_mail(registration_user, registration_event.name):
                registration.confirmation_email_sent_at = datetime.now()

            db.session.commit()
            return 'Confirmed Registration for {} {}'.format(registration_user.firstname, registration_user.lastname), 200

        except Exception as e:
            LOGGER.error('Error occured while confirming registration with id {}: {}'.format(registration_id, e))
            return errors.DB_NOT_AVAILABLE
