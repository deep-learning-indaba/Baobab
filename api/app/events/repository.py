from app import db
from app.events.models import Event
from app.organisation.models import Organisation


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
        return db.session.query(Event)\
                         .filter_by(key=event_key)\
                         .join(Organisation, Organisation.id==Event.organisation_id)\
                         .first()

    @staticmethod
    def get_by_id_with_organisation(event_id):
        return db.session.query(Event)\
                         .filter_by(id=event_id)\
                         .join(Organisation, Organisation.id==Event.organisation_id)\
                         .one_or_none()