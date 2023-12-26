from datetime import date, datetime
from app.utils.language import translatable
from app.reporting.repository import ReportingRepository
from flask_restful import fields, marshal
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

class ApplicationResponseReportAPI(restful.Resource):

    @event_admin_required
    @translatable
    def get(self, event_id: int, language: str):
        app_form = ApplicationFormRepository.get_by_event_id(event_id)
        if not app_form:
            return errors.APPLICATION_FORM_NOT_FOUND
        responses = ReportingRepository.get_applications_for_form(app_form.id, language)

        return [response_info(response) for response in responses]

class ReviewReportAPI(restful.Resource):

    @event_admin_required
    @translatable
    def get(self, event_id: int, language: str):
        app_form = ApplicationFormRepository.get_by_event_id(event_id)
        if not app_form:
            return errors.APPLICATION_FORM_NOT_FOUND
        reviews = ReportingRepository.get_reviews_for_form(app_form.id, language)
        return [review_info(review) for review in reviews]
