import json

from app import db
from app.utils.logger import Logger

LOGGER = Logger().get_logger()


def push_to_user(user_id, payload):
    """Send a Web Push to all subscriptions for user_id. Best-effort; prunes dead subscriptions."""
    from config import VAPID_PRIVATE_KEY, VAPID_CLAIM_EMAIL
    if not VAPID_PRIVATE_KEY:
        return 0

    from pywebpush import webpush, WebPushException
    from app.announcements.models import PushSubscription

    subs = db.session.query(PushSubscription).filter_by(user_id=user_id).all()
    sent = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={'sub': VAPID_CLAIM_EMAIL},
            )
            sent += 1
        except WebPushException as e:
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            if status in (404, 410):
                db.session.delete(sub)
            LOGGER.warning('push failed for sub %s: %s', sub.id, e)
    db.session.commit()
    return sent
