from app import db
from app.events.models import Event


class EventRepository():
    
    @staticmethod
    def get_by_id(event_id):
        return db.session.query(Event).get(event_id)
