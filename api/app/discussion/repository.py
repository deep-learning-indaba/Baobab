from datetime import datetime, timedelta

from sqlalchemy import and_, exists, func, not_, or_

from app import db
from app.discussion.models import (
    DiscussionThread, DiscussionMessage, DiscussionSubscription, DiscussionReport, DiscussionRead,
    DiscussionSpace, NO_SUBJECT_PLACEHOLDER,
)


class DiscussionRepository:

    # ---------- Spaces ----------

    @staticmethod
    def list_spaces(event_id, include_archived=False):
        q = db.session.query(DiscussionSpace).filter(DiscussionSpace.event_id == event_id)
        if not include_archived:
            q = q.filter(DiscussionSpace.is_archived.is_(False))
        return q.order_by(DiscussionSpace.position.asc(), DiscussionSpace.created_at.asc()).all()

    @staticmethod
    def get_space(space_id):
        return db.session.query(DiscussionSpace).get(space_id)

    @staticmethod
    def create_space(event_id, user_id, name, description, subscribe_on_reply, position=0):
        space = DiscussionSpace(
            event_id=event_id, created_by_user_id=user_id, name=name,
            description=(description or None), subscribe_on_reply=bool(subscribe_on_reply),
            position=position,
        )
        db.session.add(space)
        db.session.commit()
        return space

    @staticmethod
    def update_space(space, name=None, description=None, subscribe_on_reply=None, position=None):
        if name is not None:
            space.name = name
        if description is not None:
            space.description = (description or None)
        if subscribe_on_reply is not None:
            space.subscribe_on_reply = bool(subscribe_on_reply)
        if position is not None:
            space.position = position
        db.session.commit()
        return space

    @staticmethod
    def archive_space(space):
        space.is_archived = True
        db.session.commit()

    @staticmethod
    def delete_space(space):
        db.session.delete(space)
        db.session.commit()

    @staticmethod
    def thread_count(space_id):
        return (db.session.query(func.count(DiscussionThread.id))
                .filter(DiscussionThread.space_id == space_id)
                .scalar())

    @staticmethod
    def space_has_unread(space_id, user_id):
        """True if any thread in the space has newer activity than the user's read marker."""
        rows = (db.session.query(DiscussionThread.last_activity_at, DiscussionRead.last_read_at)
                .outerjoin(DiscussionRead,
                           (DiscussionRead.thread_id == DiscussionThread.id)
                           & (DiscussionRead.user_id == user_id))
                .filter(DiscussionThread.space_id == space_id)
                .all())
        return any(read_at is None or activity_at > read_at for activity_at, read_at in rows)

    # ---------- Threads ----------

    @staticmethod
    def _is_emptied_out_thread_clause():
        """A thread whose root post was deleted, never had a subject, and has
        no surviving (non-deleted) replies. Nothing remains worth showing on
        the board, so listing queries exclude threads matching this clause.
        """
        root_deleted = exists().where(and_(
            DiscussionMessage.thread_id == DiscussionThread.id,
            DiscussionMessage.parent_message_id.is_(None),
            DiscussionMessage.is_deleted.is_(True),
        ))
        has_active_reply = exists().where(and_(
            DiscussionMessage.thread_id == DiscussionThread.id,
            DiscussionMessage.parent_message_id.isnot(None),
            DiscussionMessage.is_deleted.is_(False),
        ))
        no_subject = or_(
            DiscussionThread.subject.is_(None),
            DiscussionThread.subject == '',
            DiscussionThread.subject == NO_SUBJECT_PLACEHOLDER,
        )
        return and_(root_deleted, no_subject, not_(has_active_reply))

    @staticmethod
    def list_threads(event_id, space_id):
        """Board view: pinned first, then most-recent-activity first."""
        return (db.session.query(DiscussionThread)
                .filter(DiscussionThread.event_id == event_id,
                        DiscussionThread.space_id == space_id)
                .filter(not_(DiscussionRepository._is_emptied_out_thread_clause()))
                .order_by(DiscussionThread.is_pinned.desc(),
                          DiscussionThread.last_activity_at.desc())
                .all())

    @staticmethod
    def get_thread(thread_id):
        return db.session.query(DiscussionThread).get(thread_id)

    @staticmethod
    def create_thread(event_id, space_id, user_id, subject, body_markdown):
        """Create a thread and its root message atomically. Returns (thread, root_message)."""
        now = datetime.utcnow()
        thread = DiscussionThread(
            event_id=event_id, space_id=space_id, created_by_user_id=user_id,
            subject=subject, created_at=now, last_activity_at=now,
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
                .filter(not_(DiscussionRepository._is_emptied_out_thread_clause()))
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

    # ---------- Event-level stats ----------

    @staticmethod
    def count_threads_for_event(event_id):
        return (db.session.query(func.count(DiscussionThread.id))
                .filter(DiscussionThread.event_id == event_id)
                .scalar())

    @staticmethod
    def count_replies_for_event(event_id):
        return (db.session.query(func.count(DiscussionMessage.id))
                .filter(
                    DiscussionMessage.event_id == event_id,
                    DiscussionMessage.parent_message_id.isnot(None),
                    DiscussionMessage.is_deleted.is_(False),
                )
                .scalar())

    @staticmethod
    def count_active_participants_for_event(event_id):
        return (db.session.query(func.count(func.distinct(DiscussionMessage.user_id)))
                .filter(
                    DiscussionMessage.event_id == event_id,
                    DiscussionMessage.is_deleted.is_(False),
                )
                .scalar())
