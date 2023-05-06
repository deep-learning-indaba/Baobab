from datetime import datetime
import flask_restful as restful
from sqlalchemy.exc import IntegrityError
from app.applicationModel.models import Question
from app.responses.models import Answer, Response
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationForm
from app.registration.mixins import RegistrationFormMixin, RegistrationSectionMixin, RegistrationQuestionMixin, OfferTagMixin
from app.utils.auth import verify_token
import traceback
from flask import g, request
from flask_restful import  fields, marshal_with, marshal
from sqlalchemy.exc import SQLAlchemyError
from app.events.models import Event
from app.registration.models import Offer, OfferTag
from app.registration.mixins import OfferMixin
from app.users.models import AppUser
from app import db, LOGGER
from app.utils import errors
from app.utils.auth import auth_required, admin_required, event_admin_required
from app.utils.emailer import email_user
from app.utils import misc
from app.outcome.models import Outcome, Status
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.responses.repository import ResponseRepository as response_repository
from app.registration.repository import OfferRepository as offer_repository
from app.registration.repository import RegistrationRepository as registration_repository
from app.users.repository import UserRepository as user_repository

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
        'requested_travel': requested_travel and (requested_travel.value == 'travel' or requested_travel.value == 'travel_and_accomodation'),
        'requested_accommodation': requested_travel and (requested_travel.value == 'accomodation' or requested_travel.value == 'travel_and_accomodation'),
        'rejected_reason': offer_entity.rejected_reason,
        'payment_amount': offer_entity.payment_amount,
        'tags': [OfferAPI._serialize_tag(it) for it in offer_entity.offer_tags if it.tag.active]
    }


def offer_update_info(offer_entity):
    return {
        'id': offer_entity.id,
        'user_id': offer_entity.user_id,
        'event_id': offer_entity.event_id,
        'offer_date': offer_entity.offer_date.strftime('%Y-%m-%d'),
        'expiry_date': offer_entity.expiry_date.strftime('%Y-%m-%d'),
        'payment_required': offer_entity.payment_required,        
        'rejected_reason': offer_entity.rejected_reason,
        'candidate_response': offer_entity.candidate_response,
        'responded_at': offer_entity.responded_at.strftime('%Y-%m-%d'),
        'payment_amount': offer_entity.payment_amount,
        'tags': [OfferAPI._serialize_tag(it) for it in offer_entity.offer_tags if it.tag.active]
    }


