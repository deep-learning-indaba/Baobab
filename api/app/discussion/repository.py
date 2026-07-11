from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.discussion.models import (
    DiscussionThread, DiscussionMessage, DiscussionSubscription, DiscussionReport, DiscussionRead,
)


class DiscussionRepository:

    # ---------- Threads ----------

    @staticmethod
    def list_threads(event_id):
        """Board view: pinned first, then most-recent-activity first."""
        return (db.session.query(DiscussionThread)
                .filter(DiscussionThread.event_id == event_id)
                .order_by(DiscussionThread.is_pinned.desc(),
                          DiscussionThread.last_activity_at.desc())
                .all())

    @staticmethod
    def get_thread(thread_id):
        return db.session.query(DiscussionThread).get(thread_id)

    @staticmethod
    def create_thread(event_id, user_id, subject, body_markdown):
        """Create a thread and its root message atomically. Returns (thread, root_message)."""
        now = datetime.utcnow()
        thread = DiscussionThread(
            event_id=event_id, created_by_user_id=user_id,
            subject=(subject or None), created_at=now, last_activity_at=now,
        )
        db.session.add(thread)
        db.session.flush()  # need thread.id

        root = DiscussionMessage(
            thread_id=thread.id, event_id=event_id, user_id=user_id,
            parent_message_id=None, body_markdown=body_markdown, created_at=now,
        )
        db.session.add(root)
        db.session.commit()
        return thread, root

    @staticmethod
    def set_pinned(thread, pinned):
        thread.is_pinned = bool(pinned)
        db.session.commit()

    # ---------- Messages ----------

    @staticmethod
    def get_message(message_id):
        return db.session.query(DiscussionMessage).get(message_id)

    @staticmethod
    def list_messages(thread_id):
        return (db.session.query(DiscussionMessage)
                .filter(DiscussionMessage.thread_id == thread_id)
                .order_by(DiscussionMessage.created_at.asc())
                .all())

    @staticmethod
    def get_root_message(thread_id):
        return (db.session.query(DiscussionMessage)
                .filter(DiscussionMessage.thread_id == thread_id,
                        DiscussionMessage.parent_message_id.is_(None))
                .order_by(DiscussionMessage.created_at.asc())
                .first())

    @staticmethod
    def reply_count(thread_id):
        """Non-deleted replies (excludes the root message)."""
        return (db.session.query(func.count(DiscussionMessage.id))
                .filter(DiscussionMessage.thread_id == thread_id,
                        DiscussionMessage.parent_message_id.isnot(None),
                        DiscussionMessage.is_deleted.is_(False))
                .scalar())

    @staticmethod
    def create_reply(thread, user_id, body_markdown):
        now = datetime.utcnow()
        root = DiscussionRepository.get_root_message(thread.id)
        reply = DiscussionMessage(
            thread_id=thread.id, event_id=thread.event_id, user_id=user_id,
            parent_message_id=(root.id if root else None),
            body_markdown=body_markdown, created_at=now,
        )
        db.session.add(reply)
        thread.last_activity_at = now
        db.session.commit()
        return reply

    @staticmethod
    def edit_message(message, body_markdown):
        message.body_markdown = body_markdown
        message.edited_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def soft_delete_message(message, deleted_by, reason=None):
        message.is_deleted = True
        message.deleted_by = deleted_by            # 'author' | 'moderator'
        message.deleted_reason = reason
        db.session.commit()

    @staticmethod
    def count_recent_messages(user_id, event_id, seconds):
        """For basic anti-spam rate limiting."""
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return (db.session.query(func.count(DiscussionMessage.id))
                .filter(DiscussionMessage.user_id == user_id,
                        DiscussionMessage.event_id == event_id,
                        DiscussionMessage.created_at > cutoff)
                .scalar())

    # ---------- Subscriptions ----------

    @staticmethod
    def get_subscription(thread_id, user_id):
        return (db.session.query(DiscussionSubscription)
                .filter_by(thread_id=thread_id, user_id=user_id)
                .first())

    @staticmethod
    def set_subscription(thread_id, user_id, subscribed):
        """Explicit subscribe/unsubscribe (upsert). Returns the row."""
        sub = DiscussionRepository.get_subscription(thread_id, user_id)
        if sub:
            sub.subscribed = subscribed
        else:
            sub = DiscussionSubscription(thread_id=thread_id, user_id=user_id, subscribed=subscribed)
            db.session.add(sub)
        db.session.commit()
        return sub

    @staticmethod
    def auto_subscribe(thread_id, user_id):
        """Auto-subscribe on post/reply, but respect a sticky (explicit) unsubscribe.

        - no row        -> create subscribed=True
        - subscribed    -> no change
        - unsubscribed  -> DO NOTHING (sticky; user opted out)
        """
        sub = DiscussionRepository.get_subscription(thread_id, user_id)
        if sub is None:
            db.session.add(DiscussionSubscription(thread_id=thread_id, user_id=user_id, subscribed=True))
            db.session.commit()
        # if a row exists (subscribed True or sticky-False), leave it as-is.

    @staticmethod
    def is_subscribed(thread_id, user_id):
        sub = DiscussionRepository.get_subscription(thread_id, user_id)
        return bool(sub and sub.subscribed)

    @staticmethod
    def list_subscriber_user_ids(thread_id, exclude_user_id=None):
        q = (db.session.query(DiscussionSubscription.user_id)
             .filter(DiscussionSubscription.thread_id == thread_id,
                     DiscussionSubscription.subscribed.is_(True)))
        ids = [row.user_id for row in q.all()]
        if exclude_user_id is not None:
            ids = [i for i in ids if i != exclude_user_id]
        return ids

    @staticmethod
    def list_subscribed_threads(event_id, user_id):
        return (db.session.query(DiscussionThread)
                .join(DiscussionSubscription,
                      DiscussionSubscription.thread_id == DiscussionThread.id)
                .filter(DiscussionThread.event_id == event_id,
                        DiscussionSubscription.user_id == user_id,
                        DiscussionSubscription.subscribed.is_(True))
                .order_by(DiscussionThread.last_activity_at.desc())
                .all())

    @staticmethod
    def get_read(thread_id, user_id):
        return (db.session.query(DiscussionRead)
                .filter_by(thread_id=thread_id, user_id=user_id)
                .first())

    @staticmethod
    def mark_read(thread_id, user_id):
        """Upsert the per-user last-viewed marker for a thread.

        Decoupled from subscription (viewing a thread never implicitly
        subscribes you), so this powers the unread indicator for every
        thread, not just ones the user is subscribed to.
        """
        now = datetime.utcnow()
        read = DiscussionRepository.get_read(thread_id, user_id)
        if read:
            read.last_read_at = now
        else:
            db.session.add(DiscussionRead(thread_id=thread_id, user_id=user_id, last_read_at=now))
        db.session.commit()

    # ---------- Reports ----------

    @staticmethod
    def get_report_by_reporter(message_id, reporter_user_id):
        return (db.session.query(DiscussionReport)
                .filter_by(message_id=message_id, reporter_user_id=reporter_user_id)
                .first())

    @staticmethod
    def create_report(message_id, event_id, reporter_user_id, reason):
        report = DiscussionReport(
            message_id=message_id, event_id=event_id,
            reporter_user_id=reporter_user_id, reason=(reason or None),
        )
        db.session.add(report)
        db.session.commit()
        return report

    @staticmethod
    def get_report(report_id):
        return db.session.query(DiscussionReport).get(report_id)

    @staticmethod
    def list_open_reports(event_id):
        return (db.session.query(DiscussionReport)
                .filter(DiscussionReport.event_id == event_id,
                        DiscussionReport.status == 'open')
                .order_by(DiscussionReport.created_at.asc())
                .all())

    @staticmethod
    def set_report_status(report, status):
        report.status = status      # 'dismissed' | 'actioned'
        db.session.commit()
