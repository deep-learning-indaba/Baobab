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


def _attachment_specs(payload):
    """[{blob_name, filename, content_type}] from a message payload. Messages
    queued before attachments became a list carry a single 'attachment'."""
    payload = payload or {}
    specs = list(payload.get('attachments') or [])
    if payload.get('attachment'):
        specs.append(payload['attachment'])
    return specs


@contextmanager
def _attachment_files(payload):
    """Downloads each attachment's blob to a local tmp file for the duration of
    the block, yielding [(filename, path, content_type)]. A message only holds
    blob names; the files themselves stay in GCS until a send needs them."""
    specs = _attachment_specs(payload)
    paths = []
    try:
        files = []
        for spec in specs:
            tmp_path = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
            paths.append(tmp_path)
            # 'bucket' is set for files kept in their own bucket (invoices);
            # None is the default bucket.
            bucket = storage.get_storage_bucket(spec.get('bucket'))
            bucket.blob(spec['blob_name']).download_to_filename(tmp_path)
            files.append((spec.get('filename') or 'document.pdf', tmp_path,
                          spec.get('content_type') or 'application/pdf'))
        yield files
    finally:
        for path in paths:
            if os.path.exists(path):
                os.remove(path)


def _deliver_email(message, connection):
    with _attachment_files(message.payload) as attachments:
        connection.send(
            recipient=message.recipient,
            subject=message.subject or '',
            body_text=message.body_text or '',
            body_html=message.body_html or '',
            sender_name=message.sender_name,
            sender_email=message.sender_email,
            attachments=attachments,
            reply_to=message.reply_to,
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


def deliver_now(message_ids):
    """Deliver specific messages immediately, for an email someone is waiting
    on (a password reset). Anything that fails stays queued with the usual
    backoff, so the cron worker retries it. Returns {message_id: outcome}."""
    messages = OutboxRepository.claim_ids(message_ids)
    outcomes = {}
    if not messages:
        return outcomes
    with SmtpConnection() as connection:
        for message in messages:
            outcomes[message.id] = _deliver_one(message, connection)
    db.session.commit()
    return outcomes


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
