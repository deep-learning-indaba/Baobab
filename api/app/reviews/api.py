from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with, marshal
from math import ceil
import random

from typing import Any, Mapping, Optional, Sequence, Union
from datetime import datetime

from app import db, LOGGER
from app.applicationModel.models import Question, Section
from app.events.models import EventRole
from app.events.repository import EventRepository as event_repository
from app.responses.repository import ResponseRepository as response_repository
from app.responses.models import Response, ResponseReviewer, Answer
from app.reviews.mixins import ReviewMixin, GetReviewResponseMixin, PostReviewResponseMixin, PostReviewAssignmentMixin, \
    GetReviewAssignmentMixin, GetReviewHistoryMixin
from app.reviews.models import ReviewForm, ReviewResponse, ReviewScore, ReviewQuestion, ReviewSection, ReviewSectionTranslation, ReviewQuestionTranslation, ReviewerTag, ReviewConfiguration
from app.reviews.repository import ReviewRepository as review_repository
from app.reviews.repository import ReviewConfigurationRepository as review_configuration_repository
from app.reviews.repository import ReviewerTagRepository as reviewer_tag_repository
from app.references.repository import ReferenceRequestRepository as reference_repository
from app.tags.repository import TagRepository as tag_repository
from app.users.repository import UserRepository as user_repository

from app.events.repository import EventRepository as event_repository
from app.utils.auth import auth_required
from app.utils.language import translatable

from app.utils.auth import auth_required, event_admin_required
from app.utils.errors import EVENT_NOT_FOUND, REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND, RESPONSE_NOT_FOUND, \
    REVIEW_FORM_NOT_FOUND, REVIEW_ALREADY_COMPLETED, NO_ACTIVE_REVIEW_FORM, REVIEW_FORM_FOR_STAGE_NOT_FOUND, REVIEW_FORM_EXISTS, UPDATE_CONFLICT, QUESTION_NOT_FOUND, SECTION_NOT_FOUND, TAG_NOT_FOUND

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
    'language': fields.String,
    'is_submitted': fields.Boolean,
    'submitted_timestamp': fields.DateTime(dt_format='iso8601')
}

extended_scores_fields = {
    'review_question_id': fields.Integer,
    'type': fields.String,
    'value': fields.String
}

extended_review_fields = {
    'review_response_id': fields.Integer,
    'response_id': fields.Integer,
    'reviewer_user_title': fields.String,
    'reviewer_user_firstname': fields.String,
    'reviewer_user_lastname': fields.String,
    'scores': fields.List(fields.Nested(extended_scores_fields), attribute='scores'),
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

reviewer_user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String,
}

review_question_detail_fields = {
    'id': fields.Integer,
    'question_id': fields.Integer,
    'type': fields.String,
    'is_required': fields.Boolean,
    'order': fields.Integer,
    'weight': fields.Float,
    'headline': fields.Raw(attribute=lambda s: s.headline_translations),
    'description': fields.Raw(attribute=lambda s: s.description_translations),
    'placeholder': fields.Raw(attribute=lambda s: s.placeholder_translations),
    'options': fields.Raw(attribute=lambda s: s.options_translations),
    'validation_regex': fields.Raw(attribute=lambda s: s.validation_regex_translations),
    'validation_text': fields.Raw(attribute=lambda s: s.validation_text_translations)
}

review_section_detail_fields = {
    'id': fields.Integer,
    'order': fields.Integer,
    'name': fields.Raw(attribute=lambda s: s.headline_translations),
    'description': fields.Raw(attribute=lambda s: s.description_translations),
    'questions': fields.List(fields.Nested(review_question_detail_fields), attribute='review_questions')
}

review_form_detail_fields = {
    'id': fields.Integer,
    'event_id': fields.Integer,
    'application_form_id': fields.Integer,
    'is_open':  fields.Boolean,
    'deadline': fields.DateTime(dt_format='iso8601'),
    'active': fields.Boolean,
    'stage': fields.Integer,
    'sections': fields.List(fields.Nested(review_section_detail_fields), attribute='review_sections')
}

