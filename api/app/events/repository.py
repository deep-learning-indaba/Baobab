from datetime import datetime

from sqlalchemy import and_, or_

from app import db
from app.applicationModel.models import ApplicationForm
from app.events.models import Event
from app.invitedGuest.models import InvitedGuest
from app.organisation.models import Organisation
from app.registration.models import Offer
from app.responses.models import Response


class EventRepository:
    @staticmethod
    def get_by_id(event_id):
        return db.session.query(Event).get(event_id)

    @staticmethod
    def exists_by_key(event_key):
        return db.session.query(Event.id).filter_by(key=event_key).first() is not None

    @staticmethod
    def get_by_key(event_key):
        return db.session.query(Event).filter_by(key=event_key).first()

    @staticmethod
    def get_event_by_response_id(response_id):
        result = (
            db.session.query(
                Response.application_form_id, ApplicationForm.event_id, Event
            )
            .filter_by(id=response_id)
            .join(ApplicationForm, ApplicationForm.id == Response.application_form_id)
            .join(Event, Event.id == ApplicationForm.event_id)
            .first()
        )
        return result.Event if result else None

    @staticmethod
    def get_upcoming_for_organisation(organisation_id):
        return (
            db.session.query(Event)
            .filter(Event.end_date >= datetime.now())
            .filter_by(organisation_id=organisation_id)
            .all()
        )

    @staticmethod
    def get_attended_by_user_for_organisation(organisation_id, user_id):
        return (
            db.session.query(Event)
            .filter(Event.end_date < datetime.now())
            .filter_by(organisation_id=organisation_id)
            .outerjoin(
                Offer,
                and_(
                    Event.id == Offer.event_id,
                    Offer.user_id == user_id,
                    Offer.candidate_response == True,
                ),
            )
            .outerjoin(
                InvitedGuest,
                and_(
                    Event.id == InvitedGuest.event_id, InvitedGuest.user_id == user_id
                ),
            )
            .filter(or_(Offer.id != None, InvitedGuest.id != None))
            .all()
        )

    @staticmethod
    def add(event):
        db.session.add(event)
        db.session.commit()
        return event
