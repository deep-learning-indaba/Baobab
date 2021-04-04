import datetime
import traceback
import itertools

import flask_restful as restful
from flask import g, request
from flask_restful import fields, marshal_with, reqparse, inputs
from sqlalchemy.exc import SQLAlchemyError

from app import LOGGER, bcrypt, db
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.applicationModel.models import ApplicationForm, Question
from app.events.models import Event, EventType
from app.events.repository import EventRepository as event_repository
from app.responses.mixins import ResponseMixin, ResponseTagMixin
from app.responses.models import Answer, Response, ResponseTag
from app.responses.repository import ResponseRepository as response_repository
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.utils import emailer, errors, strings
from app.utils.auth import auth_required, event_admin_required
from app.reviews.repository import ReviewRepository as review_repository
from app.reviews.repository import ReviewConfigurationRepository as review_configuration_repository


class ResponseAPI(ResponseMixin, restful.Resource):

    answer_fields = {
        'id': fields.Integer,
        'question_id': fields.Integer,
        'value': fields.String
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
        'answers': fields.List(fields.Nested(answer_fields)),
        'language': fields.String
    }

    @auth_required
    @marshal_with(response_fields)
    def get(self):
        args = self.get_req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        if not event.has_application_form():
            return errors.FORM_NOT_FOUND

        form = event.get_application_form()
        responses = response_repository.get_all_for_user_application(current_user_id, form.id)
        return responses

    @auth_required
    @marshal_with(response_fields)
    def post(self):
        args = self.post_req_parser.parse_args()
        user_id = g.current_user['id']
        is_submitted = args['is_submitted']
        application_form_id = args['application_form_id']
        language = args['language']
        if len(language) != 2:
            language = 'en'  # Fallback to English if language doesn't look like an ISO 639-1 code

        application_form = application_form_repository.get_by_id(application_form_id)
        if application_form is None:
            return errors.FORM_NOT_FOUND_BY_ID
        
        user = user_repository.get_by_id(user_id)
        responses = response_repository.get_all_for_user_application(user_id, application_form_id)

        if not application_form.nominations and len(responses) > 0:
            return errors.RESPONSE_ALREADY_SUBMITTED

        response = Response(application_form_id, user_id, language)
        if is_submitted:
            response.submit()
            
        response_repository.save(response)

        answers = []
        for answer_args in args['answers']:
            answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
            answers.append(answer)
        response_repository.save_answers(answers)

        try:
            if response.is_submitted:
                LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=response.id))
                user = user_repository.get_by_id(user_id)
                response = response_repository.get_by_id_and_user_id(response.id, user_id)
                self.send_confirmation(user, response)
        except:
            LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=response.id))
        finally:
            return response, 201

    @auth_required
    @marshal_with(response_fields)
    def put(self):
        args = self.put_req_parser.parse_args()
        user_id = g.current_user['id']
        is_submitted = args['is_submitted']
        language = args['language']

        response = response_repository.get_by_id(args['id'])
        if not response:
            return errors.RESPONSE_NOT_FOUND
        if response.user_id != user_id:
            return errors.UNAUTHORIZED
        if response.application_form_id != args['application_form_id']:
            return errors.UPDATE_CONFLICT

        response.is_submitted = is_submitted
        response.language = language
        if is_submitted:
            response.submit()
        response_repository.save(response)

        answers = []
        for answer_args in args['answers']:
            answer = response_repository.get_answer_by_question_id_and_response_id(answer_args['question_id'], response.id)
            if answer:
                answer.update(answer_args['value'])
            else:
                answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
            answers.append(answer)
        response_repository.save_answers(answers)

        try:
            if response.is_submitted:
                LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=response.id))
                user = user_repository.get_by_id(user_id)
                response = response_repository.get_by_id_and_user_id(response.id, user_id)
                self.send_confirmation(user, response)
        except:                
            LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=response.id))
        finally:
            return response, 200

    @auth_required
    def delete(self):
        args = self.del_req_parser.parse_args()
        current_user_id = g.current_user['id']

        response = response_repository.get_by_id(args['id'])
        if not response:
            return errors.RESPONSE_NOT_FOUND

        if response.user_id != current_user_id:
            return errors.UNAUTHORIZED

        response.withdraw()
        response_repository.save(response)      

        try:
            user = user_repository.get_by_id(current_user_id)
            event = response.application_form.event
            organisation = event.organisation

            emailer.email_user(
                'withdrawal',
                template_parameters=dict(
                    organisation_name=organisation.name
                ),
                event=event,
                user=user
            )

        except:                
            LOGGER.error('Failed to send withdrawal confirmation email for response with ID : {id}, but the response was withdrawn succesfully'.format(id=args['id']))

        return {}, 204

    def send_confirmation(self, user, response):
        try:
            answers = response.answers
            if not answers:
                LOGGER.warn('Found no answers associated with response with id {response_id}'.format(response_id=response.id))

            application_form = response.application_form
            if application_form is None:
                LOGGER.warn('Found no application form with id {form_id}'.format(form_id=response.application_form_id))

            event = application_form.event
            if event is None:
                LOGGER.warn('Found no event id {event_id}'.format(form_id=application_form.event_id))
        except:
            LOGGER.error('Could not connect to the database to retrieve response confirmation email data on response with ID : {response_id}'.format(response_id=response.id))

        try:
            question_answer_summary = strings.build_response_email_body(answers, user.user_primaryLanguage, application_form)

            if event.has_specific_translation(user.user_primaryLanguage):
                event_description = event.get_description(user.user_primaryLanguage)
            else:
                event_description = event.get_description('en')

            emailer.email_user(
                'confirmation-response-call' if event.event_type == EventType.CALL else 'confirmation-response',
                template_parameters=dict(
                    event_description=event_description,
                    question_answer_summary=question_answer_summary,
                ),
                event=event,
                user=user
            )

        except Exception as e:
            LOGGER.error('Could not send confirmation email for response with id : {response_id} due to: {e}'.format(response_id=response.id, e=e))


