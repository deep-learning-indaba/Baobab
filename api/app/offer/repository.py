from app import db
from app.offer.models import Offer, OfferTag
from sqlalchemy import func, cast, Date

class OfferRepository():

    @staticmethod
    def get_by_id(offer_id):
        return db.session.query(Offer).get(offer_id)

    @staticmethod
    def get_by_user_id_for_event(user_id, event_id):
        return db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()

    @staticmethod
    def get_offers_for_event(event_id, offer_ids):
        return (
            db.session.query(Offer)
            .filter(Offer.event_id==event_id, Offer.id.in_(offer_ids))
            .all()
        )
    
    @staticmethod
    def get_all_offers_for_event(event_id):
        return (
            db.session.query(Offer)
            .filter(Offer.event_id==event_id)
            .all()
        )

    @staticmethod
    def count_offers_allocated(event_id):
        count = (db.session.query(Offer)
                        .filter_by(event_id=event_id)
                        .count())
        return count

    @staticmethod
    def count_offers_accepted(event_id):
        count = (db.session.query(Offer)
                        .filter_by(event_id=event_id, candidate_response=True)
                        .count())
        return count

    @staticmethod
    def count_offers_rejected(event_id):
        count = (db.session.query(Offer)
                        .filter_by(event_id=event_id, candidate_response=False)
                        .count())
        return count
 
    @staticmethod
    def timeseries_offers_accepted(event_id):
        timeseries = (db.session.query(cast(Offer.responded_at, Date), func.count(Offer.responded_at))
                        .filter_by(event_id=event_id, candidate_response=True)
                        .group_by(cast(Offer.responded_at, Date))
                        .order_by(cast(Offer.responded_at, Date))
                        .all())
        return timeseries
    
    @staticmethod
    def tag_offer(offer_id, tag_id, accepted):
        offer_tag = OfferTag(offer_id, tag_id, accepted)
        db.session.add(offer_tag)
        db.session.commit()

    @staticmethod
    def remove_tag_from_offer(offer_id, tag_id):
        (db.session.query(OfferTag)
         .filter_by(offer_id=offer_id, tag_id=tag_id)
         .delete())
        db.session.commit()