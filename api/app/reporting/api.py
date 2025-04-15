from datetime import date, datetime
from app.utils.language import translatable
from app.reporting.repository import ReportingRepository
from app.guestRegistrations.repository import GuestRegistrationRepository
from app.registrationResponse.repository import RegistrationRepository
from flask_restful import fields, marshal, reqparse
import flask_restful as restful

from app.utils.auth import event_admin_required
from app.applicationModel.repository import ApplicationFormRepository
from app.utils import errors

def response_info(response):
    return {
        'user_id': response.AppUser.id,
        'email': response.AppUser.email,
        'firstname': response.AppUser.firstname,
        'lastname': response.AppUser.lastname,
        'response_id': response.Response.id,
        'response_language': response.Response.language,
        'section_id': response.Section.id,
        'section': response.SectionTranslation.name,
        'question_id': response.Question.id,
        'question': response.QuestionTranslation.headline,
        'answer': response.Answer.value,
    }

def review_info(review):
    return {
        'user_id': review.applicant_id,
        'email': review.applicant_email,
        'firstname': review.applicant_firstname,
        'lastname': review.applicant_lastname,
        'reviewer_user_id': review.reviewer_id,
        'reviewer_email': review.reviewer_email,
        'reviewer_firstname': review.reviewer_firstname,
        'reviewer_lastname': review.reviewer_lastname,
        'review_id': review.ReviewResponse.id,
        'review_language': review.ReviewResponse.language,
        'section_id': review.ReviewSectionTranslation.review_section_id,
        'section': review.ReviewSectionTranslation.headline,
        'question_id': review.ReviewQuestionTranslation.review_question_id,
        'question': review.ReviewQuestionTranslation.headline,
        'score': review.ReviewScore.value,
    }

def answer_info(answer):
    return {
        'question_id': answer.registration_question_id,
        'question': answer.registration_question.headline,
        'answer': answer.value,
    }

def registration_info(registration):
    return {
        'user_id': registration.AppUser.id,
        'email': registration.AppUser.email,
        'firstname': registration.AppUser.firstname,
        'lastname': registration.AppUser.lastname,
        'registration_id': registration.Registration.id,
        'offer_id': registration.Offer.id,
        'type': 'attendee',
        'role': None,
        'answers': [answer_info(answer) for answer in registration.Registration.answers],
        'tags': [ot.tag.stringify_tag_name() for ot in registration.Offer.offer_tags]
    }

def guest_registration_info(guest_registration):
    return {
        'user_id': guest_registration.AppUser.id,
        'email': guest_registration.AppUser.email,
        'firstname': guest_registration.AppUser.firstname,
        'lastname': guest_registration.AppUser.lastname,
        'registration_id': guest_registration.GuestRegistration.id,
        'offer_id': None,
        'type': 'guest',
        'role': guest_registration.InvitedGuest.role,
        'answers': [answer_info(answer) for answer in guest_registration.GuestRegistration.answers if answer.is_active],
        'tags': [it.tag.stringify_tag_name() for it in guest_registration.InvitedGuest.invited_guest_tags]
    }

class ApplicationResponseReportAPI(restful.Resource):

    @event_admin_required
    @translatable
    def get(self, event_id: int, language: str):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('page', type=int, required=False)
        req_parser.add_argument('per_page', type=int, required=False)
        req_args = req_parser.parse_args()

        app_form = ApplicationFormRepository.get_by_event_id(event_id)
        if not app_form:
            return errors.FORM_NOT_FOUND

        try:
            page = req_args['page'] or 1 
            per_page = req_args['per_page'] or 25
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 25
            if per_page > 100:
                per_page = 100
        except ValueError:
            return errors.INVALID_INPUT_MALFORMED_PAGINATION

        paginated_responses = ReportingRepository.get_applications_for_form(
            application_form_id=app_form.id,
            language=language,
            page=page,
            per_page=per_page
        )

        results = [response_info(response) for response in paginated_responses.items]

        return {
            'pagination': {
                'page': paginated_responses.page,
                'per_page': paginated_responses.per_page,
                'total': paginated_responses.total,
                'pages': paginated_responses.pages
            },
            'results': results
        }

class ReviewReportAPI(restful.Resource):

    @event_admin_required
    @translatable
    def get(self, event_id: int, language: str):
        app_form = ApplicationFormRepository.get_by_event_id(event_id)
        if not app_form:
            return errors.APPLICATION_FORM_NOT_FOUND
        reviews = ReportingRepository.get_reviews_for_form(app_form.id, language)
        return [review_info(review) for review in reviews]

class RegistrationsReportAPI(restful.Resource):
    
    @event_admin_required
    def get(self, event_id: int):
        guest_registrations = GuestRegistrationRepository.get_confirmed_guest_for_event(event_id, confirmed=True)
        registrations = RegistrationRepository.get_all_for_event(event_id)

        deduped = [guest_registration_info(guest_registration) for guest_registration in guest_registrations]
        user_ids = [d["user_id"] for d in deduped]
        for registration in registrations:
            if registration.AppUser.id not in user_ids:
                deduped.append(registration_info(registration))

        return deduped
