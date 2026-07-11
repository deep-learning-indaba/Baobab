from datetime import datetime

from flask import g, request
import flask_restful as restful
from flask_restful import reqparse

from app.utils.auth import auth_required
from app.utils import errors
from app.programme.repository import ProgrammeRepository
from app.programme.models import Session, SessionTranslation, Speaker, SessionSpeaker, SessionTag
from app.tags.models import Tag, TagTranslation, TagType
from app.tags.repository import TagRepository
from app.users.repository import UserRepository as user_repository
from app.events.repository import EventRepository as event_repository
from app.utils.datetime_utils import event_local_datetime


def _is_programme_editor(user_id, event_id):
    user = user_repository.get_by_id(user_id)
    return user and user.is_programme_editor(event_id)


def _primary_language(event):
    """The organisation's first configured language, used as the mandatory
    translation when none is specified — organisations aren't all English-first."""
    languages = event.organisation.languages if event and event.organisation else None
    return languages[0]['code'] if languages else 'en'


def _serialize_speaker(speaker):
    return {
        'id': speaker.id,
        'event_id': speaker.event_id,
        'name': speaker.name,
        'email': speaker.email,
        'photo_url': speaker.photo_url,
        'bio': speaker.bio,
        'linked_user_id': speaker.linked_user_id
    }


def _serialize_speaker_public(speaker):
    return {
        'id': speaker.id,
        'name': speaker.name,
        'photo_url': speaker.photo_url,
        'bio': speaker.bio
    }


def _serialize_tag_brief(tag, language):
    t = tag.get_translation(language)
    if t is None:
        t = next(iter(tag.translations), None)
    return {
        'id': tag.id,
        'name': t.name if t else ''
    }


def _serialize_session(session, language):
    t = next((x for x in session.translations if x.language == language), None)
    if t is None:
        t = session.translations[0] if session.translations else None
    title = t.title if t else ''
    description = t.description if t else ''

    translations = [
        {'language': x.language, 'title': x.title, 'description': x.description or ''}
        for x in session.translations
    ]

    session_type = None
    if session.session_type_id:
        type_tag = TagRepository.get_by_id(session.session_type_id)
        if type_tag:
            session_type = _serialize_tag_brief(type_tag, language)

    speakers = []
    for ss in session.session_speakers:
        spk = ProgrammeRepository.get_speaker(ss.speaker_id)
        if spk:
            speakers.append(_serialize_speaker(spk))

    tracks = []
    for st in session.session_tags:
        tag = TagRepository.get_by_id(st.tag_id)
        if tag:
            tracks.append(_serialize_tag_brief(tag, language))

    return {
        'id': session.id,
        'event_id': session.event_id,
        'title': title,
        'description': description,
        'translations': translations,
        'session_type': session_type,
        'session_type_id': session.session_type_id,
        'venue': session.venue or '',
        'start_time': session.start_time.isoformat() + 'Z' if session.start_time else None,
        'end_time': session.end_time.isoformat() + 'Z' if session.end_time else None,
        'speakers': speakers,
        'tracks': tracks
    }


def _serialize_session_public(session, language, event_timezone):
    t = next((x for x in session.translations if x.language == language), None)
    if t is None:
        t = session.translations[0] if session.translations else None
    title = t.title if t else ''
    description = t.description if t else ''

    translations = [
        {'language': x.language, 'title': x.title, 'description': x.description or ''}
        for x in session.translations
    ]

    session_type = None
    if session.session_type_id:
        type_tag = TagRepository.get_by_id(session.session_type_id)
        if type_tag:
            session_type = _serialize_tag_brief(type_tag, language)

    speakers = []
    for ss in session.session_speakers:
        spk = ProgrammeRepository.get_speaker(ss.speaker_id)
        if spk:
            speakers.append(_serialize_speaker_public(spk))

    tracks = []
    for st in session.session_tags:
        tag = TagRepository.get_by_id(st.tag_id)
        if tag:
            tracks.append(_serialize_tag_brief(tag, language))

    return {
        'id': session.id,
        'title': title,
        'description': description,
        'translations': translations,
        'session_type': session_type,
        'session_type_id': session.session_type_id,
        'start_time': event_local_datetime(session.start_time, event_timezone).isoformat() if session.start_time else None,
        'end_time': event_local_datetime(session.end_time, event_timezone).isoformat() if session.end_time else None,
        'speakers': speakers,
        'tracks': tracks
    }


