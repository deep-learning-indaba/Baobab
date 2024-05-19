import flask_restful as restful
from app.registration.mixins import RegistrationFormMixin
from app.utils.auth import verify_token
import traceback
from flask import request
from sqlalchemy.exc import SQLAlchemyError
from app import LOGGER
from app.utils import errors
from app.utils.auth import auth_required
from app.offer.repository import OfferRepository as offer_repository
from app.registration.repository import RegistrationRepository as registration_repository


def registration_form_info(registration_form):
    return {
        'registration_form_id': registration_form.id,
        'event_id': registration_form.event_id
    }


class RegistrationFormAPI(RegistrationFormMixin, restful.Resource):

    def _serialize_option(self, option):
        return {
            'value': option['value'],
            'label': option['label']
        }

    def _serialize_question(self, question):
        return {
            'id': question.id,
            'description': question.description,
            'headline': question.headline,
            'placeholder': question.placeholder,
            'validation_regex': question.validation_regex,
            'validation_text': question.validation_text,
            'depends_on_question_id': question.depends_on_question_id,
            'hide_for_dependent_value': question.hide_for_dependent_value,
            'type': question.type,
            'is_required': question.is_required,
            'order': question.order,
            'options': [] if not question.options else [self._serialize_option(option) for option in question.options]
        }

    def _serialize_section(self, section):
        return {
            'id': section.id,
            'name': section.name,
            'description': section.description,
            'order': section.order,
            'registration_questions': [self._serialize_question(question) for question in section.registration_questions]
        }

    def _serialize_registration_form(self, registration_form):
        return {
            'id': registration_form.id,
            'event_id': registration_form.event_id,
            'registration_sections': [self._serialize_section(section) for section in registration_form.filtered_registration_sections]
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
            
            if not offer.is_paid():
                return errors.INVOICE_NOT_PAID

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
                if ((section.show_for_tag_id is None or section.show_for_tag_id in [ot.tag_id for ot in offer.offer_tags if ot.accepted is None or ot.accepted])
                    and ((section.show_for_invited_guest is None) or (not section.show_for_invited_guest))):
                    included_sections.append(section)

            registration_form.filtered_registration_sections = included_sections

            return self._serialize_registration_form(registration_form), 200

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))
            return errors.DB_NOT_AVAILABLE
        except:
            LOGGER.error("Encountered unknown error: {}".format(
                traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
