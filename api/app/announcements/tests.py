import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import db
from app.announcements.models import Announcement, AnnouncementTranslation, AnnouncementReceipt, PushSubscription
from app.announcements.repository import AnnouncementRepository
from app.attendance.models import Checkin
from app.events.models import EventRole
from app.invitedGuest.models import InvitedGuest
from app.utils.testing import ApiTestCase


def _checkin(event_id, user_id):
    c = Checkin(event_id=event_id, user_id=user_id,
                checked_in_by_user_id=None, method='self', day=None)
    db.session.add(c)
    db.session.commit()
    return c


def _invited_guest(event_id, user_id):
    ig = InvitedGuest(event_id=event_id, user_id=user_id, role='Guest')
    db.session.add(ig)
    db.session.commit()
    return ig


class AnnouncementApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        event = self.add_event(key='TEST2025')
        self.event_id = event.id

        comms = self.add_user('comms@test.com')
        self.comms_id = comms.id
        self.add_event_role('comms-officer', comms.id, event.id)

        attendee1 = self.add_user('a1@test.com')
        self.attendee1_id = attendee1.id
        attendee2 = self.add_user('a2@test.com')
        self.attendee2_id = attendee2.id
        self.add_user('ng@test.com')

        _invited_guest(event.id, attendee1.id)
        _invited_guest(event.id, attendee2.id)
        _checkin(event.id, attendee1.id)
        _checkin(event.id, attendee2.id)

        self.comms_header = self.get_auth_header_for('comms@test.com')
        self.a1_header = self.get_auth_header_for('a1@test.com')
        self.a2_header = self.get_auth_header_for('a2@test.com')
        self.ng_header = self.get_auth_header_for('ng@test.com')

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_create_announcement_creates_receipts_for_checked_in_users(self, mock_push):
        payload = {
            'event_id': self.event_id,
            'translations': [
                {'language': 'en', 'title': 'Hello', 'body_markdown': 'World'},
            ],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertIn('id', data)
        self.assertEqual(data['audience_count'], 2)

        # Both checked-in users get a receipt
        receipts = db.session.query(AnnouncementReceipt).filter_by(announcement_id=data['id']).all()
        self.assertEqual(len(receipts), 2)
        recipient_ids = {r.user_id for r in receipts}
        self.assertIn(self.attendee1_id, recipient_ids)
        self.assertIn(self.attendee2_id, recipient_ids)
        # Not yet opened
        for r in receipts:
            self.assertIsNone(r.opened_at)

    def test_create_announcement_forbidden_for_non_comms_officer(self):
        payload = {
            'event_id': self.event_id,
            'translations': [{'language': 'en', 'title': 'Hi', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 403)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_active_list_excludes_expired(self, mock_push):
        ann_active_id = AnnouncementRepository.create(
            self.event_id, self.comms_id,
            expiry_at=datetime.utcnow() + timedelta(days=1),
            translations=[('en', 'Active', 'active body')],
        ).id
        ann_expired_id = AnnouncementRepository.create(
            self.event_id, self.comms_id,
            expiry_at=datetime.utcnow() - timedelta(hours=1),
            translations=[('en', 'Expired', 'expired body')],
        ).id

        resp = self.app.get(
            '/api/v1/announcement/active?event_id={}'.format(self.event_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        ids = [a['id'] for a in data]
        self.assertIn(ann_active_id, ids)
        self.assertNotIn(ann_expired_id, ids)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_detail_get_sets_opened_at(self, mock_push):
        payload = {
            'event_id': self.event_id,
            'translations': [{'language': 'en', 'title': 'T', 'body_markdown': 'B'}],
        }
        create_resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        ann_id = json.loads(create_resp.data)['id']

        resp = self.app.get(
            '/api/v1/announcement/{}?event_id={}'.format(ann_id, self.event_id),
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['title'], 'T')
        self.assertTrue(data['read'])

        receipt = db.session.query(AnnouncementReceipt).filter_by(
            announcement_id=ann_id, user_id=self.attendee1_id).first()
        self.assertIsNotNone(receipt.opened_at)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_late_checkin_inbox_backfills_auto_read_receipts(self, mock_push):
        # Create an announcement BEFORE the late joiner checks in
        ann_id = AnnouncementRepository.create(
            self.event_id, self.comms_id, None,
            translations=[('en', 'Old', 'old body')],
        ).id

        late_user = self.add_user('late@test.com')
        late_user_id = late_user.id
        _invited_guest(self.event_id, late_user_id)
        # late_user has NOT checked in yet → no receipt was created at dispatch time

        # Now late_user checks in and visits inbox
        _checkin(self.event_id, late_user_id)
        late_header = self.get_auth_header_for('late@test.com')
        resp = self.app.get(
            '/api/v1/announcement?event_id={}'.format(self.event_id),
            headers=late_header,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        # The announcement appears and is auto-marked read
        ann_data = next((a for a in data if a['id'] == ann_id), None)
        self.assertIsNotNone(ann_data)
        self.assertTrue(ann_data['read'])

        # Verify receipt exists and is auto-opened
        receipt = db.session.query(AnnouncementReceipt).filter_by(
            announcement_id=ann_id, user_id=late_user_id).first()
        self.assertIsNotNone(receipt)
        self.assertIsNotNone(receipt.opened_at)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_fr_recipient_gets_fr_translation(self, mock_push):
        from app.users.models import AppUser
        db.session.query(AppUser).filter_by(id=self.attendee1_id).update({'user_primaryLanguage': 'fr'})
        db.session.commit()

        payload = {
            'event_id': self.event_id,
            'translations': [
                {'language': 'en', 'title': 'Hello', 'body_markdown': 'Hello body'},
                {'language': 'fr', 'title': 'Bonjour', 'body_markdown': 'Corps Bonjour'},
            ],
        }
        create_resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        ann_id = json.loads(create_resp.data)['id']

        # FR reader gets FR
        resp_fr = self.app.get(
            '/api/v1/announcement/{}?event_id={}&language=fr'.format(ann_id, self.event_id),
            headers=self.a1_header,
        )
        self.assertEqual(json.loads(resp_fr.data)['title'], 'Bonjour')

        # EN reader gets EN
        resp_en = self.app.get(
            '/api/v1/announcement/{}?event_id={}&language=en'.format(ann_id, self.event_id),
            headers=self.a2_header,
        )
        self.assertEqual(json.loads(resp_en.data)['title'], 'Hello')

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_missing_fr_falls_back_to_en(self, mock_push):
        ann = AnnouncementRepository.create(
            self.event_id, self.comms_id, None,
            translations=[('en', 'English Only', 'body')],
        )
        ann_id = ann.id
        AnnouncementRepository.create_receipt(ann_id, self.attendee1_id)
        db.session.commit()

        resp = self.app.get(
            '/api/v1/announcement/{}?event_id={}&language=fr'.format(ann_id, self.event_id),
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['title'], 'English Only')

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_guest_list_audience_includes_non_checked_in_guests(self, mock_push):
        # Add a guest who is on the list but has not checked in
        not_checked_in = self.add_user('notcheckedin@test.com')
        not_checked_in_id = not_checked_in.id
        _invited_guest(self.event_id, not_checked_in_id)

        payload = {
            'event_id': self.event_id,
            'target_audience': 'guest_list',
            'translations': [
                {'language': 'en', 'title': 'All Guests', 'body_markdown': 'Hello everyone'},
            ],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        # 2 checked-in guests + 1 not-checked-in guest = 3
        self.assertEqual(data['audience_count'], 3)

        receipts = db.session.query(AnnouncementReceipt).filter_by(announcement_id=data['id']).all()
        recipient_ids = {r.user_id for r in receipts}
        self.assertIn(self.attendee1_id, recipient_ids)
        self.assertIn(self.attendee2_id, recipient_ids)
        self.assertIn(not_checked_in_id, recipient_ids)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_checked_in_audience_excludes_non_checked_in_guests(self, mock_push):
        # Guest on the list but not checked in
        not_checked_in = self.add_user('notcheckedin2@test.com')
        not_checked_in_id = not_checked_in.id
        _invited_guest(self.event_id, not_checked_in_id)

        payload = {
            'event_id': self.event_id,
            'target_audience': 'checked_in',
            'translations': [
                {'language': 'en', 'title': 'Checked In Only', 'body_markdown': 'Hello'},
            ],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['audience_count'], 2)

        receipts = db.session.query(AnnouncementReceipt).filter_by(announcement_id=data['id']).all()
        recipient_ids = {r.user_id for r in receipts}
        self.assertNotIn(not_checked_in_id, recipient_ids)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_invalid_target_audience_returns_error(self, mock_push):
        payload = {
            'event_id': self.event_id,
            'target_audience': 'everyone_on_earth',
            'translations': [{'language': 'en', 'title': 'Hi', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertIn(resp.status_code, (400, 422))

    def test_inbox_forbidden_for_non_guest(self):
        resp = self.app.get(
            '/api/v1/announcement?event_id={}'.format(self.event_id),
            headers=self.ng_header,
        )
        self.assertEqual(resp.status_code, 403)

    def test_push_subscription_upsert_and_delete(self):
        sub_payload = {
            'endpoint': 'https://push.example.com/abc123',
            'keys': {'p256dh': 'key1', 'auth': 'auth1'},
            'user_agent': 'TestBrowser',
        }
        resp = self.app.post(
            '/api/v1/push-subscription',
            data=json.dumps(sub_payload),
            content_type='application/json',
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 201)

        sub = db.session.query(PushSubscription).filter_by(
            endpoint='https://push.example.com/abc123').first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.user_id, self.attendee1_id)

        # Upsert: same endpoint, update keys
        sub_payload['keys']['p256dh'] = 'newkey'
        self.app.post(
            '/api/v1/push-subscription',
            data=json.dumps(sub_payload),
            content_type='application/json',
            headers=self.a1_header,
        )
        sub = db.session.query(PushSubscription).filter_by(
            endpoint='https://push.example.com/abc123').first()
        self.assertEqual(sub.p256dh, 'newkey')

        # Delete
        resp = self.app.delete(
            '/api/v1/push-subscription',
            data=json.dumps({'endpoint': 'https://push.example.com/abc123'}),
            content_type='application/json',
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 204)
        self.assertIsNone(db.session.query(PushSubscription).filter_by(
            endpoint='https://push.example.com/abc123').first())

    def test_malformed_subscription_returns_error(self):
        resp = self.app.post(
            '/api/v1/push-subscription',
            data=json.dumps({'endpoint': 'https://push.example.com/abc', 'keys': {}}),
            content_type='application/json',
            headers=self.a1_header,
        )
        self.assertIn(resp.status_code, (400, 422))

    def test_push_to_user_without_vapid_key_is_safe_noop(self):
        # A subscription exists, but with no server key configured push_to_user
        # must not raise or attempt delivery — it just reports zero sent.
        from app.utils.push import push_to_user
        db.session.add(PushSubscription(
            user_id=self.attendee1_id,
            endpoint='https://push.example.com/xyz',
            p256dh='p256dh', auth='auth', user_agent='TestBrowser',
        ))
        db.session.commit()
        with patch('config.VAPID_PRIVATE_KEY', ''):
            result = push_to_user(self.attendee1_id, {'title': 't', 'body': 'b', 'url': '/', 'tag': 'x'})
        self.assertEqual(result['sent'], 0)
        self.assertEqual(result['subscriptions'], 0)
        self.assertTrue(result['errors'])

    @patch('app.utils.push.webpush')
    def test_test_push_endpoint_delivers_to_own_subscription(self, mock_webpush):
        db.session.add(PushSubscription(
            user_id=self.attendee1_id,
            endpoint='https://push.example.com/self',
            p256dh='p256dh', auth='auth', user_agent='TestBrowser',
        ))
        db.session.commit()
        with patch('config.VAPID_PRIVATE_KEY', 'a-private-key'), \
                patch('config.VAPID_PUBLIC_KEY', 'a-public-key'):
            resp = self.app.post('/api/v1/push-subscription/test', headers=self.a1_header)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['subscriptions'], 1)
        self.assertEqual(data['sent'], 1)
        self.assertTrue(data['vapid_private_key_configured'])
        self.assertEqual(data['vapid_public_key'], 'a-public-key')
        mock_webpush.assert_called_once()

    def test_test_push_endpoint_reports_no_subscription(self):
        with patch('config.VAPID_PRIVATE_KEY', 'a-private-key'):
            resp = self.app.post('/api/v1/push-subscription/test', headers=self.a2_header)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['subscriptions'], 0)
        self.assertEqual(data['sent'], 0)

    def test_test_push_endpoint_requires_auth(self):
        resp = self.app.post('/api/v1/push-subscription/test')
        self.assertIn(resp.status_code, (401, 403))

    # ── Non-English-primary organisation ──────────────────────────────────────

    def _seed_fr_primary_event(self):
        from app.events.models import EventRole
        org = self.add_organisation(
            'Indaba Francophone', 'blah.png', 'blah_big.png', 'indaba-fr',
            languages=[{'code': 'fr', 'description': 'French'}]
        )
        event = self.add_event(key='FRTEST2025', organisation_id=org.id)
        comms = self.add_user('fr-comms@test.com')
        self.add_event_role('comms-officer', comms.id, event.id)
        return event.id, self.get_auth_header_for('fr-comms@test.com')

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_create_announcement_succeeds_with_only_primary_language(self, mock_push):
        event_id, header = self._seed_fr_primary_event()
        payload = {
            'event_id': event_id,
            'translations': [{'language': 'fr', 'title': 'Bonjour', 'body_markdown': 'Corps'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header,
        )
        self.assertEqual(resp.status_code, 201)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_create_announcement_without_primary_language_rejected(self, mock_push):
        event_id, header = self._seed_fr_primary_event()
        payload = {
            'event_id': event_id,
            'translations': [{'language': 'en', 'title': 'Hello', 'body_markdown': 'Body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=header,
        )
        self.assertEqual(resp.status_code, 400)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_translation_falls_back_to_whatever_exists_not_just_en(self, mock_push):
        # Organisation has no 'en' translation at all for this announcement — the
        # fallback must not assume English exists, it should use whatever is there.
        ann = AnnouncementRepository.create(
            self.event_id, self.comms_id, None,
            translations=[('de', 'Nur Deutsch', 'body')],
        )
        AnnouncementRepository.create_receipt(ann.id, self.attendee1_id)
        db.session.commit()

        resp = self.app.get(
            '/api/v1/announcement/{}?event_id={}&language=fr'.format(ann.id, self.event_id),
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['title'], 'Nur Deutsch')

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_delete_removes_announcement_with_translations_and_receipts(self, mock_push):
        # A sent announcement has both translation rows and receipt rows
        # pointing at it via FK — deleting it must not violate those constraints.
        payload = {
            'event_id': self.event_id,
            'translations': [{'language': 'en', 'title': 'Bye', 'body_markdown': 'body'}],
        }
        create_resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        ann_id = json.loads(create_resp.data)['id']
        self.assertTrue(
            db.session.query(AnnouncementReceipt).filter_by(announcement_id=ann_id).count() > 0)

        resp = self.app.delete(
            '/api/v1/announcement/{}?event_id={}'.format(ann_id, self.event_id),
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 204)

        self.assertIsNone(db.session.query(Announcement).filter_by(id=ann_id).first())
        self.assertEqual(
            db.session.query(AnnouncementTranslation).filter_by(announcement_id=ann_id).count(), 0)
        self.assertEqual(
            db.session.query(AnnouncementReceipt).filter_by(announcement_id=ann_id).count(), 0)

    def test_delete_forbidden_for_non_comms_officer(self):
        ann = AnnouncementRepository.create(
            self.event_id, self.comms_id, None,
            translations=[('en', 'Keep', 'body')],
        )
        resp = self.app.delete(
            '/api/v1/announcement/{}?event_id={}'.format(ann.id, self.event_id),
            headers=self.a1_header,
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIsNotNone(db.session.query(Announcement).filter_by(id=ann.id).first())

    def test_delete_not_found_for_wrong_event(self):
        other_event = self.add_event(key='OTHEREVENT2025')
        self.add_event_role('comms-officer', self.comms_id, other_event.id)
        ann = AnnouncementRepository.create(
            self.event_id, self.comms_id, None,
            translations=[('en', 'Keep', 'body')],
        )
        resp = self.app.delete(
            '/api/v1/announcement/{}?event_id={}'.format(ann.id, other_event.id),
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 404)

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_admin_list_shows_delivery_stats(self, mock_push):
        payload = {
            'event_id': self.event_id,
            'translations': [{'language': 'en', 'title': 'Stats Test', 'body_markdown': 'body'}],
        }
        self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        resp = self.app.get(
            '/api/v1/announcement/admin?event_id={}'.format(self.event_id),
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Stats Test')
        self.assertEqual(data[0]['delivered_count'], 2)
        self.assertEqual(data[0]['opened_count'], 0)


if __name__ == '__main__':
    unittest.main()