def _parse_datetime(value):
    if value is None:
        return None
    value = value.rstrip('Z')
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


class SessionListAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()

        sessions = ProgrammeRepository.list_sessions(args['event_id'])
        return [_serialize_session(s, args['language']) for s in sessions]

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_programme_editor(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        start_time = _parse_datetime(body.get('start_time'))
        end_time = _parse_datetime(body.get('end_time'))
        if start_time is None or end_time is None:
            return errors.MISSING_FIELDS
        if end_time < start_time:
            return errors.SESSION_END_BEFORE_START

        session = Session()
        session.event_id = event_id
        session.session_type_id = body.get('session_type_id')
        session.venue = body.get('venue', '')
        session.start_time = start_time
        session.end_time = end_time

        for t in (body.get('translations') or []):
            lang = t.get('language')
            title = t.get('title', '')
            desc = t.get('description', '')
            if lang and title:
                session.translations.append(SessionTranslation(None, lang, title, desc))

        ProgrammeRepository.create_session(session)

        for speaker_id in (body.get('speaker_ids') or []):
            spk = ProgrammeRepository.get_speaker(speaker_id)
            if spk and spk.event_id == event_id:
                session.session_speakers.append(SessionSpeaker(session.id, speaker_id))

        for tag_id in (body.get('track_tag_ids') or []):
            tag = TagRepository.get_by_id(tag_id)
            if tag and tag.event_id == event_id:
                session.session_tags.append(SessionTag(session.id, tag_id))

        ProgrammeRepository.commit()

        language = body.get('language', 'en')
        return _serialize_session(session, language), 201


class SessionAPI(restful.Resource):

    @auth_required
    def get(self, session_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()

        session = ProgrammeRepository.get_session(session_id)
        if not session:
            return errors.SESSION_NOT_FOUND

        return _serialize_session(session, args['language'])

    @auth_required
    def put(self, session_id):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        session = ProgrammeRepository.get_session(session_id)
        if not session:
            return errors.SESSION_NOT_FOUND

        if not _is_programme_editor(g.current_user['id'], session.event_id):
            return errors.FORBIDDEN

        start_time = _parse_datetime(body.get('start_time'))
        end_time = _parse_datetime(body.get('end_time'))
        if start_time is None or end_time is None:
            return errors.MISSING_FIELDS
        if end_time < start_time:
            return errors.SESSION_END_BEFORE_START

        session.session_type_id = body.get('session_type_id')
        session.venue = body.get('venue', '')
        session.start_time = start_time
        session.end_time = end_time

        # Update translations: remove old, add new
        existing_langs = {t.language: t for t in session.translations}
        incoming_langs = {t['language'] for t in (body.get('translations') or []) if t.get('language')}

        for lang, trans in list(existing_langs.items()):
            if lang not in incoming_langs:
                session.translations.remove(trans)

        for t in (body.get('translations') or []):
            lang = t.get('language')
            title = t.get('title', '')
            desc = t.get('description', '')
            if not lang or not title:
                continue
            if lang in existing_langs:
                existing_langs[lang].title = title
                existing_langs[lang].description = desc
            else:
                session.translations.append(SessionTranslation(session.id, lang, title, desc))

        # Update speakers
        session.session_speakers.clear()
        for speaker_id in (body.get('speaker_ids') or []):
            spk = ProgrammeRepository.get_speaker(speaker_id)
            if spk and spk.event_id == session.event_id:
                session.session_speakers.append(SessionSpeaker(session.id, speaker_id))

        # Update track tags
        session.session_tags.clear()
        for tag_id in (body.get('track_tag_ids') or []):
            tag = TagRepository.get_by_id(tag_id)
            if tag and tag.event_id == session.event_id:
                session.session_tags.append(SessionTag(session.id, tag_id))

        ProgrammeRepository.commit()

        language = body.get('language', 'en')
        return _serialize_session(session, language)

    @auth_required
    def delete(self, session_id):
        session = ProgrammeRepository.get_session(session_id)
        if not session:
            return errors.SESSION_NOT_FOUND

        if not _is_programme_editor(g.current_user['id'], session.event_id):
            return errors.FORBIDDEN

        ProgrammeRepository.delete_session(session)
        return {'message': 'Session deleted'}, 200


class SpeakerListAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        args = req_parser.parse_args()

        speakers = ProgrammeRepository.list_speakers(args['event_id'])
        return [_serialize_speaker(s) for s in speakers]

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_programme_editor(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        name = body.get('name', '').strip()
        if not name:
            return errors.MISSING_FIELDS

        if ProgrammeRepository.find_speaker_by_name(event_id, name):
            return errors.SPEAKER_NAME_TAKEN

        email = body.get('email')
        linked_user_id = ProgrammeRepository.find_linked_user(event_id, name, email)

        speaker = Speaker(
            event_id=event_id,
            name=name,
            email=email,
            photo_url=body.get('photo_url'),
            bio=body.get('bio'),
            linked_user_id=linked_user_id
        )
        ProgrammeRepository.create_speaker(speaker)
        return _serialize_speaker(speaker), 201


class SpeakerAPI(restful.Resource):

    @auth_required
    def put(self, speaker_id):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        speaker = ProgrammeRepository.get_speaker(speaker_id)
        if not speaker:
            return errors.SPEAKER_NOT_FOUND

        if not _is_programme_editor(g.current_user['id'], speaker.event_id):
            return errors.FORBIDDEN

        name = body.get('name', '').strip()
        if not name:
            return errors.MISSING_FIELDS

        if ProgrammeRepository.find_speaker_by_name(speaker.event_id, name, exclude_speaker_id=speaker.id):
            return errors.SPEAKER_NAME_TAKEN

        speaker.name = name
        speaker.email = body.get('email', speaker.email)
        speaker.photo_url = body.get('photo_url', speaker.photo_url)
        speaker.bio = body.get('bio', speaker.bio)
        speaker.linked_user_id = ProgrammeRepository.find_linked_user(
            speaker.event_id, speaker.name, speaker.email
        )

        ProgrammeRepository.commit()
        return _serialize_speaker(speaker)


class SessionTypeListAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()

        tags = ProgrammeRepository.list_session_types(args['event_id'])
        return [_serialize_tag_brief(t, args['language']) for t in tags]

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_programme_editor(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        names = body.get('name', {})
        if not names or not names.get(_primary_language(event)):
            return errors.MISSING_FIELDS

        tag = Tag(event_id, TagType.SESSION_TYPE, True)
        for lang, name in names.items():
            desc = (body.get('description') or {}).get(lang)
            tag.translations.append(TagTranslation(tag.id, lang, name, desc))
        TagRepository.add_tag(tag)

        language = body.get('language', 'en')
        return _serialize_tag_brief(tag, language), 201


class PublicProgrammeAPI(restful.Resource):
    # Intentionally unauthenticated - venue and speaker contact details are omitted below.

    def get(self, event_key):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()

        event = event_repository.get_by_key(event_key)
        if not event:
            return errors.EVENT_WITH_KEY_NOT_FOUND

        sessions = ProgrammeRepository.list_sessions(event.id)
        return [_serialize_session_public(s, args['language'], event.timezone) for s in sessions]


class TrackListAPI(restful.Resource):

    @auth_required
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('event_id', type=int, required=True)
        req_parser.add_argument('language', type=str, default='en')
        args = req_parser.parse_args()

        tags = ProgrammeRepository.list_tracks(args['event_id'])
        return [_serialize_tag_brief(t, args['language']) for t in tags]

    @auth_required
    def post(self):
        body = request.get_json()
        if not body:
            return errors.MISSING_FIELDS

        event_id = body.get('event_id')
        if not event_id:
            return errors.MISSING_FIELDS

        if not _is_programme_editor(g.current_user['id'], event_id):
            return errors.FORBIDDEN

        event = event_repository.get_by_id(event_id)
        if not event:
            return errors.EVENT_NOT_FOUND

        names = body.get('name', {})
        if not names or not names.get(_primary_language(event)):
            return errors.MISSING_FIELDS

        tag = Tag(event_id, TagType.TRACK, True)
        for lang, name in names.items():
            desc = (body.get('description') or {}).get(lang)
            tag.translations.append(TagTranslation(tag.id, lang, name, desc))
        TagRepository.add_tag(tag)

        language = body.get('language', 'en')
        return _serialize_tag_brief(tag, language), 201
