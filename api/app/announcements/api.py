import html
from datetime import datetime

import markdown as md_lib
from flask import g, request
import flask_restful as restful
from flask_restful import reqparse

from app import db, LOGGER
from app.utils.auth import auth_required
from app.utils import errors
from app.utils.emailer import resolve_sender
from app.utils.push import push_to_user
from app.announcements.models import Announcement, AnnouncementTranslation, AnnouncementReceipt, PushSubscription
from app.announcements.repository import AnnouncementRepository
from app.attendance.repository import AttendanceRepository, CheckinRepository
from app.outbox.models import OutboxChannel, OutboxMessage, OutboxStatus
from app.outbox.repository import OutboxRepository
from app.tags.repository import TagRepository as tag_repository
from app.users.models import AppUser
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository


#: Identifies announcement messages in the outbox.
OUTBOX_SOURCE_TYPE = 'announcement'


def _is_comms_officer(user_id, event_id):
    user = user_repository.get_by_id(user_id)
    return user and user.is_comms_officer(event_id)


def _primary_language(event):
    """The organisation's first configured language, used as the mandatory
    translation when none is specified — organisations aren't all English-first."""
    languages = event.organisation.languages if event and event.organisation else None
    return languages[0]['code'] if languages else 'en'


def _translations_for(ann):
    """All translations of an announcement, ordered so the first is the fallback."""
    return (db.session.query(AnnouncementTranslation)
            .filter_by(announcement_id=ann.id)
            .order_by(AnnouncementTranslation.id)
            .all())


def _pick_translation(translations, language):
    """Return (title, body_markdown) for the given language, falling back to
    whichever translation exists rather than assuming English was provided."""
    by_lang = {t.language: t for t in translations}
    t = by_lang.get(language) or (translations[0] if translations else None)
    if t:
        return t.title, t.body_markdown
    return '', ''


def _resolve_translation(ann, language):
    return _pick_translation(_translations_for(ann), language)


def _serialize_announcement(ann, receipt=None, language='en'):
    title, body = _resolve_translation(ann, language)
    return {
        'id': ann.id,
        'event_id': ann.event_id,
        'title': title,
        'body_markdown': body,
        'sent_at': ann.sent_at.isoformat() + 'Z' if ann.sent_at else None,
        'expiry_at': ann.expiry_at.isoformat() + 'Z' if ann.expiry_at else None,
        'read': receipt.opened_at is not None if receipt else False,
        'delivered_at': receipt.delivered_at.isoformat() + 'Z' if receipt and receipt.delivered_at else None,
    }


def _was_sent_as_critical(announcement_id):
    """Whether an announcement was emailed, judged from what it queued.

    Only needed for announcements sent before the flag was stored on the row.
    """
    return db.session.query(
        db.session.query(OutboxMessage)
        .filter(OutboxMessage.source_type == OUTBOX_SOURCE_TYPE,
                OutboxMessage.source_id == announcement_id,
                OutboxMessage.channel == OutboxChannel.EMAIL)
        .exists()
    ).scalar()


def _delivery_summary(status_counts):
    """Flatten per-status outbox counts into what the admin dashboard reports.

    'pending' covers messages awaiting a first attempt and ones backing off after
    a failure, since from an organiser's point of view both are still in flight.
    """
    return {
        'queued': status_counts.get(OutboxStatus.PENDING, 0) + status_counts.get(OutboxStatus.SENDING, 0),
        'sent': status_counts.get(OutboxStatus.SENT, 0),
        'skipped': status_counts.get(OutboxStatus.SKIPPED, 0),
        'failed': status_counts.get(OutboxStatus.FAILED, 0),
    }


VALID_AUDIENCES = ('checked_in', 'guest_list')


def _audience_user_ids(event, target_audience, tag_id):
    if target_audience == 'guest_list':
        user_ids = AttendanceRepository.get_all_guest_user_ids_for_event(event.id)
    else:
        user_ids = list({row.user_id for row in CheckinRepository.list_for_event(event.id)})

    if tag_id:
        tagged_user_ids = AttendanceRepository.get_user_ids_with_tag(event.id, tag_id)
        user_ids = [uid for uid in user_ids if uid in tagged_user_ids]

    # An accepted offer and an invited guest entry can both name the same person.
    return list(dict.fromkeys(user_ids))


