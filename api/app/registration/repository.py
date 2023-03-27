from app import db
from app.registration.models import Offer, Registration, RegistrationForm, OfferTag
from sqlalchemy import and_, func, cast, Date


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
    def tag_offer(offer_id, tag_id):
        offer_tag = OfferTag(offer_id, tag_id)
        db.session.add(offer_tag)
        db.session.commit()

    @staticmethod
    def remove_tag_from_offer(offer_id, tag_id):
        (db.session.query(OfferTag)
         .filter_by(offer_id=offer_id, tag_id=tag_id)
         .delete())
        db.session.commit()

class RegistrationRepository():
    @staticmethod
    def from_offer(offer_id):
        return (db.session.query(Registration)
                .filter_by(offer_id=offer_id)
                .first())

    @staticmethod
    def count_registrations(event_id):
        count = (db.session.query(Registration)
                        .join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .count())
        return count

    @staticmethod
    def timeseries_registrations(event_id):
        timeseries = (db.session.query(cast(Registration.created_at, Date), func.count(Registration.created_at))
                        .join(RegistrationForm, Registration.registration_form_id == RegistrationForm.id)
                        .filter_by(event_id=event_id)
                        .group_by(cast(Registration.created_at, Date))
                        .order_by(cast(Registration.created_at, Date))
                        .all())
        return timeseries

    @staticmethod
    def get_form_for_event(event_id):
        return (db.session.query(RegistrationForm).filter_by(event_id=event_id)).first()
