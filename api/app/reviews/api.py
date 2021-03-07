from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from math import ceil
import random
from sqlalchemy.sql import func, exists

from app import db, LOGGER
from app.applicationModel.models import ApplicationForm
from app.events.models import Event, EventRole
from app.events.repository import EventRepository as event_repository
from app.responses.repository import ResponseRepository as response_repository
from app.responses.models import Response, ResponseReviewer
from app.reviews.mixins import ReviewMixin, GetReviewResponseMixin, PostReviewResponseMixin, PostReviewAssignmentMixin, \
    GetReviewAssignmentMixin, GetReviewHistoryMixin, GetReviewSummaryMixin
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore, ReviewQuestion
from app.reviews.repository import ReviewRepository as review_repository
from app.reviews.repository import ReviewConfigurationRepository as review_configuration_repository
from app.references.repository import ReferenceRequestRepository as reference_repository

from app.users.models import AppUser, Country, UserCategory
from app.users.repository import UserRepository as user_repository

from app.events.repository import EventRepository as event_repository
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND, REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND

from app.utils.auth import auth_required, event_admin_required
from app.utils.errors import EVENT_NOT_FOUND, REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, RESPONSE_NOT_FOUND, \
    REVIEW_FORM_NOT_FOUND, REVIEW_ALREADY_COMPLETED

from app.utils import misc
from app.utils.emailer import email_user

option_fields = {
    'value': fields.String,
    'label': fields.String
}

answer_fields = {
    'id': fields.Integer,
    'question_id': fields.Integer,
    'question': fields.String(attribute='question.headline'),
    'value': fields.String(attribute='value_display'),
    'question_type': fields.String(attribute='question.type')
}

response_fields = {
    'id': fields.Integer,
    'application_form_id': fields.Integer,
    'user_id': fields.Integer,
    'is_submitted': fields.Boolean,
    'submitted_timestamp': fields.DateTime(dt_format='iso8601'),
    'is_withdrawn': fields.Boolean,
    'withdrawn_timestamp': fields.DateTime(dt_format='iso8601'),
    'started_timestamp': fields.DateTime(dt_format='iso8601'),
    'answers': fields.List(fields.Nested(answer_fields))
}

user_fields = {
    'nationality_country': fields.String(attribute='nationality_country.name'),
    'residence_country': fields.String(attribute='residence_country.name'),
    'affiliation': fields.String,
    'department': fields.String,
    'user_category': fields.String(attribute='user_category.name'),
    'id': fields.Integer
}

review_scores_fields = {
    'review_question_id': fields.Integer,
    'value': fields.String
}

review_response_fields = {
    'id': fields.Integer,
    'review_form_id': fields.Integer,
    'response_id': fields.Integer,
    'reviewer_user_id': fields.Integer,
    'scores': fields.List(fields.Nested(review_scores_fields), attribute='review_scores'),
    'language': fields.String
}

reference_fields = {
    'firstname': fields.String,
    'title': fields.String,
    'lastname': fields.String,
    'relation': fields.String,
    'uploaded_document': fields.String,
}

review_fields = {
    'review_form': fields.Raw,
    'response': fields.Nested(response_fields),
    'user': fields.Nested(user_fields),
    'reviews_remaining_count': fields.Integer,
    'review_response': fields.Nested(review_response_fields),
    'references': fields.List(fields.Nested(reference_fields)),
    'is_submitted': fields.Boolean,
    'submitted_timestamp': fields.DateTime(dt_format='iso8601')
}


def _serialize_review_form(review_form, language):
    review_questions = []
    for question in review_form.review_questions:
        translation = question.get_translation(language)
        if translation is None:
            LOGGER.warn('Missing {} translation for review question id {}'.format(language, question.id))
            translation = question.get_translation('en')
        review_questions.append({
            'id': question.id,
            'question_id': question.question_id,
            'description': translation.description,
            'headline': translation.headline,
            'type': question.type,
            'placeholder': translation.placeholder,
            'options': translation.options,
            'is_required': question.is_required,
            'order': question.order,
            'validation_regex': translation.validation_regex,
            'validation_text': translation.validation_text,
            'weight': question.weight
        })

    form = {
        'id': review_form.id,
        'application_form_id': review_form.application_form_id,
        'is_open': review_form.is_open,
        'deadline': review_form.deadline.isoformat(),
        'review_questions': review_questions
    }

    return form


