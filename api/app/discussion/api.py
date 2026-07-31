from flask import g, request
import flask_restful as restful
from flask_restful import reqparse

from app import db, LOGGER
from app.utils.auth import auth_required
from app.utils import errors
from app.utils.push import push_to_user
from app.discussion.repository import DiscussionRepository as repo
from app.attendance.repository import AttendanceRepository
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app.engagement.models import EngagementEvent
from app.profiles.models import MemberProfile

# Basic anti-spam: at most this many new messages per user per event in the window.
RATE_LIMIT_COUNT = 10
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_SUBJECT_LEN = 200
MAX_BODY_LEN = 10000


# ---------------- shared helpers ----------------

def _is_confirmed_guest(event_id, user_id):
    return AttendanceRepository.is_confirmed_guest(event_id, user_id)


def _is_moderator(user_id, event_id):
    # Comms officer OR event admin (is_comms_officer already returns True for admins).
    user = user_repository.get_by_id(user_id)
    return bool(user and user.is_comms_officer(event_id))


def _emit(event, user_id, event_type, metadata=None):
    """Best-effort engagement event. Never let analytics break a request."""
    try:
        db.session.add(EngagementEvent(
            organisation_id=event.organisation_id,
            event_id=event.id,
            user_id=user_id,
            event_type=event_type,
            event_metadata=metadata or {},
        ))
        db.session.commit()
    except Exception as e:  # noqa: BLE001
        LOGGER.warning('engagement emit failed (%s): %s', event_type, e)
        db.session.rollback()


def _author_block(user_id, event_id=None):
    # MemberProfile is global to the member (unique on user_id, no event_id) —
    # the "one identity, many events" principle. event_id is accepted but unused.
    user = user_repository.get_by_id(user_id)
    profile = (db.session.query(MemberProfile)
               .filter_by(user_id=user_id).first())
    return {
        'user_id': user_id,
        'firstname': user.firstname if user else '',
        'lastname': user.lastname if user else '',
        'photo_url': profile.photo_url if profile else None,
    }


def _serialize_message(msg, current_user_id, is_moderator):
    is_own = (msg.user_id == current_user_id)
    body = msg.body_markdown
    if msg.is_deleted:
        body = None  # client renders a tombstone; never leak deleted content
    return {
        'id': msg.id,
        'thread_id': msg.thread_id,
        'is_root': msg.parent_message_id is None,
        'author': _author_block(msg.user_id, msg.event_id),
        'body_markdown': body,
        'is_deleted': msg.is_deleted,
        'deleted_by': msg.deleted_by,
        'edited_at': msg.edited_at.isoformat() + 'Z' if msg.edited_at else None,
        'created_at': msg.created_at.isoformat() + 'Z',
        'can_edit': is_own and not msg.is_deleted,
        'can_delete': (is_own or is_moderator) and not msg.is_deleted,
    }


def _serialize_thread_summary(thread, current_user_id):
    root = repo.get_root_message(thread.id)
    preview = ''
    subject = thread.subject
    if root and not root.is_deleted:
        preview = (root.body_markdown or '')[:140]
    sub = repo.get_subscription(thread.id, current_user_id)
    is_subscribed = bool(sub and sub.subscribed)
    read = repo.get_read(thread.id, current_user_id)
    unread = bool(read is None or thread.last_activity_at > read.last_read_at)
    space = repo.get_space(thread.space_id)
    return {
        'id': thread.id,
        'event_id': thread.event_id,
        'space_id': thread.space_id,
        'space_name': space.name if space else None,
        'subject': subject,
        'preview': preview,
        'author': _author_block(thread.created_by_user_id, thread.event_id),
        'reply_count': repo.reply_count(thread.id),
        'is_pinned': thread.is_pinned,
        'last_activity_at': thread.last_activity_at.isoformat() + 'Z',
        'created_at': thread.created_at.isoformat() + 'Z',
        'is_subscribed': is_subscribed,
        'unread': unread,
    }


def _notify_subscribers(thread, event, actor_user_id, actor_name):
    """Web-push new-reply notification to every subscriber except the actor."""
    subject = thread.subject or 'a discussion'
    url = '/{}/event-app/discussion/{}'.format(event.key, thread.id)
    for uid in repo.list_subscriber_user_ids(thread.id, exclude_user_id=actor_user_id):
        try:
            push_to_user(uid, {
                'title': subject,
                'body': '{} replied'.format(actor_name),
                'url': url,
                'tag': 'discussion-{}'.format(thread.id),  # coalesces multiple replies on one thread
            })
        except Exception as e:  # noqa: BLE001
            LOGGER.warning('discussion push failed for user %s (thread %s): %s', uid, thread.id, e)


