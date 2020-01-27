from datetime import datetime
import traceback

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import SQLAlchemyError

from app.events.models import Event, EventRole
from app.events.mixins import EventsMixin, EventsKeyMixin
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

from app import db, bcrypt, LOGGER
from app.utils.errors import EVENT_NOT_FOUND, FORBIDDEN, EVENT_WITH_KEY_NOT_FOUND

from app.utils.auth import auth_optional, auth_required
from app.utils.emailer import send_mail
from app.events.repository import EventRepository as event_repository
from app.organisation.models import Organisation


def event_info(user_id, event_org):
    return {
        'id': event_org.Event.id,
        'description': event_org.Event.description,
        'key': event_org.Event.key,
        'start_date': event_org.Event.start_date.strftime("%d %B %Y"),
        'end_date': event_org.Event.end_date.strftime("%d %B %Y"),
        'status': get_user_event_response_status(user_id, event_org.Event.id),
        'email_from': event_org.Event.email_from,
        'organisation_name': event_org.Organisation.name,
        'organisation_id': event_org.Organisation.id,
        'url': event_org.Event.url,
        'is_application_open': event.is_application_open,
        'is_review_open': event.is_review_open,
        'is_selection_open': event.is_selection_open,
        'is_offer_open': event.is_offer_open,
        'is_registration_open': event.is_registration_open
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

        events = db.session.query(Event, Organisation).filter(
            Event.start_date > datetime.now()).join(Organisation, Organisation.id==Event.organisation_id).all()

        returnEvents = []

        for event in events:
            returnEvents.append(event_info(user_id, event))


        return returnEvents, 200


class EventStatsAPI(EventsMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()

        event = event_repository.get_by_id_with_organisation(args['event_id'])
        if not event:
            return EVENT_NOT_FOUND

        user_id = g.current_user["id"]
        event_id = args['event_id']
        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        num_users = db.session.query(AppUser.id).count()
        num_responses = db.session.query(Response.id).count()
        num_submitted_respones = db.session.query(Response).filter(Response.is_submitted == True).count()

        return {
            'event_description': event.Event.description,
            'num_users': num_users,
            'num_responses': num_responses,
            'num_submitted_responses': num_submitted_respones
        }, 200

class EventsByKeyAPI(EventsKeyMixin, restful.Resource):

    @auth_required
    def get(self):
        args = self.req_parser.parse_args()

        event = event_repository.get_by_key_with_organisation(args['event_key'])
        if not event:
            return EVENT_WITH_KEY_NOT_FOUND

        user_id = g.current_user["id"]
        event_id = args['event_id']
        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        return event_info(user_id, event), 200


NOT_SUBMITTED_EMAIL_BODY="""
Dear {title} {firstname} {lastname},

We noticed that you started applying to attend the {event} but have not completed and submitted your application. This is a final reminder that you have until {deadline} to submit your application in order to be considered. Please complete and submit your application if you would still like to attend this event.

We have noticed that some people were confused about the "check your answers" page and may not have clicked on the Submit button on this page. Please be aware that you must click on the Submit button to confirm your application. If you do not receive an email from us with a copy of your answers, your application will not be considered.

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

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        users = user_repository.get_all_with_unsubmitted_response()
        for user in users:
            title = user.user_title
            firstname = user.firstname
            lastname = user.lastname
            event_name = event.name
            deadline = event.get_application_form().deadline.strftime('%A %-d %B %Y')
            
            subject = 'FINAL REMINDER to submit you application for {}'.format(event_name)
            body = NOT_SUBMITTED_EMAIL_BODY.format(title=title, firstname=firstname, lastname=lastname, event=event_name, deadline=deadline)
            
            send_mail(recipient=user.email, subject=subject, body_text=body)
        
        return {'unsubmitted_responses': len(users)}, 201

# TODO change your Baobab to [event] 
NOT_STARTED_EMAIL_BODY="""
Dear {title} {firstname} {lastname},

WE HAVE NOT RECEIVED YOUR APPLICATION TO ATTEND {event}

We noticed that you have created a Baobab account, but have not yet started an application to attend {event}. 

If you think you have already filled in the form, you may have not clicked on the SUBMIT button on the final page. If this is the case, we DO NOT have your application and unfortunately you will have to re-do it. We sincerely apologise for any confusion and inconvenience in this regard. 
This is a final reminder that you have until {deadline} to complete and submit your application. 

Please ensure you have submitted your application before this date if you would still like to attend this event.

Kind Regards,
The Deep Learning Indaba team
"""
    
class NotStartedReminderAPI(EventsMixin, restful.Resource):
    
    @auth_required
    def post(self):
        args = self.req_parser.parse_args()
        event_id = args['event_id']
        user_id = g.current_user['id']

        event = db.session.query(Event).get(event_id)
        if not event:
            return EVENT_NOT_FOUND

        current_user = user_repository.get_by_id(user_id)
        if not current_user.is_event_admin(event_id):
            return FORBIDDEN

        users = user_repository.get_all_without_responses()
        for user in users:
            title = user.user_title
            firstname = user.firstname
            lastname = user.lastname
            event_name = event.name
            deadline = event.get_application_form().deadline.strftime('%A %-d %B %Y')
            
            subject = 'FINAL REMINDER: We do not have your application to attend {}'.format(event_name)
            body = NOT_STARTED_EMAIL_BODY.format(title=title, firstname=firstname, lastname=lastname, event=event_name, deadline=deadline)
            
            send_mail(recipient=user.email, subject=subject, body_text=body)
        
        return {'not_started_responses': len(users)}, 201