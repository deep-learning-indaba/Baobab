from datetime import datetime

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from sqlalchemy.exc import IntegrityError


from app.events.models import Event
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

from app import db, bcrypt, LOGGER

from app.utils.auth import auth_optional


def event_info(user_id, event):
    return {
        'id': event.id,
        'description': event.description,
        'start_date': event.start_date.strftime("%d %B %Y"),
        'end_date': event.end_date.strftime("%d %B %Y"),
        'status': get_user_event_response_status(user_id, event.id)
    }


def get_user_event_response_status(user_id, event_id):
    applicationForm = db.session.query(ApplicationForm).filter(
        ApplicationForm.event_id == event_id).first()

    if applicationForm:
        if applicationForm.deadline < datetime.now():
            return "Application closed"
        elif user_id:
            response = db.session.query(Response).filter(
                Response.application_form_id == applicationForm.id).filter(Response.user_id == user_id).first()

            if response:
                if response.is_withdrawn:
                    return "Application withdrawn"

                if response.is_submitted:
                    return "Applied"
        else:
            return "Apply now"

    return "Application not available"


class EventsAPI(restful.Resource):

    @auth_optional
    def get(self):
        user_id = 0

        if g and hasattr(g, 'current_user'):
            user_id = g.current_user["id"]

        events = db.session.query(Event).filter(
            Event.start_date > datetime.now()).all()

        returnEvents = []

        for event in events:
            returnEvents.append(event_info(user_id, event))

        return returnEvents, 200
