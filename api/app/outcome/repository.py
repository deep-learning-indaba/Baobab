from app import db
from app.outcome.models import Outcome


class OutcomeRepository():

    @staticmethod
    def get_latest_by_user_for_event(user_id, event_id,response_id=None):
        outcome = (db.session.query(Outcome)
                        .filter_by(user_id=user_id, event_id=event_id, latest=True,response_id=response_id)
                        .first())
        return outcome
    
    @staticmethod
    def get_all_by_user_for_event(user_id, event_id, response_id=None):
        outcomes = (db.session.query(Outcome)
                        .filter_by(user_id=user_id, event_id=event_id, response_id=response_id)
                        .all())
        return outcomes

    @staticmethod
    def get_latest_for_event(event_id):
        outcomes = (db.session.query(Outcome)
                        .filter_by(latest=True, event_id=event_id)
                        .all())
        return outcomes

    @staticmethod
    def add(outcome):
        db.session.add(outcome)

    