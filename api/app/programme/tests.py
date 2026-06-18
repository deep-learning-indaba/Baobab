import json
from datetime import datetime, timedelta

from app import db
from app.events.models import EventRole
from app.invitedGuest.models import InvitedGuest
from app.offer.models import Offer
from app.programme.models import Session, SessionTranslation, Speaker, SessionSpeaker, SessionTag
from app.tags.models import Tag, TagTranslation, TagType
from app.utils.testing import ApiTestCase


class ProgrammeApiTest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')

        event = self.add_event(
            name={'en': 'Indaba 2026'},
            description={'en': 'The Deep Learning Indaba 2026'},
            start_date=datetime(2026, 8, 2),
            end_date=datetime(2026, 8, 7),
            key='INDABA2026'
        )
        self.event_id = event.id

        editor = self.add_user('editor@test.com', 'Ed', 'Itor')
        self.editor_id = editor.id
        other = self.add_user('other@test.com', 'Other', 'User')
        self.other_id = other.id
        guest = self.add_user('guest@test.com', 'Guest', 'User')
        self.guest_id = guest.id

        self.add_event_role('programme-editor', self.editor_id, self.event_id)

        invited = InvitedGuest(self.event_id, self.guest_id, 'guest')
        db.session.add(invited)
        db.session.commit()

        session_type_tag = Tag(self.event_id, TagType.SESSION_TYPE, True)
        db.session.add(session_type_tag)
        db.session.commit()
        self.session_type_tag_id = session_type_tag.id
        db.session.add(TagTranslation(self.session_type_tag_id, 'en', 'Keynote', None))
        db.session.add(TagTranslation(self.session_type_tag_id, 'fr', 'Pleniere', None))

        track_tag = Tag(self.event_id, TagType.TRACK, True)
        db.session.add(track_tag)
        db.session.commit()
        self.track_tag_id = track_tag.id
        db.session.add(TagTranslation(self.track_tag_id, 'en', 'Research', None))
        db.session.add(TagTranslation(self.track_tag_id, 'fr', 'Recherche', None))

        linked_speaker = Speaker(
            event_id=self.event_id,
            name='Guest User',
            email='guest@test.com'
        )
        db.session.add(linked_speaker)
        db.session.commit()
        self.linked_speaker_id = linked_speaker.id

    def _create_session_payload(self, start='2026-08-02T09:00:00', end='2026-08-02T10:30:00',
                                 title_en='Opening Keynote', include_fr=True):
        translations = [{'language': 'en', 'title': title_en, 'description': 'A great session.'}]
        if include_fr:
            translations.append({'language': 'fr', 'title': "Discours d'ouverture", 'description': 'Une super session.'})
        return {
            'event_id': self.event_id,
            'translations': translations,
            'session_type_id': self.session_type_tag_id,
            'venue': 'Main Hall',
            'start_time': start,
            'end_time': end,
            'speaker_ids': [self.linked_speaker_id],
            'track_tag_ids': [self.track_tag_id]
        }

    # ── Positive tests ──────────────────────────────────────────────────────────

    def test_editor_creates_session(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = self._create_session_payload()

        response = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Opening Keynote')
        self.assertEqual(data['venue'], 'Main Hall')
        self.assertEqual(len(data['speakers']), 1)
        self.assertEqual(len(data['tracks']), 1)
        self.assertIsNotNone(data['session_type'])

    def test_list_sessions_sorted_by_start_time(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')

        for (start, end) in [
            ('2026-08-02T14:00:00', '2026-08-02T15:00:00'),
            ('2026-08-02T09:00:00', '2026-08-02T10:00:00'),
        ]:
            payload = self._create_session_payload(start=start, end=end)
            self.app.post(
                '/api/v1/programme/sessions',
                data=json.dumps(payload),
                content_type='application/json',
                headers=header
            )

        response = self.app.get(
            '/api/v1/programme/sessions?event_id={}'.format(self.event_id),
            headers=header
        )
        self.assertEqual(response.status_code, 200)
        sessions = json.loads(response.data)
        self.assertEqual(len(sessions), 2)
        self.assertLessEqual(sessions[0]['start_time'], sessions[1]['start_time'])

    def test_fr_language_returns_fr_translation(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = self._create_session_payload()

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        session_id = json.loads(create_resp.data)['id']

        response = self.app.get(
            '/api/v1/programme/sessions/{}?language=fr'.format(session_id),
            headers=header
        )
        data = json.loads(response.data)
        self.assertEqual(data['title'], "Discours d'ouverture")

    def test_missing_fr_falls_back_to_en(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = self._create_session_payload(include_fr=False)

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        session_id = json.loads(create_resp.data)['id']

        response = self.app.get(
            '/api/v1/programme/sessions/{}?language=fr'.format(session_id),
            headers=header
        )
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Opening Keynote')

    def test_speaker_email_auto_links_to_user(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')

        # Create speaker via API so find_linked_user runs
        speaker_resp = self.app.post(
            '/api/v1/programme/speakers',
            data=json.dumps({'event_id': self.event_id, 'name': 'Guest User', 'email': 'guest@test.com'}),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(speaker_resp.status_code, 201)
        api_speaker = json.loads(speaker_resp.data)
        self.assertEqual(api_speaker['linked_user_id'], self.guest_id)

    def test_overlapping_sessions_both_returned(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')

        for (start, end) in [
            ('2026-08-02T09:00:00', '2026-08-02T10:30:00'),
            ('2026-08-02T09:30:00', '2026-08-02T11:00:00'),
        ]:
            payload = self._create_session_payload(start=start, end=end)
            self.app.post(
                '/api/v1/programme/sessions',
                data=json.dumps(payload),
                content_type='application/json',
                headers=header
            )

        response = self.app.get(
            '/api/v1/programme/sessions?event_id={}'.format(self.event_id),
            headers=header
        )
        sessions = json.loads(response.data)
        self.assertEqual(len(sessions), 2)

    def test_editor_updates_session(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(self._create_session_payload()),
            content_type='application/json',
            headers=header
        )
        session_id = json.loads(create_resp.data)['id']

        update_payload = self._create_session_payload(title_en='Updated Title')
        response = self.app.put(
            '/api/v1/programme/sessions/{}'.format(session_id),
            data=json.dumps(update_payload),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Updated Title')

    def test_editor_deletes_session(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(self._create_session_payload()),
            content_type='application/json',
            headers=header
        )
        session_id = json.loads(create_resp.data)['id']

        delete_resp = self.app.delete(
            '/api/v1/programme/sessions/{}'.format(session_id),
            headers=header
        )
        self.assertEqual(delete_resp.status_code, 200)

        list_resp = self.app.get(
            '/api/v1/programme/sessions?event_id={}'.format(self.event_id),
            headers=header
        )
        sessions = json.loads(list_resp.data)
        self.assertEqual(len(sessions), 0)

    def test_list_session_types(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        response = self.app.get(
            '/api/v1/programme/session-types?event_id={}'.format(self.event_id),
            headers=header
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Keynote')

    def test_list_tracks(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        response = self.app.get(
            '/api/v1/programme/tracks?event_id={}'.format(self.event_id),
            headers=header
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Research')

    def test_editor_adds_session_type(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = {
            'event_id': self.event_id,
            'name': {'en': 'Workshop', 'fr': 'Atelier'}
        }
        response = self.app.post(
            '/api/v1/programme/session-types',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Workshop')

    def test_editor_creates_speaker(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = {
            'event_id': self.event_id,
            'name': 'New Speaker',
            'email': 'newspeaker@test.com',
            'bio': 'A great speaker.'
        }
        response = self.app.post(
            '/api/v1/programme/speakers',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'New Speaker')

    # ── Negative tests ──────────────────────────────────────────────────────────

    def test_non_editor_cannot_create_session(self):
        self.seed_static_data()
        header = self.get_auth_header_for('other@test.com')

        response = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(self._create_session_payload()),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 403)

    def test_non_editor_cannot_update_session(self):
        self.seed_static_data()
        editor_header = self.get_auth_header_for('editor@test.com')

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(self._create_session_payload()),
            content_type='application/json',
            headers=editor_header
        )
        session_id = json.loads(create_resp.data)['id']

        other_header = self.get_auth_header_for('other@test.com')
        response = self.app.put(
            '/api/v1/programme/sessions/{}'.format(session_id),
            data=json.dumps(self._create_session_payload(title_en='Hacked')),
            content_type='application/json',
            headers=other_header
        )
        self.assertEqual(response.status_code, 403)

    def test_non_editor_cannot_delete_session(self):
        self.seed_static_data()
        editor_header = self.get_auth_header_for('editor@test.com')

        create_resp = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(self._create_session_payload()),
            content_type='application/json',
            headers=editor_header
        )
        session_id = json.loads(create_resp.data)['id']

        other_header = self.get_auth_header_for('other@test.com')
        response = self.app.delete(
            '/api/v1/programme/sessions/{}'.format(session_id),
            headers=other_header
        )
        self.assertEqual(response.status_code, 403)

    def test_end_before_start_rejected(self):
        self.seed_static_data()
        header = self.get_auth_header_for('editor@test.com')
        payload = self._create_session_payload(
            start='2026-08-02T11:00:00',
            end='2026-08-02T09:00:00'
        )
        response = self.app.post(
            '/api/v1/programme/sessions',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_cannot_list_sessions(self):
        self.seed_static_data()
        response = self.app.get('/api/v1/programme/sessions?event_id={}'.format(self.event_id))
        self.assertEqual(response.status_code, 401)