def _pad_list(lst, length):
    diff = length - len(lst)
    lst.extend([None] * diff)
    return lst

def _review_response_status(review_response):
    status = 'not_started'
    if review_response is not None:
        status = 'completed' if review_response.is_submitted else 'started'
    return status

def _serialize_reviewer(response_reviewer, review_response):
    
    return {
        'reviewer_id': response_reviewer.reviewer_user_id,
        'reviewer_name': '{} {} {}'.format(response_reviewer.user.user_title, response_reviewer.user.firstname, response_reviewer.user.lastname),
        'review_response_id': None if review_response is None else review_response.id,
        'status': _review_response_status(review_response)
    }

def _serialize_answer(answer, language):
    question = answer.question
    translation = question.get_translation(language)
    if translation is None:
        LOGGER.warn('No {} translation found for question id {}'.format(language, question.id))
        translation = question.get_translation('en')

    return {
        'question_id': answer.question_id,
        'value': answer.value,
        'type': answer.question.type,
        'options': translation.options,
        'headline': translation.headline
    }

def _serialize_tag(tag, language):
    tag_translation = tag.get_translation(language)
    if not tag_translation:
        LOGGER.warn('Could not find {} translation for tag id {}'.format(language, tag.id))
        tag_translation = tag.get_translation('en')
    return {
        'id': tag.id,
        'name': tag_translation.name
    }

class ResponseListAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('include_unsubmitted', type=inputs.boolean, required=True)
        # Note: Including [] in the question_ids parameter because that gets added by Axios on the front-end
        req_parser.add_argument('question_ids[]', type=int, required=False, action='append')
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()

        include_unsubmitted = args['include_unsubmitted']
        question_ids = args['question_ids[]']
        language = args['language']
        
        print(('Include unsubmitted:', include_unsubmitted))

        responses = response_repository.get_all_for_event(event_id, not include_unsubmitted)

        review_config = review_configuration_repository.get_configuration_for_event(event_id)
        required_reviewers = 1 if review_config is None else review_config.num_reviews_required + review_config.num_optional_reviews

        response_reviewers = review_repository.get_response_reviewers_for_event(event_id)
        response_to_reviewers = {
            k: list(g) for k, g in itertools.groupby(response_reviewers, lambda r: r.response_id)
        }

        review_responses = review_repository.get_review_responses_for_event(event_id)
        reviewer_to_review_response = {
            r.reviewer_user_id: r for r in review_responses
        }

        serialized_responses = []
        for response in responses:
            reviewers = [_serialize_reviewer(r, reviewer_to_review_response.get(r.reviewer_user_id, None)) 
                         for r in response_to_reviewers.get(response.id, [])]
            reviewers = _pad_list(reviewers, required_reviewers)
            if question_ids:
                answers = [_serialize_answer(answer, language) for answer in response.answers if answer.question_id in question_ids]
            else:
                answers = []

            serialized = {
                'response_id': response.id,
                'user_title': response.user.user_title,
                'firstname': response.user.firstname,
                'lastname': response.user.lastname,
                'start_date': response.started_timestamp.isoformat(),
                'is_submitted': response.is_submitted,
                'is_withdrawn': response.is_withdrawn,
                'submitted_date': None if response.submitted_timestamp is None else response.submitted_timestamp.isoformat(),
                'language': response.language,
                'answers': answers,
                'reviewers': reviewers,
                'tags': [_serialize_tag(rt.tag, language) for rt in response.response_tags]
            }

            serialized_responses.append(serialized)

        return serialized_responses


