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
    # The event's contact address, so replies reach the organisers while From
    # stays the organisation's verified sending address.
    reply_to = db.Column(db.String(255), nullable=True)

    # Which email type and template revision produced the message (null for
    # push, and for a code default, which has no revision).
    template_key = db.Column(db.String(50), nullable=True)
    template_revision_id = db.Column(db.Integer(), nullable=True)
    language = db.Column(db.String(2), nullable=True)
    # The body carries a login, reset or verification code: it is hidden from
    # admins and cleared once the message reaches a terminal status.
    sensitive = db.Column(db.Boolean(), nullable=False, default=False, server_default=db.false())
    # Set when the body has been cleared (sensitive, or past retention).
    body_purged_at = db.Column(db.DateTime(), nullable=True)

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

    # Makes enqueueing idempotent where a producer wants it: re-running an
    # announcement can't queue a second copy for someone it already covered.
    # Null for messages that may legitimately repeat (a resent verification
    # email, a second reminder).
    idempotency_key = db.Column(db.String(255), nullable=True, unique=True)

    __table_args__ = (
        db.Index('ix_outbox_claimable', 'status', 'scheduled_at'),
        db.Index('ix_outbox_source', 'source_type', 'source_id'),
        db.Index('ix_outbox_event_user_created', 'event_id', 'user_id', 'created_at'),
        db.Index('ix_outbox_recipient', 'recipient'),
    )