def _enqueue(ann, event, critical, target_audience='checked_in', tag_id=None):
    """Put the announcement in the target audience's inboxes and queue push (+
    email if critical) for the outbox worker to deliver.

    Nothing is transmitted here. A guest list runs to several thousand people,
    and a per-recipient SMTP session or Web Push call takes far longer than a
    request is allowed to run, so the request only writes rows.

    target_audience:
      'checked_in' — only users who have physically checked in (default)
      'guest_list' — all confirmed guests (accepted offer or invited guest)

    tag_id, if given, further restricts the audience to guests whose Offer or
    InvitedGuest entry carries that tag (e.g. only guests with an
    accommodation or travel tag).

    Returns (audience_count, queued_count).
    """
    user_ids = _audience_user_ids(event, target_audience, tag_id)
    if not user_ids:
        return 0, 0

    users = db.session.query(AppUser).filter(AppUser.id.in_(user_ids)).all()
    if not users:
        return 0, 0

    organisation = event.organisation
    # Resolved now, while the organisation is in scope, because the worker that
    # sends these has no organisation to fall back on.
    sender_name, sender_email = resolve_sender(organisation.name, organisation.email_from)
    default_language = _primary_language(event)
    translations = _translations_for(ann)
    push_url = '/{}/event-app/announcements/{}'.format(event.key, ann.id)
    now = datetime.utcnow()

    already_receipted = {row[0] for row in (
        db.session.query(AnnouncementReceipt.user_id)
        .filter(AnnouncementReceipt.announcement_id == ann.id)
        .all())}

    # Rendering per language rather than per user: an event has a handful of
    # languages and thousands of guests.
    rendered = {}

    def render(language):
        if language not in rendered:
            title, body = _pick_translation(translations, language)
            rendered[language] = {
                'title': title,
                'body': body,
                # The title is free text, so it has to be escaped before going into
                # the heading; markdown already escapes what it renders.
                'body_html': '<h2>{}</h2>{}'.format(html.escape(title), md_lib.markdown(body)),
                'push_body': body[:120] + ('...' if len(body) > 120 else ''),
            }
        return rendered[language]

    receipts = []
    messages = []
    for user in users:
        if user.id not in already_receipted:
            receipts.append({
                'announcement_id': ann.id,
                'user_id': user.id,
                'delivered_at': now,
                'channel': 'inbox',
            })

        content = render((user.user_primaryLanguage or default_language)[:2])

        common = {
            'organisation_id': organisation.id,
            'event_id': event.id,
            'user_id': user.id,
            'source_type': OUTBOX_SOURCE_TYPE,
            'source_id': ann.id,
            'status': OutboxStatus.PENDING,
            'attempts': 0,
            'created_at': now,
            'scheduled_at': now,
            'subject': content['title'],
        }

        messages.append(dict(
            common,
            channel=OutboxChannel.PUSH,
            body_text=content['push_body'],
            payload={
                'title': content['title'],
                'body': content['push_body'],
                'url': push_url,
                'tag': 'ann-{}'.format(ann.id),
            },
        ))

        if critical and user.email:
            messages.append(dict(
                common,
                channel=OutboxChannel.EMAIL,
                recipient=user.email,
                body_text='{}\n\n{}'.format(content['title'], content['body']),
                body_html=content['body_html'],
                sender_name=sender_name,
                sender_email=sender_email,
            ))

    if receipts:
        db.session.bulk_insert_mappings(AnnouncementReceipt, receipts)
    queued = OutboxRepository.enqueue_many(messages, OUTBOX_SOURCE_TYPE, ann.id)

    db.session.commit()
    LOGGER.info('Announcement %s queued %s messages for %s recipients', ann.id, queued, len(users))
    return len(users), queued


