from datetime import datetime

from app import db


class OutboxStatus:
    PENDING = 'pending'
    SENDING = 'sending'
    SENT = 'sent'
    SKIPPED = 'skipped'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    #: Statuses that will never be attempted again.
    TERMINAL = (SENT, SKIPPED, FAILED, CANCELLED)


class OutboxChannel:
    EMAIL = 'email'
    PUSH = 'push'


#: A message is abandoned after this many delivery attempts.
MAX_ATTEMPTS = 3


class OutboxMessage(db.Model):
    """One queued outbound message: a single recipient on a single channel.

    Producers enqueue rows and return immediately; the worker behind
    /api/v1/tasks/outbox claims and delivers them. Sending to a few thousand
    recipients takes far longer than a request is allowed to run, so no producer
    may deliver inline.
    """

    __tablename__ = 'outbox_message'

    id = db.Column(db.Integer(), primary_key=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)

    channel = db.Column(db.String(16), nullable=False)
    # Snapshot of the address as it was when the message was composed, so a later
    # profile edit can't redirect a message that is already queued. Null for
    # push, which addresses the user's registered subscriptions instead.
    recipient = db.Column(db.String(255), nullable=True)

    subject = db.Column(db.String(500), nullable=True)
    body_text = db.Column(db.Text(), nullable=True)
    body_html = db.Column(db.Text(), nullable=True)
    # Channel-specific extras. For push this is the full Web Push payload.
    payload = db.Column(db.JSON(), nullable=True)

    # Resolved at enqueue time: the worker's requests carry no Origin header, so
    # it cannot resolve an organisation the way an ordinary request does.
    sender_name = db.Column(db.String(100), nullable=True)
    sender_email = db.Column(db.String(100), nullable=True)

    status = db.Column(db.String(16), nullable=False, default=OutboxStatus.PENDING)
    attempts = db.Column(db.Integer(), nullable=False, default=0)
    last_error = db.Column(db.Text(), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    # Not eligible for delivery before this time, which covers both scheduled
    # sends and the backoff applied to a message that failed.
    scheduled_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    claimed_at = db.Column(db.DateTime(), nullable=True)
    claim_token = db.Column(db.String(36), nullable=True)
    sent_at = db.Column(db.DateTime(), nullable=True)

    # What produced this message, e.g. ('announcement', 42).
    source_type = db.Column(db.String(32), nullable=False)
    source_id = db.Column(db.Integer(), nullable=True)

    __table_args__ = (
        # Makes enqueueing idempotent: re-running a producer for the same source
        # can't queue a second copy for a recipient it already covered. Rows with
        # no user_id are exempt, since NULLs don't collide in a unique index.
        db.UniqueConstraint('source_type', 'source_id', 'channel', 'user_id',
                            name='uq_outbox_source_channel_user'),
        db.Index('ix_outbox_claimable', 'status', 'scheduled_at'),
        db.Index('ix_outbox_source', 'source_type', 'source_id'),
    )
