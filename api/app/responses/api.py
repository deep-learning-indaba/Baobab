import io
import itertools
import json
import tempfile

import flask_restful as restful
from app import LOGGER
from typing import Optional, Sequence, Tuple, Mapping, Union
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.applicationModel.models import ApplicationForm, Question, Section
from app.events.models import EventType
from app.events.repository import EventRepository as event_repository
from app.responses.mixins import ResponseMixin, ResponseTagMixin
from app.responses.models import Answer, Response, ValidationError
from app.responses.repository import ResponseRepository as response_repository
from app.reviews.repository import ReviewConfigurationRepository as review_configuration_repository
from app.reviews.repository import ReviewRepository as review_repository
from app.outcome.models import Outcome
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.users.repository import UserRepository as user_repository
from app.utils import emailer, errors, strings, pdfconvertor, storage
from app.utils.zipping import zip_in_memory
from app.utils.auth import auth_required, event_admin_required
from flask import g, send_file
from flask_restful import fields, inputs, marshal, reqparse

def _extract_outcome_status(response):
    if not hasattr(response, "outcome") or not isinstance(response.outcome, Outcome):
        return None
    return response.outcome.status.name

def _extract_review_summary(response):
    if not hasattr(response, "review_summary") or not isinstance(response.outcome, Outcome):
        return None
    return response.outcome.review_summary


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
        'language': fields.String,
        'parent_id': fields.Integer(default=None),
        'outcome': fields.String(attribute=_extract_outcome_status),
        'review_summary': fields.String(attribute=_extract_review_summary)
    }

    def find_answer(self, question_id: int, answers: Sequence[Answer]) -> Optional[Answer]:
        answer = next((a for a in answers if a.question_id == question_id), None)
        return answer

    def is_entity_visible(self, entity: Union[Question, Section], answers: Sequence[Answer], language: str) -> bool:
        if not entity.depends_on_question_id:
            return True
        
        dependency_answer = self.find_answer(entity.depends_on_question_id, answers)
        if dependency_answer is None:
            return False
        
        translation = entity.get_translation(language)    
        if translation is None:
            LOGGER.warn('No {} translation found for {} id {}'.format(language, type(entity), entity.id))
            translation = entity.get_translation('en')
        
        return translation.show_for_values and dependency_answer.value in translation.show_for_values

    def validate_response(self, response: Response, application_form: ApplicationForm) -> Tuple[bool, Mapping[int, ValidationError]]:
        answers = response.answers
        errors = []

        for section in application_form.sections:
            if not self.is_entity_visible(section, answers, response.language):
                continue

            for question in section.questions:
                answer = self.find_answer(question.id, answers)

                visible = self.is_entity_visible(question, answers, response.language)
                if not visible:
                    continue

                if question.is_required and answer is None:
                    errors.append({
                        "question_id": question.id,
                        "error": ValidationError.REQUIRED
                    })
                    continue
                
                if answer is None:
                    continue

                is_valid, error = answer.is_valid(response.language)
                if not is_valid:
                    errors.append({
                        "question_id": question.id,
                        "error": error
                    })

        return not bool(errors), errors

    @auth_required
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

        for response in responses:
            outcome = outcome_repository.get_latest_by_user_for_event(current_user_id, event_id, response.id)
            response.outcome = outcome
            response.review_summary = outcome

        return marshal(responses, ResponseAPI.response_fields), 200

    @auth_required
    def post(self):
        args = self.post_req_parser.parse_args()
        user_id = g.current_user['id']
        is_submitted = args['is_submitted']
        application_form_id = args['application_form_id']
        language = args['language']
        parent_id = args.get('parent_id', None)


        if len(language) != 2:
            language = 'en'  # Fallback to English if language doesn't look like an ISO 639-1 code

        application_form = application_form_repository.get_by_id(application_form_id)

        if application_form is None:
            return errors.FORM_NOT_FOUND_BY_ID

        event = event_repository.get_event_by_application_form_id(application_form_id)

        allow_multiple_submissions = False
        if event and event.event_type == EventType.JOURNAL:
            allow_multiple_submissions = True

        if not allow_multiple_submissions:
            responses = response_repository.get_all_for_user_application(user_id, application_form_id)
            if len(responses) > 0:
                return errors.RESPONSE_ALREADY_SUBMITTED


        response = Response(application_form_id, user_id, language, parent_id)
        response_repository.save(response)

        answers = []
        for answer_args in args['answers']:
            answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
            answers.append(answer)
        response_repository.save_answers(answers)

        if is_submitted:
            is_valid, validation_errors = self.validate_response(response, application_form)
            if not is_valid:
                return validation_errors, 422
            
            response.submit()
            response_repository.save(response)

            try:
                LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=response.id))
                user = user_repository.get_by_id(user_id)
                response = response_repository.get_by_id_and_user_id(response.id, user_id)
                self.send_confirmation(user, response)
                
                event = event_repository.get_event_by_response_id(response.id)
                if event.event_type == EventType.JOURNAL:
                    event_admins = event_repository.get_event_admins(event_id=event.id)
                    for event_admin in event_admins:
                        self.send_confirmation(event_admin, response)
            except:
                LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=response.id))

        return marshal(response, ResponseAPI.response_fields), 201

    @auth_required
    def put(self):
        args = self.put_req_parser.parse_args()
        user_id = g.current_user['id']
        is_submitted = args['is_submitted']
        language = args['language']
        application_form_id = args['application_form_id']

        response = response_repository.get_by_id(args['id'])
        if not response:
            return errors.RESPONSE_NOT_FOUND
        if response.user_id != user_id:
            return errors.UNAUTHORIZED
        if response.application_form_id != application_form_id:
            return errors.UPDATE_CONFLICT
        
        application_form = application_form_repository.get_by_id(application_form_id)
        if application_form is None:
            return errors.FORM_NOT_FOUND_BY_ID

        answers = []
        for answer_args in args['answers']:
            existing_answers = response_repository.get_answer_by_question_id_and_response_id(answer_args['question_id'], response.id)
            for existing_answer in existing_answers:
                existing_answer.deactivate()
                response_repository.merge_answer(existing_answer)
            active_answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
            answers.append(active_answer)
        response_repository.save_answers(answers)

        response.language = language
        response_repository.save(response)

        if is_submitted:
            is_valid, validation_errors = self.validate_response(response, application_form)
            if not is_valid:
                return validation_errors, 422
            
            response.submit()
            response_repository.save(response)

            try:
                LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=response.id))
                user = user_repository.get_by_id(user_id)
                response = response_repository.get_by_id_and_user_id(response.id, user_id)
                self.send_confirmation(user, response)
                
                event = event_repository.get_event_by_response_id(response.id)
                if event.event_type == EventType.JOURNAL:
                    event_admins = event_repository.get_event_admins(event_id=event.id)
                    for event_admin in event_admins:
                        self.send_confirmation(event_admin, response)
            except:                
                LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=response.id))
            
        return marshal(response, ResponseAPI.response_fields), 200

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
            
            if (event.event_type==EventType.JOURNAL):
                submission_title= response_repository.get_answer_by_question_key_and_response_id('submission_title', response.id)
                if not submission_title:
                    raise errors.SUBMISSION_TITLE_NOT_FOUND

                emailer.email_user(
                    'submitting-article-journal',
                    template_parameters=dict(
                        event_description=event_description,
                        question_answer_summary=question_answer_summary,
                    ),
                     subject_parameters=dict(
                            submission_title=submission_title,
                        ),
                    event=event,
                    user=user
                )
                

            else:

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
                'user_id': response.user_id,
                'user_title': response.user.user_title,
                'firstname': response.user.firstname,
                'lastname': response.user.lastname,
                'email': response.user.email,
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

    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        event_id = args['event_id']
        tag_id = args['tag_id']
        response_id = args['response_id']

        if not _validate_user_admin_or_reviewer(g.current_user['id'], event_id, response_id):
            return errors.FORBIDDEN

        return marshal(response_repository.tag_response(response_id, tag_id), ResponseTagAPI.response_tag_fields), 201

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
            translation = tag.get_translation('en')
        return {
            'id': tag.id,
            'event_id': tag.event_id,
            'tag_type': tag.tag_type.value.upper(),
            'name': translation.name,
            'description': translation.description
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

class ResponseExportAPI(restful.Resource):

    def get(self):

        def _get_answer(question_id, answers):
            # Get the answer for a question
            for a in answers:
                if a.question_id == question_id:
                    return a

            return None

        def _get_files(application_form, answers): 
            # Get the response files that should be exported in the ZIP file

            file_names = []

            for section in application_form.sections:
                for question in section.questions:
                    answer = _get_answer(question.id, answers)                
                    if answer is not None:
                        # We are only interested in the files, 
                        # the text answers will be in the main PDF file
                        if question.type == 'multi-file':
                            file_names.extend(json.loads(answer.value))
                        if question.type == 'file':
                            file_names.append(json.loads(answer.value))

            return file_names

        req_parser = reqparse.RequestParser()
        req_parser.add_argument('response_id', type=int, required=True) 
        req_parser.add_argument('language', type=str, required=True) 
        args = req_parser.parse_args()

        response_id = args['response_id']   
        language = args['language']

        response = response_repository.get_by_id(response_id) 
        application_form = application_form_repository.get_by_id(response_id) 

        # Build the HTML string
        response_string = strings.build_response_html_app_info(response, language) + \
        strings.build_response_html_answers(response.answers, language, application_form)

        # Convert to PDF
        files_to_compress = [(
            'response.pdf', 
            pdfconvertor.html_to_pdf(response.id, response_string)
        )]

        # The files that were uploaded as part of the response
        files_to_get = _get_files(application_form, response.answers)
        bucket = storage.get_storage_bucket()

        # Download and name the files
        files_to_compress.extend([(
            f['rename'] or f['filename'],
            io.BytesIO(bucket.blob(f['filename']).download_as_bytes())
        ) for f in files_to_get])

        # Zip files
        zipped_files = zip_in_memory(files_to_compress)

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(zipped_files.getvalue())
            return send_file(
                temp.name, 
                as_attachment=True, 
                attachment_filename=f"response_{response.id}.zip"
            )
    

