from app import db, LOGGER
from app.engagement.models import EngagementEvent


class EngagementRepository:

    @staticmethod
    def record(event, user_id, event_type, metadata=None):
        """Best-effort engagement event. Never let analytics break a request."""
        try:
            db.session.add(EngagementEvent(
                organisation_id=event.organisation_id,
                event_id=event.id,
                user_id=user_id,
                event_type=event_type,
                event_metadata=metadata or {},
            ))
            db.session.commit()
        except Exception as e:  # noqa: BLE001
            LOGGER.warning('engagement record failed (%s): %s', event_type, e)
            db.session.rollback()

    @staticmethod
    def count_distinct_users(event_id, event_type):
        return (db.session.query(EngagementEvent.user_id)
                .filter_by(event_id=event_id, event_type=event_type)
                .distinct()
                .count())
