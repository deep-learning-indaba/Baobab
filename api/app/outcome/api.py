import traceback
from flask_restful import reqparse, fields, marshal_with
import flask_restful as restful
from flask import g, request
from sqlalchemy.exc import SQLAlchemyError

from app.outcome.models import OutcomeModel, Status
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.events.repository import EventRepository as event_repository
from app.users.repository import UserRepository as user_repository

from app.utils.auth import auth_required, event_admin_required
from app import LOGGER
from app import db
from app.utils import errors


outcome_fields = {
    'id': fields.Integer,
    'status': fields.String,
    'timestamp': fields.DateTime(dt_format='iso8601'),
}

user_fields = {
    'id': fields.Integer,
    'email': fields.String,
    'firstname': fields.String,
    'lastname': fields.String,
    'user_title': fields.String
}

outcome_list_fields = {
    'id': fields.Integer,
    'status': fields.String,
    'timestamp': fields.DateTime(dt_format='iso8601'),
    'user': user_fields,
    'updated_by_user': user_fields
}


class OutcomeAPI(restful.Resource):
    @auth_required
    @marshal_with(outcome_fields)
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        event_id = args['event_id']

        try:
            outcome = outcome_repository.get_latest_by_user_for_event(user_id, event_id)
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
        args = req_parser.parse_args()

        event = event_repository.get_by_id(args['event_id'])
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
            existing_outcomes = outcome_repository.get_all_by_user_for_event(args['user_id'], args['event_id'])
            for existing_outcome in existing_outcomes:
                existing_outcome.reset_latest()

            # Add new outcome
            outcome = Outcome(
                    args['event_id'],
                    args['user_id'],
                    status,
                    g.current_user['id'])

            outcome_repository.add(outcome)
            db.session.commit()
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
        event = event_repository.get_by_id(args['event_id'])
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



        