def _rate_limited(user_id, event_id):
    return repo.count_recent_messages(user_id, event_id, RATE_LIMIT_WINDOW_SECONDS) >= RATE_LIMIT_COUNT


def _get_valid_space(space_id, event_id, require_open=False):
    """Look up a space, returning None if missing, wrong event, or (if require_open) archived."""
    space = repo.get_space(space_id)
    if not space or space.event_id != event_id:
        return None
    if require_open and space.is_archived:
        return None
    return space


# ---------------- Spaces ----------------

def _serialize_space(space, user_id):
    return {
        'id': space.id,
        'event_id': space.event_id,
        'name': space.name,
        'description': space.description,
        'subscribe_on_reply': space.subscribe_on_reply,
        'position': space.position,
        'is_archived': space.is_archived,
        'thread_count': repo.thread_count(space.id),
        'has_unread': repo.space_has_unread(space.id, user_id),
    }


class DiscussionSpaceListAPI(restful.Resource):
    """GET  /api/v1/discussion/space?event_id=   list spaces (any confirmed guest)
       POST /api/v1/discussion/space              create a space (comms officer)"""

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        include_archived = _is_moderator(user_id, event_id)
        spaces = repo.list_spaces(event_id, include_archived=include_archived)
        return [_serialize_space(s, user_id) for s in spaces]

    @auth_required
    def post(self):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        name = (body.get('name') or '').strip()
        description = (body.get('description') or '').strip()
        subscribe_on_reply = body.get('subscribe_on_reply', True)
        if not event_id or not name:
            return errors.MISSING_FIELDS
        if len(name) > MAX_SUBJECT_LEN:
            return errors.MISSING_FIELDS

        user_id = g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN
        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        space = repo.create_space(event_id, user_id, name, description, subscribe_on_reply)
        return _serialize_space(space, user_id), 201