class OfferAPI(OfferMixin, restful.Resource):
    offer_fields = {
        'id': fields.Integer,
        'user_id': fields.Integer,
        'event_id': fields.Integer,
        'offer_date': fields.DateTime('iso8601'),
        'expiry_date': fields.DateTime('iso8601'),
        'payment_required': fields.Boolean,
        'rejected_reason': fields.String,
        'candidate_response': fields.Boolean,
        'responded_at': fields.DateTime('iso8601'),
        'payment_amount': fields.String
    }

    @staticmethod
    def _serialize_tag(offer_tag, language='en'):
        translation = offer_tag.tag.get_translation(language)
        if translation is None:
            LOGGER.warn('Could not find {} translation for tag id {}'.format(language, offer_tag.tag.id))
            translation = offer_tag.tag.get_translation('en')
        return {
            'id': offer_tag.tag.id,
            'event_id': offer_tag.tag.event_id,
            'tag_type': offer_tag.tag.tag_type.value.upper(),
            'name': translation.name,
            'description': translation.description,
            'accepted': offer_tag.accepted
        }

    @staticmethod
    def _stringify_tag_name_description(offer_tag, language='en'):
        translation = offer_tag.tag.get_translation(language)
        if translation is None:
            LOGGER.warn('Could not find {} translation for tag id {}'.format(language, offer_tag.tag.id))
            translation = offer_tag.tag.get_translation('en')
        return '{}: {}'.format(translation.name, translation.description)

    @auth_required
    def put(self):
        # update existing offer
        args = self.req_parser.parse_args()
        offer_id = args['offer_id']
        candidate_response = args['candidate_response']
        award_acceptance = args['award_acceptance']
        rejected_reason = args['rejected_reason']
        offer = db.session.query(Offer).filter(Offer.id == offer_id).first()

        LOGGER.info('Updating offer {} with values: candidate response: {}, '
        'Award Acceptance: {}, Rejected Reason: {}'.format(offer_id, candidate_response, award_acceptance, rejected_reason))

        if not offer:
            return errors.OFFER_NOT_FOUND

        try:
            user_id = verify_token(request.headers.get('Authorization'))['id']

            if offer and offer.user_id != user_id:
                return errors.FORBIDDEN

            offer.responded_at = datetime.now()
            offer.candidate_response = candidate_response
            offer.rejected_reason = rejected_reason
            for ai in award_acceptance:
                award_id = ai['id']
                award_accepted = ai['accepted']
                offer_tag = db.session.query(OfferTag).filter(OfferTag.tag_id == award_id).first()
                if not offer_tag or offer_tag.offer_id != offer_id:
                    return errors.OFFER_TAG_NOT_FOUND
                offer_tag.accepted = award_accepted

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
        payment_amount = args['payment_amount']
        user = db.session.query(AppUser).filter(AppUser.id == user_id).first()
        event = db.session.query(Event).filter(Event.id == event_id).first()
        event_email_from = event.email_from

        existing_offer = db.session.query(Offer).filter(Offer.user_id == user_id, Offer.event_id == event_id).first()
        if existing_offer:
            return errors.DUPLICATE_OFFER

        existing_outcome = outcome_repository.get_latest_by_user_for_event(user_id, event_id)
        if existing_outcome:
            if existing_outcome.status == Status.REJECTED:
                return errors.CANDIDATE_REJECTED
            existing_outcome.reset_latest()

        new_outcome = Outcome(
            event_id,
            user_id,
            Status.ACCEPTED,
            g.current_user['id']
        )
        outcome_repository.add(new_outcome)

        offer_entity = Offer(
            user_id=user_id,
            event_id=event_id,
            offer_date=offer_date,
            expiry_date=expiry_date,
            payment_required=payment_required,
            payment_amount=payment_amount
        )

        db.session.add(offer_entity)
        db.session.commit()

        awards = [OfferAPI._stringify_tag_name_description(it) for it in offer_entity.offer_tags if it.tag.active and it.tag.tag_type == "GRANT"]
        print(awards)
        if awards:
            awards_str = '\n\u2022' + awards.join("\n\u2022")
            email_template = 'offer-awards'
        else:
            awards_str = ''
            email_template = 'offer'


        email_user(
            email_template,
            template_parameters=dict(
                host=misc.get_baobab_host(),
                expiry_date=offer_entity.expiry_date.strftime("%Y-%m-%d"),
                event_email_from=event_email_from,
                awards=awards_str
            ),
            event=event,
            user=user)

        return offer_info(offer_entity), 201

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        try:
            offer = db.session.query(Offer).filter(Offer.event_id == event_id).filter(Offer.user_id == user_id).first()
            response = response_repository.get_submitted_by_user_id_for_event(user_id, event_id)
            if not response:
                return errors.RESPONSE_NOT_FOUND
            request_travel = response_repository.get_answer_by_question_key_and_response_id('travel_grant', response.id)
            
            if not offer:
                return errors.OFFER_NOT_FOUND
            elif offer.is_expired():
                return errors.OFFER_EXPIRED
            else:
                return offer_info(offer, request_travel), 200

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

class OfferTagAPI(restful.Resource, OfferTagMixin):
    offer_tag_fields = {
        'id': fields.Integer,
        'offer_id': fields.Integer,
        'tag_id': fields.Integer,
        'accepted': fields.Boolean,
    }

    @marshal_with(offer_tag_fields)
    @event_admin_required
    def post(self, event_id):
        del event_id
        args = self.req_parser.parse_args()
        tag_id = args['tag_id']
        offer_id = args['offer_id']
        accepted = args['accepted']

        return offer_repository.tag_offer(offer_id, tag_id, accepted), 201

    @event_admin_required
    def delete(self, event_id):
        del event_id
        args = self.req_parser.parse_args()
        tag_id = args['tag_id']
        offer_id = args['offer_id']

        offer_repository.remove_tag_from_offer(offer_id, tag_id)

        return {}

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
        'registration_sections': fields.List(fields.Nested(registration_section_fields), attribute='filtered_registration_sections')
    }

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        offer_id = args['offer_id']
        try:
            offer = offer_repository.get_by_id(offer_id)
            user_id = verify_token(request.headers.get('Authorization'))['id']

            if offer and (not offer.user_id == user_id):
                return errors.FORBIDDEN
            
            if not offer.candidate_response:
                return errors.OFFER_NOT_ACCEPTED

            registration_form = registration_repository.get_form_for_event(event_id)

            if not registration_form:
                return errors.REGISTRATION_FORM_NOT_FOUND

            sections = registration_form.registration_sections
            if not sections:
                LOGGER.warn(
                    'Sections not found for event_id: {}'.format(args['event_id']))
                return errors.SECTION_NOT_FOUND

            included_sections = []

            for section in sections:
                if ((section.show_for_tag_id is None or section.show_for_tag_id in [tag.id for tag in offer.offer_tags])
                    and ((section.show_for_invited_guest is None) or (not section.show_for_invited_guest))):
                    included_sections.append(section)

            registration_form.filtered_registration_sections = included_sections

            return marshal(registration_form, self.registration_form_fields), 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
