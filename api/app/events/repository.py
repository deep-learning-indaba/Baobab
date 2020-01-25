from app import db
from app.events.models import Event


class EventRepository():
    
    @staticmethod
    def get_by_id(event_id):
        return db.session.query(Event).get(event_id)

    @staticmethod
    def get_by_key(event_key):
        return db.session.query(Event).filter_by(key=event_key).first()