class DiscussionSpaceAPI(restful.Resource):
    """GET    /api/v1/discussion/space/<id>?event_id=   space detail (any confirmed guest, incl. archived)
       PUT    /api/v1/discussion/space/<id>   edit a space (comms officer)
       DELETE /api/v1/discussion/space/<id>   archive (if non-empty) or delete (if empty)"""

    @auth_required
    def get(self, space_id):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN

        space = _get_valid_space(space_id, event_id)
        if not space:
            return {'message': 'Space not found'}, 404
        return _serialize_space(space, user_id), 200

    @auth_required
    def put(self, space_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN

        space = _get_valid_space(space_id, event_id)
        if not space:
            return {'message': 'Space not found'}, 404

        name = body.get('name')
        if name is not None:
            name = name.strip()
            if not name or len(name) > MAX_SUBJECT_LEN:
                return errors.MISSING_FIELDS
        description = body.get('description')
        if description is not None:
            description = description.strip()

        repo.update_space(
            space, name=name, description=description,
            subscribe_on_reply=body.get('subscribe_on_reply'), position=body.get('position'))
        return _serialize_space(space, user_id), 200

    @auth_required
    def delete(self, space_id):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN

        space = _get_valid_space(space_id, event_id)
        if not space:
            return {'message': 'Space not found'}, 404

        if repo.thread_count(space.id) > 0:
            repo.archive_space(space)
            return {'is_archived': True}, 200

        repo.delete_space(space)
        return {}, 204


# ---------------- Thread list + create ----------------

class DiscussionThreadListAPI(restful.Resource):
    """GET  /api/v1/discussion/thread?event_id=&space_id=   list threads in a space
       POST /api/v1/discussion/thread                        create a thread (+root message)"""

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        parser.add_argument('space_id', type=int, required=True)
        args = parser.parse_args()
        event_id, space_id, user_id = args['event_id'], args['space_id'], g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        if not _get_valid_space(space_id, event_id):
            return {'message': 'Space not found'}, 404
        threads = repo.list_threads(event_id, space_id)
        return [_serialize_thread_summary(t, user_id) for t in threads]

    @auth_required
    def post(self):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        space_id = body.get('space_id')
        body_markdown = (body.get('body_markdown') or '').strip()
        subject = (body.get('subject') or '').strip()
        if not event_id or not space_id or not body_markdown or not subject:
            return errors.MISSING_FIELDS
        if len(subject) > MAX_SUBJECT_LEN or len(body_markdown) > MAX_BODY_LEN:
            return errors.MISSING_FIELDS

        user_id = g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND
        space = _get_valid_space(space_id, event_id, require_open=True)
        if not space:
            return {'message': 'Space not found'}, 404
        if _rate_limited(user_id, event_id):
            return errors.TOO_MANY_REQUESTS

        thread, root = repo.create_thread(event_id, space_id, user_id, subject, body_markdown)
        if space.subscribe_on_reply:
            repo.auto_subscribe(thread.id, user_id)
        repo.mark_read(thread.id, user_id)  # the author has necessarily "seen" their own post
        _emit(event, user_id, 'thread_created', {'thread_id': thread.id})
        return {'thread_id': thread.id, 'message_id': root.id}, 201


# ---------------- Thread detail + reply ----------------

class DiscussionThreadDetailAPI(restful.Resource):
    """GET /api/v1/discussion/thread/<id>?event_id=   thread + messages (marks read)"""

    @auth_required
    def get(self, thread_id):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        thread = repo.get_thread(thread_id)
        if not thread or thread.event_id != event_id:
            return {'message': 'Thread not found'}, 404

        is_mod = _is_moderator(user_id, event_id)
        messages = repo.list_messages(thread_id)
        space = repo.get_space(thread.space_id)
        repo.mark_read(thread_id, user_id)  # in-app "inbox" read tracking
        return {
            'id': thread.id,
            'space_id': thread.space_id,
            'space_name': space.name if space else None,
            'subject': thread.subject,
            'is_pinned': thread.is_pinned,
            'is_subscribed': repo.is_subscribed(thread_id, user_id),
            'is_moderator': is_mod,
            'created_at': thread.created_at.isoformat() + 'Z',
            'messages': [_serialize_message(m, user_id, is_mod) for m in messages],
        }


class DiscussionReplyAPI(restful.Resource):
    """POST /api/v1/discussion/thread/<id>/reply   add a reply (auto-subscribe + notify)"""

    @auth_required
    def post(self, thread_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        body_markdown = (body.get('body_markdown') or '').strip()
        if not event_id or not body_markdown:
            return errors.MISSING_FIELDS
        if len(body_markdown) > MAX_BODY_LEN:
            return errors.MISSING_FIELDS

        user_id = g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        thread = repo.get_thread(thread_id)
        if not thread or thread.event_id != event_id:
            return {'message': 'Thread not found'}, 404
        event = event_repository.get_by_id(event_id)
        if _rate_limited(user_id, event_id):
            return errors.TOO_MANY_REQUESTS

        reply = repo.create_reply(thread, user_id, body_markdown)
        space = repo.get_space(thread.space_id)
        if space.subscribe_on_reply:
            repo.auto_subscribe(thread.id, user_id)
        repo.mark_read(thread.id, user_id)  # replying bumps last_activity_at; don't self-mark unread

        actor = user_repository.get_by_id(user_id)
        actor_name = '{} {}'.format(actor.firstname, actor.lastname) if actor else 'Someone'
        _notify_subscribers(thread, event, user_id, actor_name)
        _emit(event, user_id, 'reply_posted', {'thread_id': thread.id})
        return {'message_id': reply.id}, 201


# ---------------- Edit / delete a message ----------------

class DiscussionMessageAPI(restful.Resource):
    """PUT    /api/v1/discussion/message/<id>   edit own message
       DELETE /api/v1/discussion/message/<id>   delete own (author) or any (moderator)"""

    @auth_required
    def put(self, message_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        body_markdown = (body.get('body_markdown') or '').strip()
        if not event_id or not body_markdown:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']

        msg = repo.get_message(message_id)
        if not msg or msg.event_id != event_id:
            return {'message': 'Message not found'}, 404
        if msg.user_id != user_id:          # only the author may edit
            return errors.FORBIDDEN
        if msg.is_deleted:
            return errors.FORBIDDEN

        repo.edit_message(msg, body_markdown)
        return {'id': msg.id, 'edited_at': msg.edited_at.isoformat() + 'Z'}, 200

    @auth_required
    def delete(self, message_id):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        parser.add_argument('reason', type=str, required=False)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']

        msg = repo.get_message(message_id)
        if not msg or msg.event_id != event_id:
            return {'message': 'Message not found'}, 404
        if msg.is_deleted:
            return {}, 204  # idempotent

        is_author = (msg.user_id == user_id)
        is_mod = _is_moderator(user_id, event_id)
        if not (is_author or is_mod):
            return errors.FORBIDDEN

        deleted_by = 'author' if is_author else 'moderator'
        repo.soft_delete_message(msg, deleted_by, reason=args.get('reason'))

        if deleted_by == 'moderator':
            event = event_repository.get_by_id(event_id)
            _emit(event, user_id, 'message_moderated', {'message_id': msg.id, 'by_role': 'moderator'})
        return {}, 204


# ---------------- Report ----------------

class DiscussionReportAPI(restful.Resource):
    """POST /api/v1/discussion/message/<id>/report   report a message"""

    @auth_required
    def post(self, message_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        reason = (body.get('reason') or '').strip()
        if not event_id:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN

        msg = repo.get_message(message_id)
        if not msg or msg.event_id != event_id:
            return {'message': 'Message not found'}, 404

        existing = repo.get_report_by_reporter(message_id, user_id)
        if existing:
            return {'id': existing.id}, 200  # idempotent: already reported

        report = repo.create_report(message_id, event_id, user_id, reason)
        event = event_repository.get_by_id(event_id)
        _emit(event, user_id, 'message_reported',
              {'message_id': msg.id, 'reason': reason[:100]})
        return {'id': report.id}, 201


# ---------------- Subscription ----------------

class DiscussionSubscriptionAPI(restful.Resource):
    """POST /api/v1/discussion/thread/<id>/subscription  {subscribed: bool}  explicit (un)subscribe"""

    @auth_required
    def post(self, thread_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        subscribed = body.get('subscribed')
        if event_id is None or subscribed is None:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        thread = repo.get_thread(thread_id)
        if not thread or thread.event_id != event_id:
            return {'message': 'Thread not found'}, 404

        repo.set_subscription(thread_id, user_id, bool(subscribed))
        event = event_repository.get_by_id(event_id)
        _emit(event, user_id,
              'thread_subscribed' if subscribed else 'thread_unsubscribed',
              {'thread_id': thread_id, 'auto': False})
        return {'subscribed': bool(subscribed)}, 200


class DiscussionSubscriptionListAPI(restful.Resource):
    """GET /api/v1/discussion/subscription?event_id=   'My subscriptions' view, across every space"""

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN
        threads = repo.list_subscribed_threads(event_id, user_id)
        return [_serialize_thread_summary(t, user_id) for t in threads]


# ---------------- Moderator: report queue + pin ----------------

class DiscussionReportQueueAPI(restful.Resource):
    """GET /api/v1/discussion/report?event_id=   list open reports (moderator)"""

    @auth_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event_id', type=int, required=True)
        args = parser.parse_args()
        event_id, user_id = args['event_id'], g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN

        result = []
        for r in repo.list_open_reports(event_id):
            msg = repo.get_message(r.message_id)
            result.append({
                'report_id': r.id,
                'message_id': r.message_id,
                'thread_id': msg.thread_id if msg else None,
                'reason': r.reason,
                'reporter': _author_block(r.reporter_user_id, event_id),
                'message_excerpt': (msg.body_markdown[:200] if msg and not msg.is_deleted else None),
                'message_is_deleted': bool(msg and msg.is_deleted),
                'message_author': _author_block(msg.user_id, event_id) if msg else None,
                'created_at': r.created_at.isoformat() + 'Z',
            })
        return result


class DiscussionReportActionAPI(restful.Resource):
    """POST /api/v1/discussion/report/<id>/dismiss  {event_id}  dismiss a report (moderator)"""

    @auth_required
    def post(self, report_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN
        report = repo.get_report(report_id)
        if not report or report.event_id != event_id:
            return {'message': 'Report not found'}, 404
        repo.set_report_status(report, 'dismissed')
        return {}, 200


class DiscussionPinAPI(restful.Resource):
    """POST /api/v1/discussion/thread/<id>/pin  {event_id, pinned: bool}  (moderator, nice-to-have)"""

    @auth_required
    def post(self, thread_id):
        body = request.get_json() or {}
        event_id = body.get('event_id')
        pinned = body.get('pinned')
        if event_id is None or pinned is None:
            return errors.MISSING_FIELDS
        user_id = g.current_user['id']
        if not _is_moderator(user_id, event_id):
            return errors.FORBIDDEN
        thread = repo.get_thread(thread_id)
        if not thread or thread.event_id != event_id:
            return {'message': 'Thread not found'}, 404
        repo.set_pinned(thread, pinned)
        return {'is_pinned': thread.is_pinned}, 200
