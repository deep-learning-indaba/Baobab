"""What was sent to a person for an event - the backend for the admin's
per-user email history.

GET  /api/v1/events/<event_id>/users/<user_id>/emails
GET  /api/v1/events/<event_id>/users/<user_id>/emails/<message_id>
POST /api/v1/events/<event_id>/users/<user_id>/emails/<message_id>/resend

Only messages tied to that event are visible: organisation-level emails
(password resets, verification) are never shown to an event admin. Sensitive
messages never expose a body, and a body older than the retention period has
been cleared anyway.

A frontend should render body_html in a sandboxed iframe (sandbox="", no
scripts), never by injecting it into the page.
"""
from datetime import datetime, timedelta

import flask_restful as restful
from flask import request

from app import LOGGER, db
from app.documents.mixins import event_admin_required_from_path
from app.email_template.registry import EMAIL_TYPES
from app.outbox.api import is_scheduler_request
from app.outbox.models import OutboxChannel, OutboxMessage, OutboxStatus
from app.outbox.repository import OutboxRepository
from app.utils import errors
from config import EMAIL_BODY_RETENTION_DAYS


MAX_PER_PAGE = 100


def _iso(value):
    return value.isoformat() + 'Z' if value else None


def _template_name(key, language='en'):
    email_type = EMAIL_TYPES.get(key)
    if email_type is None:
        return key
    return email_type.name.get(language) or email_type.name['en']


def _attachment_names(message):
    payload = message.payload or {}
    specs = list(payload.get('attachments') or [])
    if payload.get('attachment'):
        specs.append(payload['attachment'])
    return [spec.get('filename') for spec in specs]


def serialize_summary(message, ui_language='en'):
    return {
        'id': message.id,
        'channel': message.channel,
        'created_at': _iso(message.created_at),
        'sent_at': _iso(message.sent_at),
        'status': message.status,
        'attempts': message.attempts,
        'last_error': message.last_error,
        'subject': message.subject,
        'template_key': message.template_key,
        'template_name': _template_name(message.template_key, ui_language) if message.template_key else None,
        'source_type': message.source_type,
        'source_id': message.source_id,
        'recipient': message.recipient,
        'language': message.language,
        'sensitive': message.sensitive,
        'content_available': not message.sensitive and message.body_purged_at is None,
        'attachments': _attachment_names(message),
    }


def serialize_detail(message, ui_language='en'):
    result = serialize_summary(message, ui_language)
    hidden = message.sensitive or message.body_purged_at is not None
    result.update({
        'body_html': None if hidden else message.body_html,
        'body_text': None if hidden else message.body_text,
        'sender_name': message.sender_name,
        'sender_email': message.sender_email,
        'reply_to': message.reply_to,
        'template_revision_id': message.template_revision_id,
        'body_purged_at': _iso(message.body_purged_at),
    })
    return result


def _messages_for(event_id, user_id):
    return (db.session.query(OutboxMessage)
            .filter(OutboxMessage.event_id == event_id, OutboxMessage.user_id == user_id))


def _find(event_id, user_id, message_id):
    return _messages_for(event_id, user_id).filter(OutboxMessage.id == message_id).first()


class UserEmailHistoryAPI(restful.Resource):

    @event_admin_required_from_path
    def get(self, event_id, user_id):
        channel = request.args.get('channel', OutboxChannel.EMAIL)
        try:
            page = max(1, int(request.args.get('page', 1)))
            per_page = min(MAX_PER_PAGE, max(1, int(request.args.get('per_page', 50))))
        except ValueError:
            return errors.MISSING_FIELDS
        ui_language = (request.args.get('language') or 'en')[:2]

        query = _messages_for(event_id, user_id)
        if channel != 'all':
            query = query.filter(OutboxMessage.channel == channel)
        total = query.count()
        messages = (query.order_by(OutboxMessage.created_at.desc(), OutboxMessage.id.desc())
                    .offset((page - 1) * per_page).limit(per_page).all())
        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'messages': [serialize_summary(m, ui_language) for m in messages],
        }, 200


class UserEmailDetailAPI(restful.Resource):

    @event_admin_required_from_path
    def get(self, event_id, user_id, message_id):
        message = _find(event_id, user_id, message_id)
        if message is None:
            return errors.EMAIL_MESSAGE_NOT_FOUND
        return serialize_detail(message, (request.args.get('language') or 'en')[:2]), 200


class UserEmailResendAPI(restful.Resource):
    """Queues an exact copy of a previous email - same content, same
    attachments. Refused for sensitive emails (their links may have expired or
    been used, and their bodies are not kept) and for ones whose content has
    been cleared."""

    @event_admin_required_from_path
    def post(self, event_id, user_id, message_id):
        message = _find(event_id, user_id, message_id)
        if message is None or message.channel != OutboxChannel.EMAIL:
            return errors.EMAIL_MESSAGE_NOT_FOUND
        if message.sensitive or message.body_purged_at is not None or message.body_html is None:
            return errors.EMAIL_CONTENT_UNAVAILABLE

        now = datetime.utcnow()
        copy = OutboxMessage(
            organisation_id=message.organisation_id, event_id=message.event_id, user_id=message.user_id,
            channel=message.channel, recipient=message.recipient, subject=message.subject,
            body_text=message.body_text, body_html=message.body_html, payload=message.payload,
            sender_name=message.sender_name, sender_email=message.sender_email, reply_to=message.reply_to,
            template_key=message.template_key, template_revision_id=message.template_revision_id,
            language=message.language, sensitive=False, status=OutboxStatus.PENDING, attempts=0,
            created_at=now, scheduled_at=now, source_type='resend', source_id=message.id,
        )
        db.session.add(copy)
        db.session.commit()
        return serialize_summary(copy), 201


class EmailRetentionWorkerAPI(restful.Resource):
    """GET|POST /api/v1/tasks/email-retention - clear the content of messages
    older than EMAIL_BODY_RETENTION_DAYS. Driven daily by App Engine cron;
    works in chunks so a large first run spreads over several days rather than
    one long request."""

    def _run(self):
        if not is_scheduler_request():
            return errors.FORBIDDEN
        cutoff = datetime.utcnow() - timedelta(days=EMAIL_BODY_RETENTION_DAYS)
        purged = OutboxRepository.purge_bodies_older_than(cutoff)
        db.session.commit()
        LOGGER.info('Email retention: cleared %s message bodies older than %s', purged, cutoff)
        return {'purged': purged}, 200

    def get(self):
        return self._run()

    def post(self):
        return self._run()
