from datetime import datetime
from app import db
from app.events.models import Event
from app.organisation.models import Organisation
from app.responses.models import Response
from app.applicationModel.models import ApplicationForm


class EventRepository():

    @staticmethod
    def get_by_id(event_id):
        return db.session.query(Event).get(event_id)

    @staticmethod
    def exists_by_key(event_key):
        return db.session.query(Event.id)\
                         .filter_by(key=event_key)\
                         .first() is not None

    @staticmethod
    def get_by_key_with_organisation(event_key):
        return db.session.query(Event, Organisation)\
                         .filter_by(key=event_key)\
                         .join(Organisation, Organisation.id == Event.organisation_id)\
                         .first()

    @staticmethod
    def get_by_id_with_organisation(event_id):
        return db.session.query(Event, Organisation)\
                         .filter_by(id=event_id)\
                         .join(Organisation, Organisation.id == Event.organisation_id)\
                         .one_or_none()

    @staticmethod
    def get_event_by_response_id(response_id):
        result = db.session.query(Response.application_form_id, ApplicationForm.event_id, Event)\
                         .filter_by(id=response_id)\
                         .join(ApplicationForm, ApplicationForm.id == Response.application_form_id)\
                         .join(Event, Event.id == ApplicationForm.event_id)\
                         .first()
        return result.Event if result else None

    @staticmethod
    def get_upcoming_for_organisation(organisation_id):
        return db.session.query(Event, Organisation)\
                         .filter(Event.start_date > datetime.now())\
                         .filter_by(organisation_id=organisation_id)\
                         .join(Organisation, Organisation.id==Event.organisation_id)\
                         .all()

    @staticmethod
    def add(event):
        db.session.add(event)
        db.session.commit()
        return event
