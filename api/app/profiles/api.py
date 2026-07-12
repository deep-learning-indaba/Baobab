from flask import g, current_app
import flask_restful as restful
from flask_restful import reqparse

from app.profiles.models import MemberProfile
from app.profiles.repository import ProfileRepository as profile_repository
from app.profiles.repository import ConsentRepository as consent_repository
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.invitedGuest.repository import InvitedGuestRepository as invited_guest_repository
from app.tags.models import Tag, TagTranslation, TagType
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app.utils.auth import auth_required
from app.utils.errors import EVENT_NOT_FOUND, FORBIDDEN, NOT_A_GUEST, USER_NOT_FOUND
from app import db

CONSENT_VERSION = '2026-01'


def _profile_to_dict(user, profile):
    links = {}
    if profile and profile.links:
        for lnk in profile.links:
            links[lnk.link_type] = lnk.url

    interests = profile_repository.get_interests_for_user(user.id)

    data = {
        'user_id': user.id,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'affiliation': profile.affiliation if profile else None,
        'country': profile.country if profile else None,
        'email': user.email,
        'headline': profile.headline if profile else None,
        'about': profile.about if profile else None,
        'pronouns': profile.pronouns if profile else None,
        'name_pronunciation': profile.name_pronunciation if profile else None,
        'city': profile.city if profile else None,
        'photo_url': profile.photo_url if profile else None,
        'links': links,
        'visibility': profile.visibility if profile else 'community',
        'interests': interests,
    }
    return data


class ProfileAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        current_user_id = g.current_user['id']

        user = user_repository.get_by_id(current_user_id)
        if user is None:
            return USER_NOT_FOUND

        profile = profile_repository.get_or_create(current_user_id)
        return _profile_to_dict(user, profile), 200

    @auth_required
    def put(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=False)
        req_parser.add_argument('headline', type=str, required=False)
        req_parser.add_argument('about', type=str, required=False)
        req_parser.add_argument('pronouns', type=str, required=False)
        req_parser.add_argument('name_pronunciation', type=str, required=False)
        req_parser.add_argument('city', type=str, required=False)
        req_parser.add_argument('country', type=str, required=False)
        req_parser.add_argument('affiliation', type=str, required=False)
        req_parser.add_argument('photo_url', type=str, required=False)
        req_parser.add_argument('visibility', type=str, required=False)
        req_parser.add_argument('interest_ids', type=int, action='append', required=False)
        req_parser.add_argument('links', type=dict, required=False, location='json')
        args = req_parser.parse_args()
        current_user_id = g.current_user['id']

        user = user_repository.get_by_id(current_user_id)
        if user is None:
            return USER_NOT_FOUND

        profile = profile_repository.get_or_create(current_user_id)
        is_first_save = not any([
            profile.headline, profile.about, profile.pronouns,
            profile.city, profile.photo_url
        ])

        if args['headline'] is not None:
            profile.headline = args['headline']
        if args['about'] is not None:
            profile.about = args['about']
        if args['pronouns'] is not None:
            profile.pronouns = args['pronouns']
        if args['name_pronunciation'] is not None:
            profile.name_pronunciation = args['name_pronunciation']
        if args['city'] is not None:
            profile.city = args['city']
        if args['country'] is not None:
            profile.country = args['country']
        if args['affiliation'] is not None:
            profile.affiliation = args['affiliation']
        if args['photo_url'] is not None:
            profile.photo_url = args['photo_url']
        if args['visibility'] in ('community', 'hidden'):
            profile.visibility = args['visibility']

        db.session.commit()

        if args['interest_ids'] is not None:
            profile_repository.set_interests(current_user_id, args['interest_ids'])

        if args['links'] is not None:
            profile_repository.set_links(profile, args['links'])

        fields_filled = sum(1 for f in [
            profile.headline, profile.about, profile.pronouns,
            profile.city, profile.photo_url
        ] if f)
        if is_first_save and fields_filled > 0:
            pass  # engagement event hook: profile_confirmed

        return _profile_to_dict(user, profile), 200


class ProfileViewAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('user_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        if not attendance_repository.is_confirmed_guest(event_id, current_user_id):
            return NOT_A_GUEST

        target_user = user_repository.get_by_id(args['user_id'])
        if target_user is None:
            return USER_NOT_FOUND

        profile = profile_repository.get(args['user_id'])

        if profile and profile.visibility == 'hidden':
            invited_guest = invited_guest_repository.get_for_event_and_user(event_id, args['user_id'])
            role = invited_guest.role if invited_guest else 'General Attendee'
            return {
                'user_id': target_user.id,
                'firstname': target_user.firstname,
                'lastname': target_user.lastname,
                'role': role,
                'photo_url': profile.photo_url if profile else None,
                'hidden': True,
            }, 200

        invited_guest = invited_guest_repository.get_for_event_and_user(event_id, args['user_id'])
        role = invited_guest.role if invited_guest else 'General Attendee'
        data = _profile_to_dict(target_user, profile)
        data['role'] = role
        return data, 200


class ProfileListAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        current_user_id = g.current_user['id']

        if not attendance_repository.is_confirmed_guest(event_id, current_user_id):
            return NOT_A_GUEST

        pairs = profile_repository.list_community(event_id)
        result = []
        for user, profile in pairs:
            invited_guest = invited_guest_repository.get_for_event_and_user(event_id, user.id)
            role = invited_guest.role if invited_guest else 'General Attendee'
            data = _profile_to_dict(user, profile)
            data['role'] = role
            result.append(data)
        return result, 200


class ProfileInterestsAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()

        event = event_repository.get_by_id(args['event_id'])
        if event is None:
            return EVENT_NOT_FOUND

        tags = (db.session.query(Tag, TagTranslation)
                .outerjoin(TagTranslation, (TagTranslation.tag_id == Tag.id) & (TagTranslation.language == 'en'))
                .filter(Tag.event_id == args['event_id'], Tag.tag_type == TagType.INTEREST, Tag.active == True)
                .all())

        return [{'id': tag.id, 'name': tr.name if tr else str(tag.id)} for tag, tr in tags], 200

    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('name', type=str, required=True)
        args = req_parser.parse_args()
        event_id = args['event_id']
        name = args['name'].strip()[:80]

        event = event_repository.get_by_id(event_id)
        if event is None:
            return EVENT_NOT_FOUND

        normalised = name.lower()
        existing = (db.session.query(Tag, TagTranslation)
                    .join(TagTranslation, TagTranslation.tag_id == Tag.id)
                    .filter(
                        Tag.event_id == event_id,
                        Tag.tag_type == TagType.INTEREST,
                        db.func.lower(TagTranslation.name) == normalised,
                        TagTranslation.language == 'en',
                    ).first())
        if existing:
            tag, tr = existing
            return {'id': tag.id, 'name': tr.name}, 200

        tag = Tag(event_id=event_id, tag_type=TagType.INTEREST)
        db.session.add(tag)
        db.session.flush()
        for lang in ('en', 'fr'):
            db.session.add(TagTranslation(tag_id=tag.id, language=lang, name=name))
        db.session.commit()
        return {'id': tag.id, 'name': name}, 201


class ConsentAPI(restful.Resource):
    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=False)
        args = req_parser.parse_args()
        current_user_id = g.current_user['id']

        rows = consent_repository.get_all_latest(current_user_id, event_id=args['event_id'])
        return [
            {
                'consent_type': r.consent_type,
                'consent_version': r.consent_version,
                'granted': r.granted,
                'timestamp': r.timestamp.isoformat() + 'Z',
            }
            for r in rows
        ], 200

    @auth_required
    def post(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=False)
        req_parser.add_argument('consent_type', type=str, required=True)
        req_parser.add_argument('granted', type=bool, required=True)
        args = req_parser.parse_args()
        current_user_id = g.current_user['id']

        row = consent_repository.append(
            user_id=current_user_id,
            event_id=args['event_id'],
            consent_type=args['consent_type'],
            consent_version=CONSENT_VERSION,
            granted=args['granted'],
        )
        return {
            'consent_type': row.consent_type,
            'consent_version': row.consent_version,
            'granted': row.granted,
            'timestamp': row.timestamp.isoformat() + 'Z',
        }, 201