response_review_fields = {
    'review_form': fields.Raw,
    'review_responses': fields.List(fields.Nested(extended_review_fields)),
}


def _serialize_review_question(review_question, language):
    translation = review_question.get_translation(language)
    if translation is None:
        LOGGER.warn('Missing {} translation for review review_question id {}'.format(language, review_question.id))
        translation = review_question.get_translation('en')
    return {
        'id': review_question.id,
        'question_id': review_question.question_id,
        'description': translation.description,
        'headline': translation.headline,
        'type': review_question.type,
        'placeholder': translation.placeholder,
        'options': translation.options,
        'is_required': review_question.is_required,
        'order': review_question.order,
        'validation_regex': translation.validation_regex,
        'validation_text': translation.validation_text,
        'weight': review_question.weight
    }

def _serialize_review_form(review_form: ReviewForm, language: str) -> Mapping[str, Any]:
    review_sections = []

    for section in review_form.review_sections:
        translation = section.get_translation(language)
        if translation is None:
            LOGGER.warn('Missing {} translation for review section id {}'.format(language, section.id))
            translation = section.get_translation('en')
        review_sections.append({
            'id': section.id,
            'order': section.order,
            'headline': translation.headline,
            'description': translation.description,
            'review_questions': [_serialize_review_question(q, language) for q in section.review_questions]
        })

    form = {
        'id': review_form.id,
        'application_form_id': review_form.application_form_id,
        'is_open': review_form.is_open,
        'deadline': review_form.deadline.isoformat(),
        'stage': review_form.stage,
        'review_sections': review_sections
    }

    return form


def _add_reviewer_role(user_id, event_id):
    event_role = EventRole('reviewer', user_id, event_id)
    db.session.add(event_role)
    db.session.commit()

def _is_visible(answer: Answer, answers: Sequence[Answer], language: str) -> bool:
    section = answer.question.section
    if not _is_entity_visible(section, answers, language):
        return False
    
    return _is_entity_visible(answer.question, answers, language)


def _find_answer(question_id: int, answers: Sequence[Answer]) -> Optional[Answer]:
    answer = next((a for a in answers if a.question_id == question_id), None)
    return answer


def _is_entity_visible(entity: Union[Question, Section], answers: Sequence[Answer], language: str) -> bool:
    if not entity.depends_on_question_id:
        return True
    
    dependency_answer = _find_answer(entity.depends_on_question_id, answers)
    if dependency_answer is None:
        return False
    
    translation = entity.get_translation(language)    
    if translation is None:
        LOGGER.warn('No {} translation found for {} id {}'.format(language, type(entity), entity.id))
        translation = entity.get_translation('en')
    
    return translation.show_for_values and dependency_answer.value in translation.show_for_values


class ResponseModel:
    def __init__(self, response: Response, answers: Sequence[Answer]=None):
        self.id = response.id
        self.application_form_id = response.application_form_id
        self.user_id = response.user_id
        self.is_submitted = response.is_submitted
        self.submitted_timestamp = response.submitted_timestamp
        self.is_withdrawn = response.is_withdrawn
        self.withdrawn_timestamp = response.withdrawn_timestamp
        self.started_timestamp = response.started_timestamp
        self.language = response.language
        self.answers = answers or response.answers
        self.user = response.user
    

def _filter_response(response: Response) -> ResponseModel:
    if response is None:
        return None

    new_answers = [answer for answer in response.answers if _is_visible(answer, response.answers, response.language)]
    return ResponseModel(response, new_answers)


class ReviewResponseUser():
    def __init__(self, review_form, response, reviews_remaining_count, language, reference_responses=None,
                 review_response=None, reviewer=None):
        self.review_form = _serialize_review_form(review_form, language)
        self.response = response
        self.user = None if response is None else response.user
        self.reviews_remaining_count = reviews_remaining_count
        self.references = reference_responses
        self.review_response = review_response
        self.reviewer = reviewer

class ReviewResponses():
    def __init__(self, review_form, review_responses, language):
        self.review_form = _serialize_review_form(review_form, language)
        self.review_responses = review_responses


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
        response = _filter_response(response)

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
            review_response=review_response,
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
        response = _filter_response(response)

        if response is None:
            return RESPONSE_NOT_FOUND

        review_response = review_repository.get_review_response(review_form.id, response_id, g.current_user['id'])

        return ReviewResponseUser(review_form, response, 0, args['language'], review_response=review_response)

