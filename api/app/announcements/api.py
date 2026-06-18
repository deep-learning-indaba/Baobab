from datetime import datetime

import markdown as md_lib
from flask import g, request
import flask_restful as restful
from flask_restful import reqparse

from app import db
from app.utils.auth import auth_required
from app.utils import errors
from app.utils.push import push_to_user
from app.utils.emailer import send_mail
from app.announcements.models import Announcement, AnnouncementTranslation, AnnouncementReceipt, PushSubscription
from app.announcements.repository import AnnouncementRepository
from app.attendance.repository import AttendanceRepository, CheckinRepository
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository


def _is_comms_officer(user_id, event_id):
    user = user_repository.get_by_id(user_id)
    return user and user.is_comms_officer(event_id)


def _resolve_translation(ann, language):
    """Return (title, body_markdown) for the given language, falling back to EN."""
    translations = db.session.query(AnnouncementTranslation).filter_by(announcement_id=ann.id).all()
    by_lang = {t.language: t for t in translations}
    t = by_lang.get(language) or by_lang.get('en')
    if t:
        return t.title, t.body_markdown
    return '', ''


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


def _dispatch(ann, event, critical):
    """Create receipts and send push (+ email if critical) to all checked-in attendees."""
    checked_in_rows = CheckinRepository.list_for_event(event.id)
    user_ids = list({row.user_id for row in checked_in_rows})
    now = datetime.utcnow()

    for uid in user_ids:
        existing = AnnouncementRepository.get_receipt(ann.id, uid)
        if existing:
            continue

        AnnouncementRepository.create_receipt(ann.id, uid, delivered_at=now, channel='inbox')
        db.session.flush()

        user = user_repository.get_by_id(uid)
        if not user:
            continue

        language = (user.user_primaryLanguage or 'en')[:2]
        title, body = _resolve_translation(ann, language)

        # Web Push — best-effort
        try:
            event_key = event.key
            push_url = '/{}/event-app/announcements/{}'.format(event_key, ann.id)
            push_to_user(uid, {
                'title': title,
                'body': body[:120] + ('...' if len(body) > 120 else ''),
                'url': push_url,
                'tag': 'ann-{}'.format(ann.id),
            })
        except Exception:
            pass

        # Email backstop — critical only
        if critical and user.email:
            try:
                body_html = md_lib.markdown(body)
                send_mail(
                    recipient=user.email,
                    subject=title,
                    body_html='<h2>{}</h2>{}'.format(title, body_html),
                    body_text='{}\n\n{}'.format(title, body),
                )
            except Exception:
                pass

    db.session.commit()


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

        translations_in = body.get('translations') or []
        en_trans = next((t for t in translations_in if t.get('language') == 'en'), None)
        if not en_trans or not en_trans.get('title'):
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

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        ann = AnnouncementRepository.create(event_id, g.current_user['id'], expiry_at, translations)

        critical = bool(body.get('critical', False))
        _dispatch(ann, event, critical)

        # Count audience for response
        audience = len({r.user_id for r in CheckinRepository.list_for_event(event_id)})
        return {'id': ann.id, 'audience_count': audience}, 201


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
        result = []
        for ann in announcements:
            s = _serialize_announcement(ann, None, language)
            s['delivered_count'] = AnnouncementRepository.count_delivered(ann.id)
            s['opened_count'] = AnnouncementRepository.count_opened(ann.id)
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
