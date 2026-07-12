from datetime import datetime

from app import db


class DiscussionThread(db.Model):
    __tablename__ = 'discussion_thread'
    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    is_pinned = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    # last_activity_at drives board ordering; bumped on every new reply.
    last_activity_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.Index('ix_discussion_thread_event_activity', 'event_id', 'last_activity_at'),
    )


class DiscussionMessage(db.Model):
    __tablename__ = 'discussion_message'
    id = db.Column(db.Integer(), primary_key=True)
    thread_id = db.Column(db.Integer(), db.ForeignKey('discussion_thread.id'), nullable=False)
    # event_id is denormalised (also on the thread) to keep moderation/rate-limit
    # queries simple, mirroring how `connection` carries event_id.
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    parent_message_id = db.Column(db.Integer(), db.ForeignKey('discussion_message.id'), nullable=True)
    body_markdown = db.Column(db.Text(), nullable=False)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    deleted_by = db.Column(db.String(16), nullable=True)     # 'author' | 'moderator'
    deleted_reason = db.Column(db.String(500), nullable=True)
    edited_at = db.Column(db.DateTime(), nullable=True)       # null = never edited
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.Index('ix_discussion_message_thread', 'thread_id', 'created_at'),
    )


class DiscussionSubscription(db.Model):
    __tablename__ = 'discussion_subscription'
    id = db.Column(db.Integer(), primary_key=True)
    thread_id = db.Column(db.Integer(), db.ForeignKey('discussion_thread.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    subscribed = db.Column(db.Boolean(), nullable=False, default=True)   # False = sticky unsubscribe
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('thread_id', 'user_id', name='uq_discussion_sub_thread_user'),
    )


class DiscussionRead(db.Model):
    """Per-user last-viewed marker for a thread, independent of subscription.

    Decoupled from DiscussionSubscription so viewing a thread (which should
    never implicitly subscribe you, per the "reading is not subscribing"
    rule) can still power an unread indicator for every thread, not just
    ones you're subscribed to.
    """
    __tablename__ = 'discussion_read'
    id = db.Column(db.Integer(), primary_key=True)
    thread_id = db.Column(db.Integer(), db.ForeignKey('discussion_thread.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    last_read_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('thread_id', 'user_id', name='uq_discussion_read_thread_user'),
    )


class DiscussionReport(db.Model):
    __tablename__ = 'discussion_report'
    id = db.Column(db.Integer(), primary_key=True)
    message_id = db.Column(db.Integer(), db.ForeignKey('discussion_message.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    reporter_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    reason = db.Column(db.String(1000), nullable=True)
    status = db.Column(db.String(16), nullable=False, default='open')   # 'open' | 'dismissed' | 'actioned'
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('message_id', 'reporter_user_id', name='uq_discussion_report_msg_reporter'),
    )
