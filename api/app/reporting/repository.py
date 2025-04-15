from app import db
from app.users.models import AppUser
from app.applicationModel.models import Question, Section, QuestionTranslation, SectionTranslation
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewQuestionTranslation, ReviewResponse, ReviewScore, ReviewSection, ReviewSectionTranslation
from app.responses.models import Response, Answer
from sqlalchemy.orm import aliased

class ReportingRepository():

    @staticmethod
    def get_applications_for_form(application_form_id: int, language: str, page: int, per_page: int):
        """Get a paginated list of applications for an application form."""
        query = (
            db.session.query(Answer, Response, Question, QuestionTranslation, Section, SectionTranslation, AppUser)
            .filter_by(is_active=True)
            .join(Response, Answer.response_id == Response.id)
            .filter_by(application_form_id=application_form_id, is_submitted=True)
            .join(Question, Answer.question_id == Question.id)
            .join(QuestionTranslation, Question.id == QuestionTranslation.question_id)
            .filter_by(language=language)
            .join(Section, Question.section_id == Section.id)
            .join(SectionTranslation, Section.id == SectionTranslation.section_id)
            .filter_by(language=language)
            .join(AppUser, Response.user_id == AppUser.id)
        )

        paginated_responses = query.paginate(page=page, per_page=per_page, error_out=False)

        return paginated_responses
    
    @staticmethod
    def get_reviews_for_form(application_form_id: int, language: str, page: int, per_page: int):
        """Get a paginated list of reviews for an application form."""
        Applicant = aliased(AppUser)
        Reviewer = aliased(AppUser)

        query = (
            db.session.query(ReviewScore, ReviewResponse, ReviewSectionTranslation, ReviewQuestionTranslation, 
                             Applicant.id.label("applicant_id"), 
                             Applicant.email.label("applicant_email"),
                             Applicant.firstname.label("applicant_firstname"), 
                             Applicant.lastname.label("applicant_lastname"),
                             Reviewer.id.label("reviewer_id"),
                             Reviewer.email.label("reviewer_email"),
                             Reviewer.firstname.label("reviewer_firstname"),
                             Reviewer.lastname.label("reviewer_lastname"))
            .filter_by(is_active=True)
            .join(ReviewQuestion, ReviewScore.review_question_id == ReviewQuestion.id)
            .join(ReviewQuestionTranslation, ReviewQuestionTranslation.review_question_id == ReviewQuestion.id)
            .filter_by(language=language)
            .join(ReviewSection, ReviewQuestion.review_section_id == ReviewSection.id)
            .join(ReviewSectionTranslation, ReviewSectionTranslation.review_section_id == ReviewSection.id)
            .filter_by(language=language)
            .join(ReviewForm, ReviewSection.review_form_id == ReviewForm.id)
            .filter_by(application_form_id=application_form_id)
            .join(ReviewResponse, ReviewScore.review_response_id == ReviewResponse.id)
            .join(Response, ReviewResponse.response_id == Response.id)
            .join(Applicant, Response.user_id == Applicant.id)
            .join(Reviewer, ReviewResponse.reviewer_user_id == Reviewer.id)
        )
        
        paginated_reviews = query.paginate(page=page, per_page=per_page, error_out=False)

        return paginated_reviews
