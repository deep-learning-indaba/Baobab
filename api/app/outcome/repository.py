from app import db
from app.outcome.models import Outcome


class OutcomeRepository():

    @staticmethod
    def get_latest_by_user_for_event(user_id, event_id):
        outcome = (db.session.query(Outcome)
                        .filter_by(user_id=user_id, event_id=event_id, latest=True)
                        .first())
        return outcome
    
    @staticmethod
    def get_all_by_user_for_event(user_id, event_id):
        outcomes = (db.session.query(Outcome)
                        .filter_by(user_id=user_id, event_id=event_id)
                        .all())
        return outcomes

    @staticmethod
    def add(outcome):
        db.session.add(outcome)