def _validate_user_admin_or_reviewer(user_id, event_id, response_id):
    user = user_repository.get_by_id(user_id)
    # Check if the user is an event admin
    permitted = user.is_event_admin(event_id)
    # If they're not an event admin, check if they're a reviewer for the relevant response
    if not permitted and user.is_reviewer(event_id):
        response_reviewer = review_repository.get_response_reviewer(response_id, user.id)
        if response_reviewer is not None:
            permitted = True
    
    return permitted

class ResponseTagAPI(restful.Resource, ResponseTagMixin):
    response_tag_fields = {
        'id': fields.Integer,
        'response_id': fields.Integer,
        'tag_id': fields.Integer
    }

    @marshal_with(response_tag_fields)
    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        event_id = args['event_id']
        tag_id = args['tag_id']
        response_id = args['response_id']

        if not _validate_user_admin_or_reviewer(g.current_user['id'], event_id, response_id):
            return errors.FORBIDDEN

        return response_repository.tag_response(response_id, tag_id), 201

    @auth_required
    def delete(self):
        args = self.req_parser.parse_args()

        event_id = args['event_id']
        tag_id = args['tag_id']
        response_id = args['response_id']

        if not _validate_user_admin_or_reviewer(g.current_user['id'], event_id, response_id):
            return errors.FORBIDDEN

        response_repository.remove_tag_from_response(response_id, tag_id)

        return {}



class ResponseDetailAPI(restful.Resource):

    @staticmethod
    def _serialize_date(date):
        if date is None:
            return None
        return date.isoformat()

    @staticmethod
    def _serialize_answer(answer):
        return {
            'id': answer.id,
            'question_id': answer.question_id,
            'value': answer.value
        }

    @staticmethod
    def _serialize_tag(tag, language):
        translation = tag.get_translation(language)
        if translation is None:
            LOGGER.warn('Could not find {} translation for tag id {}'.format(language, tag.id))
        return {
            'id': tag.id,
            'name': translation.name
        }

    @staticmethod
    def _serialize_reviewer(response_reviewer, review_form_id):
        if review_form_id is None:
            completed = False
        else:
            review_response = review_repository.get_review_response(review_form_id, response_reviewer.response_id, response_reviewer.reviewer_user_id)

        return {
            'reviewer_user_id': response_reviewer.user.id,
            'user_title': response_reviewer.user.user_title,
            'firstname': response_reviewer.user.firstname,
            'lastname': response_reviewer.user.lastname,
            'status': _review_response_status(review_response)
        }


    @staticmethod
    def _serialize_response(response, language, review_form_id, num_reviewers):
        return {
            'id': response.id,
            'application_form_id': response.application_form_id,
            'user_id': response.user_id,
            'is_submitted': response.is_submitted,
            'submitted_timestamp': ResponseDetailAPI._serialize_date(response.submitted_timestamp),
            'is_withdrawn': response.is_withdrawn,
            'withdrawn_timestamp': ResponseDetailAPI._serialize_date(response.withdrawn_timestamp),
            'started_timestamp': ResponseDetailAPI._serialize_date(response.started_timestamp),
            'answers': [ResponseDetailAPI._serialize_answer(answer) for answer in response.answers],
            'language': response.language,
            'user_title': response.user.user_title,
            'firstname': response.user.firstname,
            'lastname': response.user.lastname,
            'tags': [ResponseDetailAPI._serialize_tag(rt.tag, language) for rt in response.response_tags],
            'reviewers': [ResponseDetailAPI._serialize_reviewer(r, review_form_id) for r in response.reviewers]
        }

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('response_id', type=int, required=True) 
        req_parser.add_argument('language', type=str, required=True) 
        args = req_parser.parse_args()

        response_id = args['response_id']   
        language = args['language']

        response = response_repository.get_by_id(response_id)
        review_form = review_repository.get_review_form(event_id)
        review_form_id = None if review_form is None else review_form.id

        review_config = review_configuration_repository.get_configuration_for_event(event_id)
        num_reviewers = review_config.num_reviews_required + review_config.num_optional_reviews if review_config is not None else 1

        return ResponseDetailAPI._serialize_response(response, language, review_form_id, num_reviewers)