class AnnouncementListAPI(restful.Resource):
    """GET /api/v1/announcement — inbox for confirmed guest.
       POST /api/v1/announcement — create + dispatch (comms officer)."""

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()
        event_id = args['event_id']
        language = args['language'][:2] if args['language'] else 'en'
        user_id = g.current_user['id']

        if not AttendanceRepository.is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN

        # Lazily backfill receipts for late check-ins
        AnnouncementRepository.backfill_receipts_for_user(event_id, user_id)

        receipts = {r.announcement_id: r for r in AnnouncementRepository.get_receipts_for_user(event_id, user_id)}
        announcements = AnnouncementRepository.list_all_for_event(event_id)

        return [_serialize_announcement(ann, receipts.get(ann.id), language) for ann in announcements]

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_comms_officer(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        translations_in = body.get('translations') or []
        primary_language = _primary_language(event)
        primary_trans = next((t for t in translations_in if t.get('language') == primary_language), None)
        if not primary_trans or not primary_trans.get('title'):
            return errors.MISSING_FIELDS

        expiry_at = None
        if body.get('expiry_at'):
            try:
                expiry_at = datetime.fromisoformat(body['expiry_at'].rstrip('Z'))
            except (ValueError, AttributeError):
                return errors.MISSING_FIELDS

        translations = [
            (t['language'], t['title'], t.get('body_markdown', ''))
            for t in translations_in
            if t.get('language') and t.get('title')
        ]

        target_audience = body.get('target_audience', 'checked_in')
        if target_audience not in VALID_AUDIENCES:
            return errors.MISSING_FIELDS

        tag_id = body.get('tag_id')
        if tag_id is not None:
            tag = tag_repository.get_by_id(tag_id)
            if not tag or tag.event_id != event_id:
                return errors.TAG_NOT_FOUND

        critical = bool(body.get('critical', False))

        ann = AnnouncementRepository.create(
            event_id, g.current_user['id'], expiry_at, translations,
            critical=critical, target_audience=target_audience, tag_id=tag_id)

        audience, queued = _enqueue(ann, event, critical, target_audience, tag_id)

        return {'id': ann.id, 'audience_count': audience, 'queued_count': queued}, 201


class AnnouncementResendAPI(restful.Resource):
    """POST /api/v1/announcement/<id>/resend — re-reach an announcement's audience.

    Two things an organiser means by "resend", both done here:
      * anyone in the audience who was never queued — because a send was cut
        short, or because they joined the guest list afterwards — is queued now
      * messages that failed, or that had no device to push to, are tried again

    Nobody who already received a message is queued a second time: enqueueing
    skips recipients that already have a row for this announcement, and retrying
    deliberately excludes 'sent'. So this is safe to press more than once.

    The audience defaults to the one recorded when the announcement was sent, and
    can be widened via target_audience/tag_id/critical in the body — useful for
    following a checked-in-only announcement with one to the full guest list.
    """

    @auth_required
    def post(self, announcement_id):
        body = request.get_json() or {}

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_comms_officer(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        ann = AnnouncementRepository.get_by_id(announcement_id)
        if not ann or ann.event_id != event_id:
            return {'message': 'Announcement not found'}, 404

        target_audience = body.get('target_audience') or ann.target_audience or 'checked_in'
        if target_audience not in VALID_AUDIENCES:
            return errors.MISSING_FIELDS

        tag_id = body.get('tag_id', ann.tag_id)
        if tag_id is not None:
            tag = tag_repository.get_by_id(tag_id)
            if not tag or tag.event_id != event_id:
                return errors.TAG_NOT_FOUND

        if 'critical' in body:
            critical = bool(body['critical'])
        elif ann.critical is not None:
            critical = ann.critical
        else:
            # Sent before the flag was recorded: an email row in the outbox is the
            # only remaining evidence that it went out as critical.
            critical = _was_sent_as_critical(ann.id)

        retried = OutboxRepository.retry_terminal(OUTBOX_SOURCE_TYPE, ann.id)
        audience, queued = _enqueue(ann, event, critical, target_audience, tag_id)

        LOGGER.info('Announcement %s resent: %s newly queued, %s retried', ann.id, queued, retried)
        return {
            'id': ann.id,
            'audience_count': audience,
            'queued_count': queued,
            'retried_count': retried,
        }, 200


class AnnouncementActiveAPI(restful.Resource):
    """GET /api/v1/announcement/active?event_id= — non-expired, for home page banner."""

    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()
        language = args['language'][:2] if args['language'] else 'en'

        announcements = AnnouncementRepository.list_active(args['event_id'])
        return [_serialize_announcement(ann, None, language) for ann in announcements]


class AnnouncementAdminAPI(restful.Resource):
    """GET /api/v1/announcement/admin?event_id= — sent list with delivery stats (comms officer)."""

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()
        event_id = args['event_id']
        language = args['language'][:2] if args['language'] else 'en'

        if not _is_comms_officer(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        announcements = AnnouncementRepository.list_all_for_event(event_id)
        receipt_counts = AnnouncementRepository.receipt_counts_for_event(event_id)
        delivery = OutboxRepository.status_counts(
            OUTBOX_SOURCE_TYPE, [ann.id for ann in announcements])

        result = []
        for ann in announcements:
            counts = receipt_counts.get(ann.id, {})
            s = _serialize_announcement(ann, None, language)
            s['delivered_count'] = counts.get('delivered', 0)
            s['opened_count'] = counts.get('opened', 0)
            s['email_delivery'] = _delivery_summary(
                delivery.get(ann.id, {}).get(OutboxChannel.EMAIL, {}))
            s['push_delivery'] = _delivery_summary(
                delivery.get(ann.id, {}).get(OutboxChannel.PUSH, {}))
            s['critical'] = ann.critical
            s['target_audience'] = ann.target_audience
            result.append(s)
        return result


class AnnouncementDetailAPI(restful.Resource):
    """GET /api/v1/announcement/<id> — detail, marks opened.
       DELETE /api/v1/announcement/<id> — remove (comms officer)."""

    @auth_required
    def get(self, announcement_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()
        event_id = args['event_id']
        language = args['language'][:2] if args['language'] else 'en'
        user_id = g.current_user['id']

        if not AttendanceRepository.is_confirmed_guest(event_id, user_id):
            return errors.FORBIDDEN

        ann = AnnouncementRepository.get_by_id(announcement_id)
        if not ann or ann.event_id != event_id:
            return {'message': 'Announcement not found'}, 404

        receipt = AnnouncementRepository.get_receipt(announcement_id, user_id)
        if receipt and not receipt.opened_at:
            receipt.opened_at = datetime.utcnow()
            db.session.commit()

        return _serialize_announcement(ann, receipt, language)

    @auth_required
    def delete(self, announcement_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']

        if not _is_comms_officer(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        ann = AnnouncementRepository.get_by_id(announcement_id)
        if not ann or ann.event_id != event_id:
            return {'message': 'Announcement not found'}, 404

        # Drop anything still queued: deleting an announcement should stop it
        # going out, not just hide it from the dashboard.
        OutboxRepository.delete_for_source(OUTBOX_SOURCE_TYPE, ann.id)
        AnnouncementRepository.delete(ann)
        return {}, 204


class PushSubscriptionAPI(restful.Resource):
    """POST /api/v1/push-subscription — upsert subscription.
       DELETE /api/v1/push-subscription — remove subscription."""

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        endpoint = body.get('endpoint')
        keys = body.get('keys') or {}
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return errors.MISSING_FIELDS

        user_id = g.current_user['id']
        existing = db.session.query(PushSubscription).filter_by(endpoint=endpoint).first()
        if existing:
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            existing.user_agent = body.get('user_agent', '')
        else:
            sub = PushSubscription(
                user_id=user_id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=body.get('user_agent', ''),
            )
            db.session.add(sub)
        db.session.commit()
        return {}, 201

    @auth_required
    def delete(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        endpoint = body.get('endpoint')
        if not endpoint:
            return errors.MISSING_FIELDS

        sub = db.session.query(PushSubscription).filter_by(endpoint=endpoint).first()
        if sub and sub.user_id == g.current_user['id']:
            db.session.delete(sub)
            db.session.commit()
        return {}, 204


class PushSubscriptionTestAPI(restful.Resource):
    """POST /api/v1/push-subscription/test — send a test push to the current
    user's own devices and return diagnostics. Isolates the delivery path from
    the announcement audience/receipt logic, for debugging."""

    @auth_required
    def post(self):
        from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY
        user_id = g.current_user['id']
        result = push_to_user(user_id, {
            'title': 'Test notification',
            'body': 'If you can see this, push notifications are working.',
            'url': '/',
            'tag': 'push-test',
        })
        # Surface config so the client can spot a public/private key mismatch.
        result['vapid_private_key_configured'] = bool(VAPID_PRIVATE_KEY)
        result['vapid_public_key'] = VAPID_PUBLIC_KEY
        return result, 200