class ResponseReviewEventAdminAPI(restful.Resource):
    @event_admin_required
    def get(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('response_id', type=int, required=True)
        parser.add_argument('language', type=str, required=True)
        args = parser.parse_args()

        response_id = args['response_id']

        review_form = review_repository.get_review_form(event_id)
        if review_form is None:
            return REVIEW_FORM_NOT_FOUND

        response_reviews = (review_repository.get_all_review_responses_by_response(review_form.id, response_id))
        serialized_reviews =  [
            ReviewResponseDetailListAPI._serialise_review_response(response, args['language'])
            for response in response_reviews
        ]
        return marshal(ReviewResponses(review_form, serialized_reviews, args['language']), response_review_fields), 200



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

        review_repository.deactivate_review(review_response)
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
    def __init__(self, count, reviewer_tags: Sequence[ReviewerTag], language: str):
        self.email = count.email
        self.user_title = count.user_title
        self.firstname = count.firstname
        self.lastname = count.lastname
        self.reviews_allocated = count.reviews_allocated
        self.reviews_completed = count.reviews_completed
        self.reviewer_user_id = count.reviewer_user_id
        self.tags = [_serialize_tag(rt.tag, language) for rt in reviewer_tags]

class ReviewSummaryAPI(restful.Resource):

    @auth_required
    @event_admin_required
    def get(self, event_id):
        get_req_parser = reqparse.RequestParser()
        get_req_parser.add_argument('tags[]', type=int, action="append")
        args = get_req_parser.parse_args()
        tags = args['tags[]']

        config = review_configuration_repository.get_configuration_for_event(event_id)
        num_reviews_required = config.num_reviews_required if config is not None else 1

        return {
            'reviews_unallocated': review_repository.count_unassigned_reviews(event_id, num_reviews_required, tag_ids=tags)
        }


def _serialize_tag(tag, language):
    translation = tag.get_translation(language)
    if translation is None:
        LOGGER.warn('Could not find {} translation for tag id {}'.format(language, tag.id))
        translation = tag.get_translation('en')
    return {
        'id': tag.id,
        'event_id': tag.event_id,
        'tag_type': tag.tag_type.value.upper(),
        'name': translation.name,
        'description': translation.description
    }

class ReviewAssignmentAPI(GetReviewAssignmentMixin, PostReviewAssignmentMixin, restful.Resource):
    reviews_count_fields = {
        'reviewer_user_id': fields.Integer,
        'email': fields.String,
        'user_title': fields.String,
        'firstname': fields.String,
        'lastname': fields.String,
        'reviews_allocated': fields.Integer,
        'reviews_completed': fields.Integer,
        'tags': fields.Raw
    }

    @auth_required
    @marshal_with(reviews_count_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']
        language = args['language']

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        counts = review_repository.count_reviews_allocated_and_completed_per_reviewer(event_id)
        reviewer_tags = reviewer_tag_repository.reviewer_tags_for_event(event_id)

        def _filter_reviewer_tags(reviewer_user_id):
            return [rt for rt in reviewer_tags if rt.reviewer_user_id == reviewer_user_id]

        views = [ReviewCountView(count, _filter_reviewer_tags(count.reviewer_user_id), language) for count in counts]
        return views

    @event_admin_required
    def post(self, event_id):
        args = self.post_req_parser.parse_args()
        reviewer_user_email = args['reviewer_user_email']
        num_reviews = args['num_reviews']
        tags = args['tags'] or []

        event = event_repository.get_by_id(event_id)
        if not event:
            return EVENT_NOT_FOUND

        reviewer_user = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
        if reviewer_user is None:
            return USER_NOT_FOUND

        if not reviewer_user.is_reviewer(event_id):
            _add_reviewer_role(reviewer_user.id, event_id)

        config = review_configuration_repository.get_configuration_for_event(event_id)
        num_reviews_required = config.num_reviews_required if config is not None else 1

        # If the reviewer has any additional tags, then include those as well
        reviewer_tags = reviewer_tag_repository.reviewer_tags_for_reviewer(user_id=reviewer_user.id, event_id=event_id)
        reviewer_tag_ids = [rt.tag_id for rt in reviewer_tags]

        filter_tags = set(tags) | set(reviewer_tag_ids)
        response_ids = self.get_eligible_response_ids(event_id, reviewer_user.id, num_reviews,
                                                      num_reviews_required, filter_tags)
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
        return {'reviews_assigned': len(response_ids)}, 201

    @event_admin_required
    def delete(self, event_id):
        args = self.post_req_parser.parse_args()
        reviewer_user_email = args['reviewer_user_email']
        num_reviews = args['num_reviews']
        tags = args['tags'] or []

        event = event_repository.get_by_id(event_id)
        if not event:
            return EVENT_NOT_FOUND

        reviewer_user = user_repository.get_by_email(reviewer_user_email, g.organisation.id)
        if reviewer_user is None:
            return USER_NOT_FOUND
        
        # Get all reviews that have been assigned to the reviewer and match the tags

        review_list = review_repository.get_review_list(reviewer_user.id, event_id)
        LOGGER.info(f"len(Review list): {len(review_list)}")

        not_started = [response_reviewer for response, response_reviewer, review_response in review_list
                       if review_response is None
                       and self._tags_match(response, tags)]

        LOGGER.info(f"len(Not started): {len(not_started)}")

        counter = 0
        for response_reviewer in not_started:
            db.session.delete(response_reviewer)
            counter += 1
            if counter >= num_reviews:
                break

        db.session.commit()
        return {'num_deleted': counter}, 200

    def _tags_match(self, response, tags):
        LOGGER.info(f"Tags: {tags}")
        response_tag_ids = [rt.tag_id for rt in response.response_tags]
        LOGGER.info(f"Response tag ids: {response_tag_ids}")
        return all(t in response_tag_ids for t in tags)

    def add_reviewer_role(self, user_id, event_id):
        event_role = EventRole('reviewer', user_id, event_id)
        db.session.add(event_role)
        db.session.commit()

    def get_eligible_response_ids(self, event_id, reviewer_user_id, num_reviews, reviews_required, tags):
        candidate_responses = review_repository.get_candidate_responses(event_id, reviewer_user_id, reviews_required)
        # Filter by tags
        if tags:
            filtered_candidates_responses = []
            for response in candidate_responses:
                response_tag_ids = [rt.tag_id for rt in response.response_tags]
                if all(t in response_tag_ids for t in tags):
                    filtered_candidates_responses.append(response)
        else:
            filtered_candidates_responses = candidate_responses

        candidate_response_ids = set([r.id for r in filtered_candidates_responses])

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
                for response, _, review_response in responses_to_review]

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
            'review_question_id': review_score.review_question.id,
            'headline': review_question_translation.headline,
            'description': review_question_translation.description,
            'type': review_score.review_question.type,
            'value': review_score.value,
            'weight': review_score.review_question.weight,
        }

    @staticmethod
    def _serialise_review_response(review_response, language):
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
                ReviewResponseDetailListAPI._serialise_identifier(answer, language)
                for answer in review_response.response.answers
                if answer.question.is_review_identifier()
            ],

            'scores': [
                ReviewResponseDetailListAPI._serialise_score(review_score, language)
                for review_score in review_response.review_scores
                if (review_score.review_question.type == 'multi-choice'
                    or review_score.review_question.type == 'long-text'
                    or review_score.review_question.type == 'short-text'
                    or review_score.review_question.type == 'radio'
                    )
            ],

            'total': review_response.calculate_score()
        }

    @auth_required
    @event_admin_required
    def get(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('language', type=str, required=True)
        args = parser.parse_args()

        review_responses = review_repository.get_all_review_responses_by_event(event_id)
        return [
            ReviewResponseDetailListAPI._serialise_review_response(review_response, args['language'])
            for review_response in review_responses
        ], 200

class ReviewResponseSummaryListAPI(restful.Resource):
    @staticmethod
    def _serialise_response(response: Response, review_form: ReviewForm, language: str):
        scores = []
        for review_section in review_form.review_sections:
            for review_question in review_section.review_questions:
                if review_question.weight > 0:
                    review_question_translation = review_question.get_translation(language)
                    if not review_question_translation:
                        review_question_translation = review_question.get_translation('en')
                        LOGGER.warn('Could not find {} translation for review question id {}'.format(language, review_question.id))

                    average_score = review_repository.get_average_score_for_review_question(response.id, review_question.id)

                    score = {
                        "review_question_id": review_question.id,
                        "headline": review_question_translation.headline,
                        "description": review_question_translation.description,
                        "type": review_question.type,
                        "score": average_score,
                        "weight": review_question.weight
                    }
                    scores.append(score)

        response_summary = {
            "response_id": response.id,
            "response_user_title": response.user.user_title,
            "response_user_firstname": response.user.firstname,
            "response_user_lastname": response.user.lastname,

            "identifiers": [
                ReviewResponseDetailListAPI._serialise_identifier(answer, response.language)
                for answer in response.answers
                if answer.question.is_review_identifier()
            ],

            "scores": scores,
            "total": sum(score['score'] * score['weight'] for score in scores)
        }
        return response_summary

    @auth_required
    @event_admin_required
    def get(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('language', type=str, required=True)
        args = parser.parse_args()

        responses = response_repository.get_all_for_event(event_id)
        review_form = review_repository.get_review_form(event_id)

        return [
            ReviewResponseSummaryListAPI._serialise_response(response, review_form, args['language'])
            for response in responses
        ], 200


class ReviewStageAPI(restful.Resource):

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()

        event_id = args['event_id']

        review_forms = review_repository.get_all_review_forms_for_event(event_id)
        current_form = [r for r in review_forms if r.active]

        if not current_form:
            return NO_ACTIVE_REVIEW_FORM
        
        current_form = current_form[0]    

        return {
            'current_stage': current_form.stage,
            'total_stages': len(review_forms)
        }

    @auth_required
    @event_admin_required
    def post(self, event_id):
        parser = reqparse.RequestParser()
        parser.add_argument('stage', type=int, required=True)
        args = parser.parse_args()

        stage = args['stage']

        review_forms = review_repository.get_all_review_forms_for_event(event_id)
        selected_form = [r for r in review_forms if r.stage == stage]

        if not selected_form:
            return REVIEW_FORM_FOR_STAGE_NOT_FOUND

        selected_form = selected_form[0]

        for form in review_forms:
            form.deactivate()
        
        selected_form.activate()

        db.session.commit()
        
        return {}, 201


class ReviewFormDetailAPI(restful.Resource):

    @event_admin_required
    @marshal_with(review_form_detail_fields)
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('stage', type=int, required=False)
        args = req_parser.parse_args()

        stage = args['stage']

        review_form = review_repository.get_review_form(event_id, stage=stage)

        if not review_form:
            return REVIEW_FORM_FOR_STAGE_NOT_FOUND

        review_form.event_id = event_id

        return review_form

    @event_admin_required
    @marshal_with(review_form_detail_fields)
    def post(self, event_id):
        dt_format = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('stage', type=int, required=True)
        req_parser.add_argument('is_open', type=bool, required=True)
        req_parser.add_argument('deadline', type=dt_format, required=True)
        req_parser.add_argument('active', type=bool, required=True)
        req_parser.add_argument('sections', type=dict, required=True, action='append')
        req_parser.add_argument('num_reviews', type=int, required=True)
        args = req_parser.parse_args()

        application_form_id = args['application_form_id']
        stage = args['stage']
        is_open = args['is_open']
        deadline = args['deadline']
        active = args['active']
        sections_data = args['sections']
        num_reviews = args['num_reviews']

        review_form = review_repository.get_review_form(event_id, stage)
        if review_form is not None:
            return REVIEW_FORM_EXISTS

        other_review_forms = review_repository.get_review_forms(event_id)

        review_form = ReviewForm(
            application_form_id, 
            deadline, 
            stage, 
            # Only make this stage active if there is no other active stage.
            active=not any(o.active for o in other_review_forms))
        
        review_config = ReviewConfiguration(num_reviews_required=num_reviews, 
                                            num_optional_reviews=0)
        review_form.review_configuration = review_config
        review_repository.add_model(review_form)

        for section_data in sections_data:
            section = ReviewSection(review_form.id, section_data['order'])
            review_repository.add_model(section)

            languages = section_data['name'].keys()
            for language in languages:
                section_translation = ReviewSectionTranslation(
                    review_section_id=section.id,
                    language=language,
                    headline=section_data['name'][language],
                    description=section_data['description'][language])
                review_repository.add_model(section_translation)

            for question_data in section_data['questions']:
                question = ReviewQuestion(
                    review_section_id=section.id, 
                    question_id=question_data['question_id'] or None,
                    type=question_data['type'],
                    is_required=question_data['is_required'],
                    order=question_data['order'],
                    weight=question_data['weight'])
                
                review_repository.add_model(question)

                languages = question_data['headline'].keys()
                for language in languages:
                    question_translation = ReviewQuestionTranslation(
                        review_question_id=question.id,
                        language=language, 
                        description=question_data["description"][language], 
                        headline=question_data["headline"][language], 
                        placeholder=question_data["placeholder"][language], 
                        options=question_data["options"][language], 
                        validation_regex=question_data["validation_regex"][language], 
                        validation_text=question_data["validation_text"][language])

                    review_repository.add_model(question_translation)

        new_review_form = review_repository.get_review_form_by_id(review_form.id)
        new_review_form.event_id = event_id

        return new_review_form, 201

    @event_admin_required
    @marshal_with(review_form_detail_fields)
    def put(self, event_id):
        dt_format = lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('stage', type=int, required=True)
        req_parser.add_argument('is_open', type=bool, required=True)
        req_parser.add_argument('deadline', type=dt_format, required=True)
        req_parser.add_argument('sections', type=dict, required=True, action='append')
        req_parser.add_argument('num_reviews', type=int, required=True)
        args = req_parser.parse_args()

        id = args['id']
        application_form_id = args['application_form_id']
        stage = args['stage']
        is_open = args['is_open']
        deadline = args['deadline']
        sections_data = args['sections']
        num_reviews = args['num_reviews']

        review_form = review_repository.get_review_form_by_id(id)
        if not review_form:
            return REVIEW_FORM_NOT_FOUND
        
        if application_form_id != review_form.application_form_id:
            return UPDATE_CONFLICT

        if event_id != review_form.application_form.event_id:
            return UPDATE_CONFLICT
        
        review_form.stage = stage
        review_form.is_open = is_open
        review_form.deadline = deadline
        if review_form.review_configuration:
            review_form.review_configuration.num_reviews_required = num_reviews
        else:
            review_form.review_configuration = ReviewConfiguration(num_reviews_required=num_reviews, num_optional_reviews=0)
        
        # Note: we don't update the active property which is controlled by
        # the ReviewStageAPI

        # Delete questions in the review form that no longer exist
        all_question_ids = [q["id"] for s in sections_data for q in s["questions"] if "id" in q]
        for section in review_form.review_sections:
            for question in section.review_questions:
                if question.id not in all_question_ids:
                    review_repository.delete_review_question(question)
        
        all_section_ids = [s["id"] for s in sections_data if "id" in s]
        for section in review_form.review_sections:
            if section.id not in all_section_ids:
                review_repository.delete_review_section(section)

        for section_data in sections_data:
            if 'id' in section_data:
                # If ID is populated, then update the existing section
                section = next((s for s in review_form.review_sections if s.id == section_data['id']), None)  # type: ReviewSection
                if not section:
                    return SECTION_NOT_FOUND

                current_translations = section.translations  # type: Sequence[ReviewSectionTranslation]
                for current_translation in current_translations:
                    current_translation.description = section_data['description'][current_translation.language]
                    current_translation.headline = section_data['name'][current_translation.language]
                
                section.order = section_data["order"]
            else:
                # if not populated, then add new section
                section = ReviewSection(review_form.id, section_data["order"])
                review_repository.add_model(section)

                languages = section_data['name'].keys()
                for language in languages:
                    section_translation = ReviewSectionTranslation(
                        section.id, 
                        language, 
                        section_data['name'][language], 
                        section_data['description'][language])
                    review_repository.add_model(section_translation)

            for question_data in section_data["questions"]:
                if "id" in question_data:
                    current_question = next((q for q in section.review_questions if q.id == question_data['id']), None)  # type: ReviewQuestion
                    if not current_question:
                        return QUESTION_NOT_FOUND

                    current_question.question_id = question_data["question_id"] or None
                    current_question.type = question_data["type"]
                    current_question.order = question_data["order"]
                    current_question.is_required = question_data["is_required"]
                    current_question.weight = question_data["weight"]

                    current_translations = current_question.translations  # type: Sequence[ReviewQuestionTranslation]
                    for current_translation in current_translations:
                        current_translation.description = question_data['description'][current_translation.language]
                        current_translation.headline = question_data['headline'][current_translation.language]
                        current_translation.options = question_data['options'][current_translation.language]
                        current_translation.placeholder = question_data['placeholder'][current_translation.language]
                        current_translation.validation_regex = question_data['validation_regex'][current_translation.language]
                        current_translation.validation_text = question_data['validation_text'][current_translation.language]
                else:
                    question = ReviewQuestion(
                        review_section_id=section.id, 
                        question_id=question_data["question_id"] or None,
                        type=question_data["type"],
                        is_required=question_data["is_required"],
                        order=question_data["order"],
                        weight=question_data["weight"])

                    review_repository.add_model(question)

                    for language in question_data['headline'].keys():
                        translation = ReviewQuestionTranslation(
                            review_question_id=question.id,
                            language=language,
                            description=question_data["description"][language],
                            headline=question_data["headline"][language],
                            placeholder=question_data["placeholder"][language],
                            options=question_data["options"][language],
                            validation_regex=question_data["validation_regex"][language],
                            validation_text=question_data["validation_text"][language])

                        review_repository.add_model(translation)


            db.session.commit()

        review_form = review_repository.get_review_form_by_id(id)
        review_form.event_id = event_id

        return review_form, 200

class ReviewerTagAPI(restful.Resource):

    @event_admin_required
    @translatable
    def post(self, event_id: int, language: str):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('reviewer_user_id', type=int, required=True)
        req_parser.add_argument('tag_id', type=int, required=True)
        args = req_parser.parse_args()

        reviewer_user_id = args['reviewer_user_id']
        reviewer_user = user_repository.get_by_id(reviewer_user_id)
        if not reviewer_user:
            return USER_NOT_FOUND
        if not reviewer_user.is_reviewer(event_id):
            return FORBIDDEN
        
        tag_id = args['tag_id']
        tag = tag_repository.get_by_id(tag_id)
        if not tag:
            return TAG_NOT_FOUND
        if tag.event_id != event_id:
            return FORBIDDEN

        reviewer_tag = ReviewerTag(reviewer_user_id=reviewer_user_id, tag_id=tag_id, event_id=event_id)
        reviewer_tag_repository.add_reviewer_tag(reviewer_tag)
        tag_translation = reviewer_tag.tag.get_translation(language)

        return {
            'id': reviewer_tag.id,
            'reviewer_user_id': reviewer_tag.reviewer_user_id,
            'tag_id': reviewer_tag.tag_id,
            'event_id': reviewer_tag.event_id,
            'name': tag_translation.name,
            'description': tag_translation.description
        }, 201
    
    @event_admin_required
    def delete(self, event_id: int):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('reviewer_user_id', type=int, required=True)
        req_parser.add_argument('tag_id', type=int, required=True)
        args = req_parser.parse_args()

        reviewer_user_id = args['reviewer_user_id']
        tag_id = args['tag_id']
        reviewer_tag = reviewer_tag_repository.get_reviewer_tag(reviewer_user_id, tag_id, event_id)
        if not reviewer_tag:
            return FORBIDDEN
        
        reviewer_tag_repository.delete_reviewer_tag(reviewer_tag)
        return {}, 200
