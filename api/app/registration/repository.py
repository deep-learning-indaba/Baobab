from app import db
from app.registration.models import Offer


class OfferRepository():

    @staticmethod
    def get_by_user_id_for_event(user_id, event_id):
        return db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()
 