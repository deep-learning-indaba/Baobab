import uuid
from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.outbox.models import MAX_ATTEMPTS, OutboxMessage, OutboxStatus


#: How long a claimed message may sit in 'sending' before it's assumed the worker
#: holding it died. Comfortably longer than one worker run.
STALE_CLAIM_SECONDS = 600

#: Base delay before retrying a failed message, multiplied by the attempt count.
RETRY_BACKOFF_MINUTES = 5


class OutboxRepository:

    @staticmethod
    def enqueue_many(messages, source_type=None, source_id=None):
        """Queue messages, skipping any already queued for the same source.

        `messages` are plain dicts of OutboxMessage column values. Nothing is
        committed: the caller commits so that the queued rows and whatever they
        were derived from land in a single transaction.

        Returns the number of rows queued.
        """
        if not messages:
            return 0

        if source_type is not None:
            already_queued = OutboxRepository.queued_keys(source_type, source_id)
            messages = [
                m for m in messages
                if (m.get('channel'), m.get('user_id')) not in already_queued
            ]
            if not messages:
                return 0

        db.session.bulk_insert_mappings(OutboxMessage, messages)
        return len(messages)

    @staticmethod
    def queued_keys(source_type, source_id):
        """(channel, user_id) pairs already present for a source, in any status."""
        rows = (db.session.query(OutboxMessage.channel, OutboxMessage.user_id)
                .filter(OutboxMessage.source_type == source_type,
                        OutboxMessage.source_id == source_id)
                .all())
        return {(row[0], row[1]) for row in rows}

    @staticmethod
    def claim_batch(limit, now=None):
        """Take exclusive ownership of up to `limit` messages that are due.

        The `status == 'pending'` predicate on the UPDATE is what makes the claim
        exclusive: concurrent workers may select overlapping candidates, but only
        one UPDATE can move a given row out of 'pending', and each worker then
        reads back only the rows carrying its own token. That keeps the claim
        portable to SQLite, which has no SELECT ... FOR UPDATE SKIP LOCKED.
        """
        now = now or datetime.utcnow()
        token = str(uuid.uuid4())

        candidate_ids = [row[0] for row in (
            db.session.query(OutboxMessage.id)
            .filter(OutboxMessage.status == OutboxStatus.PENDING,
                    OutboxMessage.scheduled_at <= now)
            .order_by(OutboxMessage.scheduled_at, OutboxMessage.id)
            .limit(limit)
            .all())]
        if not candidate_ids:
            return []

        (db.session.query(OutboxMessage)
         .filter(OutboxMessage.id.in_(candidate_ids),
                 OutboxMessage.status == OutboxStatus.PENDING)
         .update({'status': OutboxStatus.SENDING, 'claimed_at': now, 'claim_token': token},
                 synchronize_session=False))
        db.session.commit()

        return (db.session.query(OutboxMessage)
                .filter(OutboxMessage.claim_token == token)
                .order_by(OutboxMessage.id)
                .all())

    @staticmethod
    def release(messages):
        """Return claimed but unattempted messages to the pending pool.

        No attempt is charged, because none was made — this is the worker running
        out of its time budget, not a delivery failure.
        """
        for message in messages:
            message.status = OutboxStatus.PENDING
            message.claim_token = None
            message.claimed_at = None
        return len(messages)

    @staticmethod
    def requeue_stale(stale_before=None):
        """Recover messages whose worker died while holding them.

        An abandoned message is charged an attempt even though its outcome is
        unknown, so a message that reliably kills its worker lands in 'failed'
        instead of cycling forever.
        """
        stale_before = stale_before or (datetime.utcnow() - timedelta(seconds=STALE_CLAIM_SECONDS))
        stale = (db.session.query(OutboxMessage)
                 .filter(OutboxMessage.status == OutboxStatus.SENDING,
                         OutboxMessage.claimed_at < stale_before)
                 .all())
        for message in stale:
            OutboxRepository.mark_failed(
                message, 'Abandoned: the worker holding this message reported no outcome')
        if stale:
            db.session.commit()
        return len(stale)

    @staticmethod
    def mark_sent(message, now=None):
        message.status = OutboxStatus.SENT
        message.sent_at = now or datetime.utcnow()
        message.attempts += 1
        message.claim_token = None
        message.last_error = None

    @staticmethod
    def mark_skipped(message, reason):
        """Terminal, but not a failure — there was nothing to deliver to."""
        message.status = OutboxStatus.SKIPPED
        message.attempts += 1
        message.claim_token = None
        message.last_error = str(reason)[:2000]

    @staticmethod
    def mark_failed(message, error):
        """Record a failed attempt, scheduling a retry until attempts run out."""
        message.attempts += 1
        message.claim_token = None
        message.last_error = str(error)[:2000]
        if message.attempts >= MAX_ATTEMPTS:
            message.status = OutboxStatus.FAILED
        else:
            message.status = OutboxStatus.PENDING
            message.scheduled_at = (datetime.utcnow()
                                    + timedelta(minutes=RETRY_BACKOFF_MINUTES * message.attempts))

    @staticmethod
    def retry_terminal(source_type, source_id, statuses=None):
        """Return a source's given-up messages to the queue for another attempt.

        Only touches statuses passed in, which must never include 'sent' — a
        message that was delivered has to stay delivered, or a retry turns into a
        duplicate for someone who already received it.

        The attempt counter is reset, so a retried message gets a full allowance
        rather than failing again immediately.
        """
        statuses = statuses or (OutboxStatus.FAILED, OutboxStatus.SKIPPED)
        if OutboxStatus.SENT in statuses:
            raise ValueError('Refusing to retry messages that were already sent')

        now = datetime.utcnow()
        return (db.session.query(OutboxMessage)
                .filter(OutboxMessage.source_type == source_type,
                        OutboxMessage.source_id == source_id,
                        OutboxMessage.status.in_(statuses))
                .update({'status': OutboxStatus.PENDING, 'attempts': 0, 'claim_token': None,
                         'claimed_at': None, 'scheduled_at': now, 'last_error': None},
                        synchronize_session=False))

    @staticmethod
    def status_counts(source_type, source_ids):
        """{source_id: {channel: {status: count}}} for several sources at once."""
        if not source_ids:
            return {}

        rows = (db.session.query(OutboxMessage.source_id,
                                 OutboxMessage.channel,
                                 OutboxMessage.status,
                                 func.count(OutboxMessage.id))
                .filter(OutboxMessage.source_type == source_type,
                        OutboxMessage.source_id.in_(source_ids))
                .group_by(OutboxMessage.source_id, OutboxMessage.channel, OutboxMessage.status)
                .all())

        counts = {}
        for source_id, channel, status, count in rows:
            counts.setdefault(source_id, {}).setdefault(channel, {})[status] = count
        return counts

    @staticmethod
    def pending_count():
        return (db.session.query(OutboxMessage)
                .filter(OutboxMessage.status == OutboxStatus.PENDING)
                .count())

    @staticmethod
    def delete_for_source(source_type, source_id):
        (db.session.query(OutboxMessage)
         .filter(OutboxMessage.source_type == source_type,
                 OutboxMessage.source_id == source_id)
         .delete(synchronize_session=False))
