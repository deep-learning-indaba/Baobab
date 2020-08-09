import datetime
import traceback

import flask_restful as restful
from flask import g, request
from flask_restful import fields, marshal_with, reqparse
from sqlalchemy.exc import SQLAlchemyError

from app import LOGGER, bcrypt, db
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.applicationModel.models import ApplicationForm, Question
from app.events.models import Event
from app.events.repository import EventRepository as event_repository
from app.responses.mixins import ResponseMixin
from app.responses.models import Answer, Response
from app.responses.repository import ResponseRepository as response_repository
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.utils import emailer, errors, strings
from app.utils.auth import auth_required


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
        'answers': fields.List(fields.Nested(answer_fields))
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

        application_form = application_form_repository.get_by_id(application_form_id)
        if application_form is None:
            return errors.FORM_NOT_FOUND_BY_ID
        
        user = user_repository.get_by_id(user_id)
        responses = response_repository.get_all_for_user_application(user_id, application_form_id)

        if not application_form.nominations and len(responses) > 0:
            return errors.RESPONSE_ALREADY_SUBMITTED

        response = Response(application_form_id, user_id)
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

        response = response_repository.get_by_id(args['id'])
        if not response:
            return errors.RESPONSE_NOT_FOUND
        if response.user_id != user_id:
            return errors.UNAUTHORIZED
        if response.application_form_id != args['application_form_id']:
            return errors.UPDATE_CONFLICT

        response.is_submitted = is_submitted
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
                dict(
                    title=user.user_title,
                    firstname=user.firstname,
                    lastname=user.lastname,
                    organisation_name=organisation.name,
                    event_name=event.name
                ),
                event_id=event.id,
                user=user,
                subject_parameters={'event_name': event.name}
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
            question_answer_summary = strings.build_response_email_body(answers)

            emailer.email_user(
                'confirmation-response',
                dict(
                    title=user.user_title,
                    firstname=user.firstname,
                    lastname=user.lastname,
                    event_description=event.description,
                    question_answer_summary=question_answer_summary,
                    event_name=event.name
                ),
                event_id=event.id,
                user=user,
                subject_parameters={'event_name': event.name}
            )

        except:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(response_id=response.id))