def _add_reviewer_role(user_id, event_id):
    event_role = EventRole('reviewer', user_id, event_id)
    db.session.add(event_role)
    db.session.commit()


class ReviewResponseUser():
    def __init__(self, review_form, response, reviews_remaining_count, language, reference_responses=None,
                 review_response=None):
        self.review_form = _serialize_review_form(review_form, language)
        self.response = response
        self.user = None if response is None else response.user
        self.reviews_remaining_count = reviews_remaining_count
        self.references = reference_responses
        self.review_response = review_response


class ReviewResponseReference():
    def __init__(self, title, firstname, lastname, relation, uploaded_document):
        self.title = title
        self.firstname = firstname
        self.lastname = lastname
        self.relation = relation
        self.uploaded_document = uploaded_document


class ReviewAPI(ReviewMixin, restful.Resource):

    @auth_required
    @marshal_with(review_fields)
    def get(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']

        review_form = review_repository.get_review_form(event_id)
        if review_form is None:
            return EVENT_NOT_FOUND

        reviews_remaining_count = review_repository.get_remaining_reviews_count(g.current_user['id'],
                                                                                review_form.application_form_id)
        skip = self.sanitise_skip(args['skip'], reviews_remaining_count)

        response = review_repository.get_response_to_review(skip, g.current_user['id'], review_form.application_form_id)

        references = []
        if response is not None:
            reference_requests = reference_repository.get_all_by_response_id(response.id)

            for r in reference_requests:
                reference = reference_repository.get_reference_by_reference_request_id(r.id)
                if reference is not None:
                    references.append(
                        ReviewResponseReference(r.title, r.firstname, r.lastname, r.relation,
                                                reference.uploaded_document)
                    )

        review_response = None if response is None else review_repository.get_review_response(review_form.id,
                                                                                              response.id,
                                                                                              g.current_user['id'])
        references = None if len(references) == 0 else references

        return ReviewResponseUser(
            review_form,
            response,
            reviews_remaining_count,
            args['language'],
            reference_responses=references,
            review_response=review_response
        )

    def sanitise_skip(self, skip, reviews_remaining_count):
        if skip is None:
            skip = 0

        if skip < 0:
            skip = 0

        if reviews_remaining_count == 0:
            skip = 0
        elif skip >= reviews_remaining_count:
            skip = reviews_remaining_count - 1

        return skip


class ResponseReviewAPI(restful.Resource):
    @auth_required
    @marshal_with(review_fields)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('response_id', type=int, required=True)
        parser.add_argument('event_id', type=int, required=True)
        parser.add_argument('language', type=str, required=True)
        args = parser.parse_args()

        response_id = args['response_id']
        event_id = args['event_id']

        review_form = review_repository.get_review_form(event_id)
        if review_form is None:
            return REVIEW_FORM_NOT_FOUND

        response = review_repository.get_response_by_reviewer(response_id, g.current_user['id'])

        if response is None:
            return RESPONSE_NOT_FOUND

        review_response = review_repository.get_review_response(review_form.id, response_id, g.current_user['id'])

        return ReviewResponseUser(review_form, response, 0, args['language'], review_response=review_response)


class ReviewResponseAPI(GetReviewResponseMixin, PostReviewResponseMixin, restful.Resource):

    @auth_required
    @marshal_with(review_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        id = args['id']
        reviewer_user_id = g.current_user['id']

        review_form_response = review_repository.get_review_response_with_form(id, reviewer_user_id)

        if review_form_response is None:
            return REVIEW_RESPONSE_NOT_FOUND

        review_form, review_response = review_form_response

        response = review_repository.get_response_by_review_response(id, reviewer_user_id,
                                                                     review_form.application_form_id)

        return ReviewResponseUser(review_form, response, 0, args['language'], review_response=review_response)

    @auth_required
    @marshal_with(review_response_fields)
    def post(self):
        args = self.post_req_parser.parse_args()
        validation_result = self.validate_scores(args['scores'])
        if validation_result is not None:
            return validation_result

        response_id = args['response_id']
        review_form_id = args['review_form_id']
        reviewer_user_id = g.current_user['id']
        scores = args['scores']
        language = args['language']
        is_submitted = args['is_submitted']

        response_reviewer = review_repository.get_response_reviewer(response_id, reviewer_user_id)
        if response_reviewer is None:
            return FORBIDDEN

        review_response = ReviewResponse(review_form_id, reviewer_user_id, response_id, language)
        review_response.review_scores = self.get_review_scores(scores)
        if is_submitted:
            review_response.submit()
        review_repository.add_model(review_response)

        return review_response, 201

    @auth_required
    @marshal_with(review_response_fields)
    def put(self):
        args = self.post_req_parser.parse_args()
        validation_result = self.validate_scores(args['scores'])
        if validation_result is not None:
            return validation_result

        response_id = args['response_id']
        review_form_id = args['review_form_id']
        reviewer_user_id = g.current_user['id']
        scores = args['scores']
        is_submitted = args['is_submitted']

        response_reviewer = review_repository.get_response_reviewer(response_id, reviewer_user_id)
        if response_reviewer is None:
            return FORBIDDEN

        review_response = review_repository.get_review_response(review_form_id, response_id, reviewer_user_id)
        if review_response is None:
            return REVIEW_RESPONSE_NOT_FOUND

        review_repository.delete_review(review_response)
        review_response.review_scores = self.get_review_scores(scores)
        if is_submitted:
            review_response.submit()
        db.session.commit()

        return review_response, 200

    def get_review_scores(self, scores):
        review_scores = []
        for score in scores:
            review_score = ReviewScore(score['review_question_id'], score['value'])
            review_scores.append(review_score)
        return review_scores

    def validate_scores(self, scores):
        for score in scores:
            if 'review_question_id' not in score.keys():
                return self.get_error_message('review_question_id')
            if 'value' not in score.keys():
                return self.get_error_message('value')

    def get_error_message(self, key):
        return (
        {'message': {key: 'Missing required parameter in the JSON body or the post body or the query string'}}, 400)


class ReviewCountView():
    def __init__(self, count):
        self.email = count.email
        self.user_title = count.user_title
        self.firstname = count.firstname
        self.lastname = count.lastname
        self.reviews_allocated = count.reviews_allocated
        self.reviews_completed = count.reviews_completed
        self.reviewer_user_id = count.reviewer_user_id

class ReviewSummaryAPI(GetReviewSummaryMixin, restful.Resource):
    @auth_required
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        config = review_configuration_repository.get_configuration_for_event(event_id)

        return {
            'reviews_unallocated': review_repository.count_unassigned_reviews(event_id, config.num_reviews_required)
        }


class ReviewAssignmentAPI(GetReviewAssignmentMixin, PostReviewAssignmentMixin, restful.Resource):
    reviews_count_fields = {
        'reviewer_user_id': fields.Integer,
        'email': fields.String,
        'user_title': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'reviews_allocated': fields.Integer,
        'reviews_completed': fields.Integer
    }

    @auth_required
    @marshal_with(reviews_count_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        counts = review_repository.count_reviews_allocated_and_completed_per_reviewer(event_id)
        views = [ReviewCountView(count) for count in counts]
        return views

    @auth_required
    def post(self):
        args = self.post_req_parser.parse_args()
        user_id = g.current_user['id']
        event_id = args['event_id']
        reviewer_user_email = args['reviewer_user_email']
        num_reviews = args['num_reviews']

        event = event_repository.get_by_id(event_id)
        if not event:
            return EVENT_NOT_FOUND

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        reviewer_user = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
        if reviewer_user is None:
            return USER_NOT_FOUND

        if not reviewer_user.is_reviewer(event_id):
            _add_reviewer_role(reviewer_user.id, event_id)

        config = review_configuration_repository.get_configuration_for_event(event_id)

        response_ids = self.get_eligible_response_ids(event_id, reviewer_user.id, num_reviews,
                                                      config.num_reviews_required)
        response_reviewers = [ResponseReviewer(response_id, reviewer_user.id) for response_id in response_ids]
        db.session.add_all(response_reviewers)
        db.session.commit()

        if len(response_ids) > 0:
            email_user(
                'reviews-assigned',
                template_parameters=dict(
                    num_reviews=len(response_ids),
                    baobab_host=misc.get_baobab_host(),
                    system_name=g.organisation.system_name,
                    event_key=event.key
                ),
                event=event,
                user=reviewer_user)
        return {}, 201

    def add_reviewer_role(self, user_id, event_id):
        event_role = EventRole('reviewer', user_id, event_id)
        db.session.add(event_role)
        db.session.commit()

    def get_eligible_response_ids(self, event_id, reviewer_user_id, num_reviews, reviews_required):
        candidate_responses = review_repository.get_candidate_response_ids(event_id, reviewer_user_id, reviews_required)
        candidate_response_ids = set([r.id for r in candidate_responses])

        # Now remove any responses that the reviewer is already assigned to
        already_assigned = review_repository.get_already_assigned(reviewer_user_id)
        already_assigned_ids = set([r.response_id for r in already_assigned])
        responses = list(candidate_response_ids - already_assigned_ids)

        return random.sample(responses, min(len(responses), num_reviews))


_review_history_fields = {
    'response_id': fields.Integer,
    'review_response_id': fields.Integer,
    'submitted_timestamp': fields.DateTime(dt_format='iso8601'),
    'reviewed_user_id': fields.String
}

review_history_fields = {
    'reviews': fields.List(fields.Nested(_review_history_fields)),
    'num_entries': fields.Integer,
    'current_pagenumber': fields.Integer,
    'total_pages': fields.Integer
}


class ReviewHistoryModel:
    def __init__(self, review):
        self.response_id = review.Response.id
        self.review_response_id = review.id
        self.submitted_timestamp = review.submitted_timestamp
        self.reviewed_user_id = review.AppUser.id


class ReviewHistoryAPI(GetReviewHistoryMixin, restful.Resource):

    @auth_required
    @marshal_with(review_history_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        user_id = g.current_user['id']
        event_id = args['event_id']
        page_number = args['page_number']
        limit = args['limit']
        sort_column = args['sort_column']

        reviewer = user_repository.get_by_id(user_id).is_reviewer(event_id)
        if not reviewer:
            return FORBIDDEN

        reviews = review_repository.get_review_history(user_id, event_id)

        if sort_column == 'review_response_id':
            reviews = reviews.order_by(ReviewResponse.id)

        if sort_column == 'submitted_timestamp':
            reviews = reviews.order_by(ReviewResponse.submitted_timestamp)

        reviews = reviews.slice(page_number * limit, page_number * limit + limit).all()

        num_entries = review_repository.get_review_history_count(user_id, event_id)

        total_pages = ceil(float(num_entries) / limit)

        reviews = [ReviewHistoryModel(review) for review in reviews]
        return {'reviews': reviews, 'num_entries': num_entries, 'current_pagenumber': page_number,
                'total_pages': total_pages}


class ReviewListAPI(restful.Resource):

    @staticmethod
    def _serialize_answer(answer, language):
        translation = answer.question.get_translation(language)
        if not translation:
            translation = answer.question.get_translation('en')
            LOGGER.warn('Could not find {} translation for question id {}'.format(language, answer.question.id))
        return {
            'headline': translation.headline,
            'value': answer.value_display
        }

    @staticmethod
    def _serialize_response(response, review_response, language):
        info = [
            ReviewListAPI._serialize_answer(answer, language)
            for answer in response.answers if answer.question.key == 'review-identifier']

        submitted = None
        if review_response and review_response.submitted_timestamp:
            submitted = review_response.submitted_timestamp.isoformat()

        return {
            'response_id': response.id,
            'language': response.language,
            'information': info,
            'started': review_response is not None,
            'submitted': submitted,
            'total_score': review_response.calculate_score() if review_response is not None else 0.0
        }

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        parser.add_argument('language', type=str, required=True)
        args = parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']
        language = args['language']

        if not user_repository.get_by_id(user_id).is_reviewer(event_id):
            return FORBIDDEN

        responses_to_review = review_repository.get_review_list(user_id, event_id)

        return [ReviewListAPI._serialize_response(response, review_response, language)
                for response, review_response in responses_to_review]

class ResponseReviewAssignmentAPI(restful.Resource):
    @event_admin_required
    def post(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('response_ids', type=int, required=True, action='append')
        parser.add_argument('reviewer_email', type=str, required=True)
        args = parser.parse_args()

        response_ids = args['response_ids']
        reviewer_email = args['reviewer_email']

        filtered_response_ids = response_repository.filter_ids_to_event(response_ids, event_id)

        if set(filtered_response_ids) != set(response_ids):
            return FORBIDDEN

        event = event_repository.get_by_id(event_id)

        reviewer_user = user_repository.get_by_email(reviewer_email, g.organisation.id)
        if reviewer_user is None:
            return USER_NOT_FOUND

        if not reviewer_user.is_reviewer(event_id):
            _add_reviewer_role(reviewer_user.id, event_id)

        response_reviewers = [ResponseReviewer(response_id, reviewer_user.id) for response_id in response_ids]
        db.session.add_all(response_reviewers)
        db.session.commit()

        if len(response_ids) > 0:
            email_user(
                'reviews-assigned',
                template_parameters=dict(
                    num_reviews=len(response_ids),
                    baobab_host=misc.get_baobab_host(),
                    system_name=g.organisation.system_name,
                    event_key=event.key
                ),
                event=event,
                user=reviewer_user)
        return {}, 201

    @event_admin_required
    def delete(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('response_id', type=int, required=True)
        parser.add_argument('reviewer_user_id', type=int, required=True)
        args = parser.parse_args()

        response_id = args['response_id']
        reviewer_user_id = args['reviewer_user_id']

        review_form = review_repository.get_review_form(event_id)
        if not review_form:
            return REVIEW_FORM_NOT_FOUND

        # If the reviewer has already completed the review, action can't be completed
        review_response = review_repository.get_review_response(review_form.id, response_id, reviewer_user_id)
        if review_response:
            return REVIEW_ALREADY_COMPLETED

        review_repository.delete_response_reviewer(response_id, reviewer_user_id)

        return {}, 200

class ReviewResponseDetailListAPI(restful.Resource):
    @staticmethod
    def _serialise_identifier(answer, language):
        question_translation = answer.question.get_translation(language)
        if question_translation is None:
            question_translation = answer.question.get_translation('en')
            LOGGER.warn('Could not find {} translation for question id {}'.format(language, answer.question.id))

        return {
            'headline': question_translation.headline,
            'value': answer.value_display
        }

    @staticmethod
    def _serialise_score(review_score, language):
        review_question_translation = review_score.review_question.get_translation(language)
        if review_question_translation is None:
            review_question_translation = review_score.review_question.get_translation('en')
            LOGGER.warn('Could not find {} translation for review question id {}'.format(language,
                                                                                         review_score.review_question.id))

        return {
            'headline': review_question_translation.headline,
            'description': review_question_translation.description,
            'type': review_score.review_question.type,
            'score': review_score.value,
            'weight': review_score.review_question.weight,
        }

    @staticmethod
    def _serialise_review_response(review_response):
        return {
            'review_response_id': review_response.id,
            'response_id': review_response.response_id,

            'reviewer_user_title': review_response.reviewer_user.user_title,
            'reviewer_user_firstname': review_response.reviewer_user.firstname,
            'reviewer_user_lastname': review_response.reviewer_user.lastname,

            'response_user_title': review_response.response.user.user_title,
            'response_user_firstname': review_response.response.user.firstname,
            'response_user_lastname': review_response.response.user.lastname,

            'identifiers': [
                ReviewResponseDetailListAPI._serialise_identifier(answer, review_response.language)
                for answer in review_response.response.answers
                if answer.question.is_review_identifier()
            ],

            'scores': [
                ReviewResponseDetailListAPI._serialise_score(review_score, review_response.language)
                for review_score in review_response.review_scores
                if (review_score.review_question.type == 'multi-choice'
                    or review_score.review_question.type == 'long-text'
                    or review_score.review_question.type == 'short-text'
                    )
            ],

            'total': review_response.calculate_score()
        }

    @auth_required
    @event_admin_required
    def get(self, event_id):
        review_responses = review_repository.get_all_review_responses_by_event(event_id)
        return [
                   ReviewResponseDetailListAPI._serialise_review_response(review_response)
                   for review_response in review_responses
               ], 200
