import os
import tempfile
import time
import uuid
from contextlib import contextmanager

from app import LOGGER, db
from app.outbox.models import OutboxChannel
from app.outbox.repository import OutboxRepository
from app.utils import storage
from app.utils.emailer import SmtpConnection
from app.utils.push import push_to_user
from config import OUTBOX_BATCH_SIZE, OUTBOX_TIME_BUDGET_SECONDS


#: Outcomes are committed in chunks so that a run cut short still records what it
#: managed to deliver, rather than replaying the whole batch.
COMMIT_EVERY = 25


@contextmanager
def _attachment_file(payload):
    """Downloads payload['attachment']['blob_name'] to a local tmp file for
    the duration of the block, or yields (None, None) when there is no
    attachment. A message is small (subject/body/blob name); the PDF itself
    only exists in GCS until a send actually needs it, one at a time, rather
    than every queued document sitting in local disk between enqueue and
    delivery.
    """
    attachment = (payload or {}).get('attachment')
    if not attachment:
        yield None, None
        return

    tmp_path = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4().hex}.pdf')
    try:
        bucket = storage.get_storage_bucket()
        bucket.blob(attachment['blob_name']).download_to_filename(tmp_path)
        yield attachment.get('filename') or 'document.pdf', tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _deliver_email(message, connection):
    with _attachment_file(message.payload) as (file_name, file_path):
        connection.send(
            recipient=message.recipient,
            subject=message.subject or '',
            body_text=message.body_text or '',
            body_html=message.body_html or '',
            sender_name=message.sender_name,
            sender_email=message.sender_email,
            file_name=file_name or '',
            file_path=file_path or '',
        )


def _deliver_push(message):
    result = push_to_user(message.user_id, message.payload or {}, commit=False)

    if result['subscriptions'] == 0:
        OutboxRepository.mark_skipped(message, 'No push subscriptions registered for this user')
        return 'skipped'

    if result['sent'] == 0:
        raise RuntimeError('; '.join(result['errors']) or 'Web push delivery failed')

    return 'sent'


def _deliver_one(message, connection):
    """Deliver one message and record its outcome. Returns the outcome key."""
    try:
        if message.channel == OutboxChannel.PUSH:
            outcome = _deliver_push(message)
            if outcome == 'skipped':
                return outcome
        elif message.channel == OutboxChannel.EMAIL:
            _deliver_email(message, connection)
        else:
            OutboxRepository.mark_skipped(
                message, 'Unknown channel: {}'.format(message.channel))
            return 'skipped'

        OutboxRepository.mark_sent(message)
        return 'sent'
    except Exception as e:  # noqa: BLE001 - one bad recipient must not abort the batch
        LOGGER.error('Outbox delivery failed for message %s (%s): %s',
                     message.id, message.channel, e, exc_info=True)
        OutboxRepository.mark_failed(message, e)
        return 'failed'


def deliver_pending(batch_size=None, time_budget_seconds=None):
    """Claim and deliver a batch of queued messages.

    Returns a summary dict of what happened. Delivery stops when the batch is
    exhausted or the time budget expires, whichever comes first; anything
    released is retried on the next run.
    """
    batch_size = batch_size or OUTBOX_BATCH_SIZE
    time_budget_seconds = (OUTBOX_TIME_BUDGET_SECONDS if time_budget_seconds is None
                           else time_budget_seconds)

    started_at = time.monotonic()
    summary = {'recovered': OutboxRepository.requeue_stale(),
               'claimed': 0, 'sent': 0, 'skipped': 0, 'failed': 0, 'released': 0}

    messages = OutboxRepository.claim_batch(batch_size)
    summary['claimed'] = len(messages)
    if not messages:
        return summary

    # One connection for the whole batch — see SmtpConnection. Opened lazily on
    # the first email, so a push-only batch never connects.
    with SmtpConnection() as connection:
        for index, message in enumerate(messages):
            if time.monotonic() - started_at > time_budget_seconds:
                remaining = messages[index:]
                summary['released'] = OutboxRepository.release(remaining)
                LOGGER.info('Outbox time budget reached, released %s messages', len(remaining))
                break

            summary[_deliver_one(message, connection)] += 1

            if (index + 1) % COMMIT_EVERY == 0:
                db.session.commit()

    db.session.commit()
    return summary
