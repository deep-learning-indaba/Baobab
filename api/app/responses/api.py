import datetime
import traceback

from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from flask import g, request

from sqlalchemy.exc import SQLAlchemyError

from app.applicationModel.mixins import ApplicationFormMixin
from app.responses.models import Response, Answer
from app.applicationModel.models import ApplicationForm, Question
from app.email_template.repository import EmailRepository as email_repository
from app.events.models import Event
from app.users.models import AppUser
from app.utils.auth import auth_required
from app.utils import errors, emailer, strings
from app import LOGGER

from app import db, bcrypt


class ResponseAPI(ApplicationFormMixin, restful.Resource):

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
        args = self.req_parser.parse_args()

        try:
            event = db.session.query(Event).filter(Event.id == args['event_id']).first()
            if not event:
                LOGGER.warn("Event not found for event_id: {}".format(args['event_id']))
                return errors.EVENT_NOT_FOUND

            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
            if not form:
                LOGGER.warn("Form not found for event_id: {}".format(args['event_id']))
                return errors.FORM_NOT_FOUND
            
            # Get the latest response (note there may be older withdrawn responses)
            response = db.session.query(Response).filter(
                Response.application_form_id == form.id, Response.user_id == g.current_user['id']
                ).order_by(Response.started_timestamp.desc()).first()
            if not response:
                LOGGER.debug("Response not found for event_id: {}".format(args['event_id']))
                return errors.RESPONSE_NOT_FOUND
            
            answers = db.session.query(Answer).filter(Answer.response_id == response.id).all()
            response.answers = list(answers)

            return response

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    @marshal_with(response_fields)
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('is_submitted', type=bool, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        try: 
            response = Response(args['application_form_id'], user_id)
            response.is_submitted = args['is_submitted']
            if args['is_submitted']:
                response.submitted_timestamp = datetime.datetime.now()
            db.session.add(response)
            db.session.commit()

            for answer_args in args['answers']:
                answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
                db.session.add(answer)
            db.session.commit()

            try:
                if response.is_submitted:
                    LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=response.id))
                    user = db.session.query(AppUser).filter(AppUser.id==g.current_user['id']).first()
                    self.send_confirmation(user, response)
            except:
                LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=response.id))
            finally:
                return response, 201  # 201 is 'CREATED' status code

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    @marshal_with(response_fields)
    def put(self):
        # Update an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        req_parser.add_argument('is_submitted', type=bool, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        try: 
            old_response = db.session.query(Response).filter(Response.id == args['id']).first()
            if not old_response:
                LOGGER.error("Response not found for id {}".format(args['id']))
                return errors.RESPONSE_NOT_FOUND
            if old_response.user_id != user_id:
                LOGGER.error("Old user id {} does not match user id {}".format(old_response.user_id, user_id))
                return errors.UNAUTHORIZED
            if old_response.application_form_id != args['application_form_id']:
                LOGGER.error("Update conflict for {}".format(args['application_form_id']))
                return errors.UPDATE_CONFLICT

            old_response.is_submitted = args['is_submitted']
            if args['is_submitted']:
                old_response.submitted_timestamp = datetime.datetime.now()
                old_response.is_withdrawn = False
                old_response.withdrawn_timestamp = None

            for answer_args in args['answers']:
                old_answer = db.session.query(Answer).filter(Answer.response_id == old_response.id, Answer.question_id == answer_args['question_id']).first()
                if old_answer:  # Update the existing answer
                    old_answer.value = answer_args['value']
                else:
                    answer = Answer(old_response.id, answer_args['question_id'], answer_args['value'])
                    db.session.add(answer)
            db.session.commit()
            db.session.flush()

            try:
                if old_response.is_submitted:
                    LOGGER.info('Sending confirmation email for response with ID : {id}'.format(id=old_response.id))
                    user = db.session.query(AppUser).filter(AppUser.id==g.current_user['id']).first()
                    self.send_confirmation(user, old_response)
            except:                
                LOGGER.warn('Failed to send confirmation email for response with ID : {id}, but the response was submitted succesfully'.format(id=old_response.id))
            finally:
                return old_response, 200

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def delete(self):
        # Delete an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        args = req_parser.parse_args()

        try:
            response = db.session.query(Response).filter(Response.id == args['id']).first()
            if not response:
                return errors.RESPONSE_NOT_FOUND

            if response.user_id != g.current_user['id']:
                return errors.UNAUTHORIZED
            
            response.is_withdrawn = True
            response.withdrawn_timestamp = datetime.datetime.now()
            response.is_submitted = False
            response.submitted_timestamp = None

            db.session.commit()
            db.session.flush()

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE            

        try:
            user = db.session.query(AppUser).filter(AppUser.id == g.current_user['id']).first()
            event = response.application_form.event
            organisation = event.organisation
            subject = 'Withdrawal of Application for the {event_name}'.format(event_name=event.description)
            
            withdrawal_template = email_repository.get(event.id, 'withdrawal').template
            body_text = withdrawal_template.format(title=user.user_title, firstname=user.firstname, lastname=user.lastname, organisation_name=organisation.name)
            emailer.send_mail(user.email, subject, body_text)
        except:                
            LOGGER.error('Failed to send withdrawal confirmation email for response with ID : {id}, but the response was withdrawn succesfully'.format(id=args['id']))

        return {}, 204

    def send_confirmation(self, user, response):
        try:
            answers = db.session.query(Answer).join(Question, Answer.question_id == Question.id).filter(Answer.response_id == response.id).order_by(Question.order).all()
            if answers is None:
                LOGGER.warn('Found no answers associated with response with id {response_id}'.format(response_id=response.id))

            application_form = db.session.query(ApplicationForm).filter(ApplicationForm.id == response.application_form_id).first() 
            if application_form is None:
                LOGGER.warn('Found no application form with id {form_id}'.format(form_id=response.application_form_id))

            event = db.session.query(Event).filter(Event.id == application_form.event_id).first() 
            if event is None:
                LOGGER.warn('Found no event id {event_id}'.format(form_id=application_form.event_id))
        except:
            LOGGER.error('Could not connect to the database to retrieve response confirmation email data on response with ID : {response_id}'.format(response_id=response.id))

        try:
            subject = 'Your application to {}'.format(event.description)
            greeting = strings.build_response_email_greeting(user.user_title, user.firstname, user.lastname)
            body_text = greeting + '\n\n' + strings.build_response_email_body(event.name, event.description, answers)
            emailer.send_mail(user.email, subject, body_text=body_text)

        except:
            LOGGER.error('Could not send confirmation email for response with id : {response_id}'.format(response_id=response.id))



            

