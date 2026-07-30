import json

from app import db
from app.utils.logger import Logger
from pywebpush import webpush, WebPushException
from app.announcements.models import PushSubscription


LOGGER = Logger().get_logger()


def push_to_user(user_id, payload, commit=True):
    """Send a Web Push to all subscriptions for user_id. Best-effort; prunes dead subscriptions.

    Pass commit=False when pushing to many users in one pass, so that pruned
    subscriptions are flushed once by the caller rather than once per user.

    Returns a diagnostics dict:
      {'subscriptions': n, 'sent': n, 'failed': n, 'errors': [str, ...]}
    """
    from config import VAPID_PRIVATE_KEY, VAPID_CLAIM_EMAIL
    result = {'subscriptions': 0, 'sent': 0, 'failed': 0, 'errors': []}

    if not VAPID_PRIVATE_KEY:
        LOGGER.warning(
            'push_to_user(%s) skipped: VAPID_PRIVATE_KEY is not configured; no web push will be sent',
            user_id,
        )
        result['errors'].append('VAPID_PRIVATE_KEY not configured on the server')
        return result

    subs = db.session.query(PushSubscription).filter_by(user_id=user_id).all()
    result['subscriptions'] = len(subs)
    if not subs:
        LOGGER.info('push_to_user(%s): no push subscriptions found for user', user_id)

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
            result['sent'] += 1
        except WebPushException as e:
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            if status in (404, 410):
                db.session.delete(sub)
            result['failed'] += 1
            result['errors'].append('sub {} status={}: {}'.format(sub.id, status, str(e)[:200]))
            LOGGER.warning('push failed for sub %s (status %s): %s', sub.id, status, e)
        except Exception as e:  # noqa: BLE001 - best-effort, never let one bad sub abort the rest
            result['failed'] += 1
            result['errors'].append('sub {}: {}'.format(sub.id, str(e)[:200]))
            LOGGER.warning('push error for sub %s: %s', sub.id, e, exc_info=True)
    if commit:
        db.session.commit()
    return result
