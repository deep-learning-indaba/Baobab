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
from app.guestRegistrations.repository import GuestRegistrationRepository
from app.events.repository import EventRepository as event_repository
import itertools


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

            db_offer = db.session.query(Offer).filter(
                Offer.user_id == user_id).first()

            if db_offer is None:
                return errors.OFFER_NOT_FOUND
            registration = db.session.query(Registration).filter(
                Registration.offer_id == db_offer.id).first()

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
            offer = db.session.query(Offer).filter(
                Offer.id == offer_id).first()

            if not offer:
                return errors.OFFER_NOT_FOUND

            user_id = verify_token(request.headers.get('Authorization'))['id']
            if not user_id:
                return errors.USER_NOT_FOUND
            current_user = db.session.query(AppUser).filter(
                AppUser.id == user_id).first()

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

            event = event_repository.get_by_id(registration_form.event_id)

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

            self.send_confirmation(current_user, registration_questions, registration_answers, registration.confirmed, event)

            # 201 is 'CREATED' status code
            return marshal(registration, self.registration_fields), 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except Exception as e:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
        
            

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

            db_offer = db.session.query(Offer).filter(
                Offer.id == registration.offer_id).one_or_none()

            if db_offer is None:
                return errors.OFFER_NOT_FOUND

            if db_offer.user_id != user_id:
                return errors.FORBIDDEN

            registration.registration_form_id = args['registration_form_id']
            db.session.commit()

            for answer_args in args['answers']:
                answer = db.session.query(RegistrationAnswer).filter(
                    RegistrationAnswer.registration_question_id == answer_args[
                        'registration_question_id'],
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

            current_user = user_repository.get_by_id(user_id)

            registration_answers = db.session.query(RegistrationAnswer).filter(
                RegistrationAnswer.registration_id == registration.id).all()
                
            registration_questions = db.session.query(RegistrationQuestion).filter(
                RegistrationQuestion.registration_form_id == args['registration_form_id']).all()

            registration_form = db.session.query(RegistrationForm).filter(
                RegistrationForm.id == args['registration_form_id']).first()

            event = event_repository.get_by_id(registration_form.event_id)

            self.send_confirmation(
                current_user, registration_questions, registration_answers, registration.confirmed, event)

            return 200
        except Exception as e:
            return 'Could not access DB', 400

    def send_confirmation(self, user, questions, answers, confirmed, event):
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

            emailer.email_user(
                'registration-with-confirmation' if confirmed else 'registration-pending-confirmation',
                template_parameters=dict(
                    summary=summary
                ),
                event=event,
                user=user)

        except Exception as e:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(
                response_id=user.id))


def map_registration_info(registration_info):
    return {
        'registration_id': registration_info.Registration.id,
        'user_id': registration_info.AppUser.id,
        'firstname': registration_info.AppUser.firstname,
        'lastname': registration_info.AppUser.lastname,
        'email': registration_info.AppUser.email,
        # TODO get this from somewhere else
        # 'user_category': registration_info.AppUser.user_category.name,
        # 'affiliation': registration_info.AppUser.affiliation,
        'created_at': registration_info.Registration.created_at,
        'confirmed': registration_info.Registration.confirmed,
    }


def map_registration_info_guests(registration_info):
    if(registration_info and registration_info.GuestRegistration and registration_info.GuestRegistration.id):
        reg_id = registration_info.GuestRegistration.id
        created_at = registration_info.GuestRegistration.created_at
    else:
        reg_id = None
        created_at = None
    return {
        'registration_id': reg_id,
        'user_id': registration_info.AppUser.id,
        'firstname': registration_info.AppUser.firstname,
        'lastname': registration_info.AppUser.lastname,
        'email': registration_info.AppUser.email,
        # TODO get this information from somewhere else
        # 'user_category': registration_info.AppUser.user_category.name,
        # 'affiliation': registration_info.AppUser.affiliation,
        'created_at': created_at,
        'confirmed' : True,
    }


registration_admin_fields = {
    'registration_id': fields.Integer(),
    'user_id': fields.Integer(),
    'firstname': fields.String(),
    'lastname': fields.String(),
    'email': fields.String(),
    'user_category': fields.String(),
    'affiliation': fields.String(),
    'created_at': fields.DateTime('iso8601'),
    'confirmed': fields.Boolean,
}


def _get_registrations(event_id, user_id, confirmed, exclude_already_signed_in=False):
    try:
        current_user = UserRepository.get_by_id(user_id)
        if not current_user.is_registration_volunteer(event_id):
            return errors.FORBIDDEN
        if(exclude_already_signed_in == True):
            registrations = RegistrationRepository.get_unsigned_in_attendees(
                event_id, confirmed=confirmed)
            guest_registration = GuestRegistrationRepository.get_all_unsigned_guests(
                event_id)
        else:
            if confirmed is None: 
                registrations = RegistrationRepository.get_all_for_event(
                    event_id)
            else:
                registrations = RegistrationRepository.get_confirmed_for_event(
                    event_id, confirmed=confirmed)                
            guest_registration = GuestRegistrationRepository.get_all_guests(
                event_id)

        registrations = [map_registration_info(info) for info in registrations]
        guest_registrations = [map_registration_info_guests(
            info) for info in guest_registration]
        all_registrations = registrations + guest_registrations
        # remove duplicates  
        all_registrations_no_duplicates = list()
        for name, group in itertools.groupby(sorted(all_registrations, key=lambda d : d['user_id']), key=lambda d : d['user_id']):
            all_registrations_no_duplicates.append(next(group))
        return marshal(all_registrations_no_duplicates, registration_admin_fields)
    except Exception as e:
        LOGGER.error(
            'Error occured while retrieving unconfirmed registrations: {}'.format(e))
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
        exclude_already_signed_in = args['exclude_already_signed_in'] or None
        # This is just for Indaba
        return _get_registrations(event_id, user_id, confirmed=None, exclude_already_signed_in=exclude_already_signed_in)


def _send_registration_confirmation_mail(user, event):
    try:
        emailer.email_user(
            'registration-confirmed',
            event=event,
            user=user)
        
        return True
    except Exception as e:
        LOGGER.error(
            'Error occured while sending email to {}: {}'.format(user.email, e))
        return False


class RegistrationConfirmAPI(RegistrationConfirmMixin, restful.Resource):

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        registration_id = args['registration_id']
        user_id = g.current_user['id']

        try:
            current_user = UserRepository.get_by_id(user_id)
            registration, offer = RegistrationRepository.get_by_id_with_offer(
                registration_id)
            if not current_user.is_registration_admin(offer.event_id):
                return errors.FORBIDDEN

            registration.confirm()
            registration_user = UserRepository.get_by_id(offer.user_id)
            registration_event = EventRepository.get_by_id(offer.event_id)
            if _send_registration_confirmation_mail(registration_user, registration_event):
                registration.confirmation_email_sent_at = datetime.now()

            db.session.commit()
            return 'Confirmed Registration for {} {}'.format(registration_user.firstname, registration_user.lastname), 200

        except Exception as e:
            LOGGER.error('Error occured while confirming registration with id {}: {}'.format(
                registration_id, e))
            return errors.DB_NOT_AVAILABLE
