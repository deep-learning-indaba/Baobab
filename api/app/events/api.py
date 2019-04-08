from datetime import datetime
import traceback

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError

from app.events.models import Event, EventRole
from app.events.mixins import EventsMixin
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

from app import db, bcrypt, LOGGER
from app.utils.errors import EVENT_NOT_FOUND, FORBIDDEN

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail


def event_info(user_id, event):
    return {
        'id': event.id,
        'description': event.description,
        'start_date': event.start_date.strftime("%d %B %Y"),
        'end_date': event.end_date.strftime("%d %B %Y"),
        'status': get_user_event_response_status(user_id, event.id)
    }


def get_user_event_response_status(user_id, event_id):

    def _log_application_status(context):
        LOGGER.debug("Application {} for user_id: {}, event_id: {}".format(context, user_id, event_id))

    try: 
        applicationForm = db.session.query(ApplicationForm).filter(
            ApplicationForm.event_id == event_id).first()

        if applicationForm:
            if applicationForm.deadline < datetime.now():
                _log_application_status('closed, deadline passed')
                return "Application closed"
            elif user_id:
                response = db.session.query(Response).filter(
                    Response.application_form_id == applicationForm.id).filter(
                        Response.user_id == user_id
                        ).order_by(Response.started_timestamp.desc()).first()

                if response:
                    if response.is_withdrawn:
                        _log_application_status('withdrawn')
                        return "Application withdrawn"
                    elif response.is_submitted:
                        _log_application_status('submitted')
                        return "Applied"
                    else:
                        _log_application_status('continue')
                        return "Continue application"
                else:
                    _log_application_status('open')
                    return "Apply now"

            else:
                _log_application_status('open')
                return "Apply now"
    
    except SQLAlchemyError as e:
        LOGGER.error("Database error encountered: {}".format(e))            
    except: 
        LOGGER.error("Encountered unknown error: {}".format(traceback.format_exc()))

    _log_application_status('not available')
    return "Application not available"


class EventsAPI(restful.Resource):

    @auth_optional
    def get(self):
        user_id = 0

        if g and hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user["id"]

        events = db.session.query(Event).filter(
            Event.start_date > datetime.now()).all()

        returnEvents = []

        for event in events:
            returnEvents.append(event_info(user_id, event))

        return returnEvents, 200


class EventStatsAPI(EventsMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()

        event = db.session.query(Event).filter(Event.id == args['event_id']).first()
        if not event:
            return EVENT_NOT_FOUND

        user_id = g.current_user["id"]
        event_id = args['event_id']
        user = db.session.query(AppUser).filter(AppUser.id == user_id).first()
        if not user.is_event_admin(event_id):
            return FORBIDDEN

        num_users = db.session.query(AppUser.id).count()
        num_responses = db.session.query(Response.id).count()
        num_submitted_respones = db.session.query(Response).filter(Response.is_submitted == True).count()

        return {
            'event_description': event.description,
            'num_users': num_users,
            'num_responses': num_responses,
            'num_submitted_responses': num_submitted_respones
        }, 200


NOT_SUBMITTED_EMAIL_BODY="""
Dear {} {} {},

We noticed that you started applying to attend the {} but have not completed and submitted your application. This is a reminder that the deadline for applications is {} and any applications not submitted by this date will not be considered. Please complete and submit your application if you would still like to attend this event.

Kind Regards,
The Deep Learning Indaba team
"""

class NotSubmittedReminderAPI(EventsMixin, restful.Resource):
    
    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        event = db.session.query(Event).get(event_id)
        if not event:
            return EVENT_NOT_FOUND

        user = db.session.query(AppUser).get(user_id)
        if not user.is_event_admin(event_id):
            return FORBIDDEN

        users = user_repository.get_all_users_with_unsubmitted_response()
        for user in users:
            title = user.user_title
            firstname = user.firstname
            lastname = user.lastname
            event_name = event.name
            deadline = event.get_application_form().deadline.strftime('%A %-d %B %Y')
            
            subject = '{} Reminder'.format(event_name)
            body = NOT_SUBMITTED_EMAIL_BODY.format(title, firstname, lastname, event_name, deadline)
            
            send_mail(recipient=user.email, subject=subject, body_text=body)
        
        return {'unsubmitted_responses': len(users)}, 201