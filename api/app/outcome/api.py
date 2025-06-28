import traceback
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from flask import g, request
from sqlalchemy.exc import SQLAlchemyError


from app.outcome.models import Outcome, Status
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.events.repository import EventRepository as event_repository
from app.users.repository import UserRepository as user_repository
from app.utils.emailer import email_user

from app.responses.repository import ResponseRepository as response_repository
from app.utils import errors, strings
from app.reviews.repository import ReviewRepository as review_repository
from app.events.models import EventType

from app.utils.auth import auth_required, event_admin_required
from app import LOGGER
from app import db
from app.utils import errors
from app.utils import misc
from app.reviews.api import ReviewResponseDetailListAPI


def _extract_status(outcome):
    if not isinstance(outcome, Outcome):
        return None
    return outcome.status.name

outcome_fields = {
    'id': fields.Integer,
    'status': fields.String(attribute=_extract_status),
    'timestamp': fields.DateTime(dt_format='iso8601'),
    'review_summary': fields.String,
}

user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String
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

outcome_list_fields = {
    'id': fields.Integer,
    'status': fields.String(attribute=_extract_status),
    'timestamp': fields.DateTime(dt_format='iso8601'),
    'user': fields.Nested(user_fields),
    'updated_by_user': fields.Nested(user_fields),
    'response': fields.Nested(response_fields)
}

class OutcomeAPI(restful.Resource):
    @event_admin_required
    @marshal_with(outcome_fields)
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('user_id', type=int, required=True)
        req_parser.add_argument('response_id', type=int, required=True)
        args = req_parser.parse_args()

        user_id = args['user_id']
        response_id=args['response_id']

        try:
            outcome = outcome_repository.get_latest_by_user_for_event(user_id, event_id, response_id)
            if not outcome:
                return errors.OUTCOME_NOT_FOUND
            
            return outcome

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
        
    

    @event_admin_required
    @marshal_with(outcome_fields)
    def post(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('user_id', type=int, required=True)
        req_parser.add_argument('outcome', type=str, required=True)
        req_parser.add_argument('response_id', type=int, required=True)
        req_parser.add_argument('review_summary', type=str, required=False)
        args = req_parser.parse_args()

        event = event_repository.get_by_id(event_id)

        if not event:
            return errors.EVENT_NOT_FOUND

        user = user_repository.get_by_id(args['user_id'])
        if not user:
            return errors.USER_NOT_FOUND
        

        try:
            status = Status[args['outcome']]
        except KeyError:
            return errors.OUTCOME_STATUS_NOT_VALID

        try:
            # Set existing outcomes to no longer be the latest outcome
            existing_outcomes = outcome_repository.get_all_by_user_for_event(args['user_id'], event_id, args['response_id'])
            for existing_outcome in existing_outcomes:
                existing_outcome.reset_latest()

            # Add new outcome
            outcome = Outcome(
                    event_id,
                    args['user_id'],
                    status,
                    g.current_user['id'],
                    args['response_id'],
                    args.get('review_summary')) 
                    # args['review_summary'])

            outcome_repository.add(outcome)
            db.session.commit()

            if (event.event_type==EventType.JOURNAL):
                response = response_repository.get_by_id_and_user_id(outcome.response_id, outcome.user_id)
                submission_title=strings.answer_by_question_key('submission_title', response.application_form, response.answers)
                review_form = review_repository.get_review_form(outcome.event_id)

                if review_form is not None:
                    response_reviews = review_repository.get_all_review_responses_by_response(review_form.id, outcome.response_id)
                else:
        
                    raise errors.REVIEW_FORM_NOT_FOUND
                
                serialized_reviews =  [ReviewResponseDetailListAPI._serialise_review_response(response, user.user_primaryLanguage) for response in response_reviews]

                question_answer_summary = strings.build_review_email_body(serialized_reviews, user.user_primaryLanguage, review_form)
                email_user(
                        'response-journal',
                        template_parameters=dict(
                            summary=outcome.review_summary,
                            outcome=outcome.status.value,
                            submission_title=submission_title,
                            reviewers_contents=question_answer_summary,
                        ), 
                        subject_parameters=dict(
                            submission_title=submission_title,
                        ),
                        event=event,
                        user=user,
                    )

            else:
                if (status == Status.REJECTED or status == Status.WAITLIST):  # Email will be sent with offer for accepted candidates  
                    email_user(
                        'outcome-rejected' if status == Status.REJECTED else 'outcome-waitlist',
                        template_parameters=dict(
                            host=misc.get_baobab_host()
                        ),
                        event=event,
                        user=user,
                    )
            
            
            return outcome, 201

        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE
        


class OutcomeListAPI(restful.Resource):
    @event_admin_required
    @marshal_with(outcome_list_fields)
    def get(self, event_id):
        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        try:
            outcomes = outcome_repository.get_latest_for_event(event_id)
            return outcomes
        except SQLAlchemyError as e:
            LOGGER.error("Database error encountered: {}".format(e))            
            return errors.DB_NOT_AVAILABLE
        except: 
            LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))
            return errors.DB_NOT_AVAILABLE



        
