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
    def enqueue_many(messages):
        """Queue messages, skipping any whose idempotency_key is already queued.

        `messages` are plain dicts of OutboxMessage column values. Nothing is
        committed: the caller commits so that the queued rows and whatever they
        were derived from land in a single transaction.

        Returns the number of rows queued.
        """
        if not messages:
            return 0

        keys = [m['idempotency_key'] for m in messages if m.get('idempotency_key')]
        if keys:
            already_queued = OutboxRepository.existing_idempotency_keys(keys)
            seen = set()
            kept = []
            for m in messages:
                key = m.get('idempotency_key')
                if key and (key in already_queued or key in seen):
                    continue
                if key:
                    seen.add(key)
                kept.append(m)
            messages = kept
            if not messages:
                return 0

        for m in messages:
            m.setdefault('sensitive', False)
        db.session.bulk_insert_mappings(OutboxMessage, messages)
        return len(messages)

    @staticmethod
    def existing_idempotency_keys(keys):
        existing = set()
        keys = list(keys)
        # Chunked: an announcement to a few thousand guests would otherwise put
        # thousands of bound parameters in one IN clause.
        for start in range(0, len(keys), 1000):
            chunk = keys[start:start + 1000]
            existing.update(row[0] for row in (
                db.session.query(OutboxMessage.idempotency_key)
                .filter(OutboxMessage.idempotency_key.in_(chunk))
                .all()))
        return existing

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
    def claim_ids(message_ids, now=None):
        """Take exclusive ownership of specific pending messages - the send_now
        path. Same exclusivity rule as claim_batch, so a cron run that picked the
        same rows can't deliver them a second time."""
        if not message_ids:
            return []
        now = now or datetime.utcnow()
        token = str(uuid.uuid4())
        (db.session.query(OutboxMessage)
         .filter(OutboxMessage.id.in_(list(message_ids)),
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
        OutboxRepository._purge_if_sensitive(message)

    @staticmethod
    def _purge_if_sensitive(message):
        """A terminal sensitive message no longer needs its body, and keeping it
        would leave a working reset or login link in the database."""
        if message.sensitive and message.status in OutboxStatus.TERMINAL:
            OutboxRepository._clear_body(message)

    @staticmethod
    def _clear_body(message, now=None):
        message.body_text = None
        message.body_html = None
        if message.channel == 'email':
            message.payload = None
        message.body_purged_at = now or datetime.utcnow()

    @staticmethod
    def purge_bodies_older_than(cutoff, limit=20000):
        """Clear the content of terminal messages created before `cutoff`,
        keeping who/when/what-type/status. Returns how many were cleared."""
        rows = (db.session.query(OutboxMessage)
                .filter(OutboxMessage.created_at < cutoff,
                        OutboxMessage.status.in_(OutboxStatus.TERMINAL),
                        OutboxMessage.body_purged_at.is_(None))
                .order_by(OutboxMessage.id)
                .limit(limit)
                .all())
        now = datetime.utcnow()
        for message in rows:
            OutboxRepository._clear_body(message, now)
        return len(rows)

    @staticmethod
    def mark_skipped(message, reason):
        """Terminal, but not a failure — there was nothing to deliver to."""
        message.status = OutboxStatus.SKIPPED
        message.attempts += 1
        message.claim_token = None
        message.last_error = str(reason)[:2000]
        OutboxRepository._purge_if_sensitive(message)

    @staticmethod
    def mark_failed(message, error):
        """Record a failed attempt, scheduling a retry until attempts run out."""
        message.attempts += 1
        message.claim_token = None
        message.last_error = str(error)[:2000]
        if message.attempts >= MAX_ATTEMPTS:
            message.status = OutboxStatus.FAILED
            OutboxRepository._purge_if_sensitive(message)
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
