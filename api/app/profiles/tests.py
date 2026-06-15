import json
from datetime import datetime, timedelta

from app import db
from app.profiles.models import MemberProfile, MemberProfileLink, MemberProfileInterest
from app.profiles.repository import ProfileRepository as profile_repository
from app.profiles.repository import ConsentRepository as consent_repository
from app.users.models import UserConsent
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.tags.models import Tag, TagTranslation, TagType
from app.offer.models import Offer
from app.utils.testing import ApiTestCase


class ProfileAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.guest = self.add_user('guest@test.com', 'Guest', 'User')
        self.non_guest = self.add_user('nonguesttest@test.com', 'NonGuest', 'User')
        self.guest_id = self.guest.id
        self.non_guest_id = self.non_guest.id
        self.event = self.add_event(
            {'en': 'Profile Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'PROFEV'
        )
        self.event_id = self.event.id
        offer = Offer(
            user_id=self.guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer)
        db.session.commit()

        interest_tag = Tag(event_id=self.event_id, tag_type=TagType.INTEREST)
        db.session.add(interest_tag)
        db.session.flush()
        db.session.add(TagTranslation(tag_id=interest_tag.id, language='en', name='Machine Learning'))
        db.session.add(TagTranslation(tag_id=interest_tag.id, language='fr', name='Apprentissage automatique'))
        db.session.commit()
        self.interest_tag_id = interest_tag.id

    def test_get_own_profile_creates_if_missing(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get('/api/v1/profile?event_id={}'.format(self.event_id), headers=header)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], self.guest_id)
        self.assertEqual(data['visibility'], 'community')
        profile = db.session.query(MemberProfile).filter_by(user_id=self.guest_id).first()
        self.assertIsNotNone(profile)

    def test_update_own_profile(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        payload = {
            'event_id': self.event_id,
            'headline': 'PhD student in NLP',
            'about': 'Researcher at Univ X',
            'city': 'Lagos',
            'visibility': 'community',
            'interest_ids': [self.interest_tag_id],
            'links': {'linkedin': 'https://linkedin.com/in/test'},
        }
        response = self.app.put(
            '/api/v1/profile',
            data=json.dumps(payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['headline'], 'PhD student in NLP')
        self.assertEqual(data['city'], 'Lagos')
        self.assertEqual(len(data['interests']), 1)
        self.assertEqual(data['interests'][0]['name'], 'Machine Learning')
        self.assertEqual(data['links'].get('linkedin'), 'https://linkedin.com/in/test')

    def test_update_profile_creates_interest_tag(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        create_payload = {'event_id': self.event_id, 'name': 'New Interest'}
        response = self.app.post(
            '/api/v1/profile/interests',
            data=json.dumps(create_payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'New Interest')

        response2 = self.app.post(
            '/api/v1/profile/interests',
            data=json.dumps(create_payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.data)
        self.assertEqual(data2['id'], data['id'])

    def test_update_visibility_to_hidden(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        payload = {'event_id': self.event_id, 'visibility': 'hidden'}
        response = self.app.put(
            '/api/v1/profile',
            data=json.dumps(payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['visibility'], 'hidden')

    def test_list_community_excludes_hidden_profiles(self):
        self.seed_static_data()
        second_guest = self.add_user('guest2@test.com', 'Second', 'Guest')
        second_guest_id = second_guest.id
        offer2 = Offer(
            user_id=second_guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer2)
        db.session.commit()
        hidden_profile = MemberProfile(user_id=second_guest_id)
        hidden_profile.visibility = 'hidden'
        db.session.add(hidden_profile)
        db.session.commit()

        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get('/api/v1/profile/list?event_id={}'.format(self.event_id), headers=header)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        user_ids = [p['user_id'] for p in data]
        self.assertIn(self.guest_id, user_ids)
        self.assertNotIn(second_guest_id, user_ids)

    def test_view_another_profile(self):
        self.seed_static_data()
        profile = MemberProfile(user_id=self.guest_id)
        profile.headline = 'Hello'
        db.session.add(profile)
        db.session.commit()

        second_guest = self.add_user('guest2@test.com', 'Second', 'Guest')
        second_guest_id = second_guest.id
        offer2 = Offer(
            user_id=second_guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer2)
        db.session.commit()

        header = self.get_auth_header_for('guest2@test.com')
        response = self.app.get(
            '/api/v1/profile/view?event_id={}&user_id={}'.format(self.event_id, self.guest_id),
            headers=header,
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['headline'], 'Hello')
        self.assertFalse(data.get('hidden', False))

    def test_view_hidden_profile_returns_minimal(self):
        self.seed_static_data()
        hidden_profile = MemberProfile(user_id=self.guest_id)
        hidden_profile.visibility = 'hidden'
        db.session.add(hidden_profile)
        db.session.commit()

        second_guest = self.add_user('guest2@test.com', 'Second', 'Guest')
        second_guest_id = second_guest.id
        offer2 = Offer(
            user_id=second_guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer2)
        db.session.commit()

        header = self.get_auth_header_for('guest2@test.com')
        response = self.app.get(
            '/api/v1/profile/view?event_id={}&user_id={}'.format(self.event_id, self.guest_id),
            headers=header,
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['hidden'])
        self.assertNotIn('headline', data)
        self.assertNotIn('about', data)

    def test_non_guest_cannot_list_profiles(self):
        self.seed_static_data()
        header = self.get_auth_header_for('nonguesttest@test.com')
        response = self.app.get('/api/v1/profile/list?event_id={}'.format(self.event_id), headers=header)
        self.assertEqual(response.status_code, 403)

    def test_non_guest_cannot_view_profile(self):
        self.seed_static_data()
        header = self.get_auth_header_for('nonguesttest@test.com')
        response = self.app.get(
            '/api/v1/profile/view?event_id={}&user_id={}'.format(self.event_id, self.guest_id),
            headers=header,
        )
        self.assertEqual(response.status_code, 403)


class ConsentAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.user = self.add_user('user@test.com', 'Test', 'User')
        self.user_id = self.user.id
        self.event = self.add_event(
            {'en': 'Consent Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'CONEV'
        )
        self.event_id = self.event.id

    def test_record_consent_appends_row(self):
        self.seed_static_data()
        header = self.get_auth_header_for('user@test.com')
        payload = {'event_id': self.event_id, 'consent_type': 'longitudinal_use', 'granted': True}
        response = self.app.post(
            '/api/v1/consent',
            data=json.dumps(payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['granted'])
        self.assertEqual(data['consent_type'], 'longitudinal_use')

        rows = db.session.query(UserConsent).filter_by(user_id=self.user_id).all()
        self.assertEqual(len(rows), 1)

    def test_record_consent_twice_appends_both_rows(self):
        self.seed_static_data()
        header = self.get_auth_header_for('user@test.com')
        payload = {'event_id': self.event_id, 'consent_type': 'longitudinal_use', 'granted': True}
        self.app.post(
            '/api/v1/consent',
            data=json.dumps(payload),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        payload2 = {'event_id': self.event_id, 'consent_type': 'longitudinal_use', 'granted': False}
        self.app.post(
            '/api/v1/consent',
            data=json.dumps(payload2),
            headers=dict(header, **{'Content-Type': 'application/json'}),
        )
        rows = db.session.query(UserConsent).filter_by(user_id=self.user_id).all()
        self.assertEqual(len(rows), 2)

    def test_get_consent_returns_latest_state(self):
        self.seed_static_data()
        header = self.get_auth_header_for('user@test.com')
        for granted in [True, False]:
            payload = {'event_id': self.event_id, 'consent_type': 'longitudinal_use', 'granted': granted}
            self.app.post(
                '/api/v1/consent',
                data=json.dumps(payload),
                headers=dict(header, **{'Content-Type': 'application/json'}),
            )
        response = self.app.get('/api/v1/consent?event_id={}'.format(self.event_id), headers=header)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0]['granted'])
