import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import db
from app.announcements.api import _enqueue
from app.announcements.models import Announcement, AnnouncementTranslation, AnnouncementReceipt, PushSubscription
from app.announcements.repository import AnnouncementRepository
from app.attendance.models import Checkin
from app.events.models import Event, EventRole
from app.invitedGuest.models import InvitedGuest, InvitedGuestTag
from app.offer.models import OfferTag
from app.outbox.models import OutboxChannel, OutboxMessage, OutboxStatus
from app.users.models import AppUser
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
    def test_tag_filter_restricts_to_tagged_invited_guests(self, mock_push):
        tag = self.add_tag(event_id=self.event_id, tag_type='GRANT', names={'en': 'Accommodation'})
        ig = db.session.query(InvitedGuest).filter_by(
            event_id=self.event_id, user_id=self.attendee1_id).first()
        db.session.add(InvitedGuestTag(ig.id, tag.id))
        db.session.commit()

        payload = {
            'event_id': self.event_id,
            'tag_id': tag.id,
            'translations': [{'language': 'en', 'title': 'Accommodation Info', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['audience_count'], 1)

        receipts = db.session.query(AnnouncementReceipt).filter_by(announcement_id=data['id']).all()
        recipient_ids = {r.user_id for r in receipts}
        self.assertEqual(recipient_ids, {self.attendee1_id})

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_tag_filter_matches_tagged_offer_holders_and_combines_with_guest_list_audience(self, mock_push):
        tag = self.add_tag(event_id=self.event_id, tag_type='GRANT', names={'en': 'Travel'})
        traveller = self.add_user('traveller@test.com')
        traveller_id = traveller.id
        self.add_offer(traveller_id, event_id=self.event_id, payment_required=False,
                        candidate_response=True, tags=[tag])
        # A confirmed guest without the tag must NOT be included.
        untagged_offer_holder = self.add_user('notravel@test.com')
        untagged_offer_holder_id = untagged_offer_holder.id
        self.add_offer(untagged_offer_holder_id, event_id=self.event_id, payment_required=False,
                        candidate_response=True)

        payload = {
            'event_id': self.event_id,
            'target_audience': 'guest_list',
            'tag_id': tag.id,
            'translations': [{'language': 'en', 'title': 'Travel Info', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['audience_count'], 1)

        receipts = db.session.query(AnnouncementReceipt).filter_by(announcement_id=data['id']).all()
        recipient_ids = {r.user_id for r in receipts}
        self.assertEqual(recipient_ids, {traveller_id})

    @patch('app.announcements.api.push_to_user', return_value=0)
    def test_tag_filter_excludes_tagged_guest_not_matching_checked_in_audience(self, mock_push):
        tag = self.add_tag(event_id=self.event_id, tag_type='GRANT', names={'en': 'Accommodation'})
        not_checked_in = self.add_user('tagged-not-checked-in@test.com')
        ig = _invited_guest(self.event_id, not_checked_in.id)
        db.session.add(InvitedGuestTag(ig.id, tag.id))
        db.session.commit()

        payload = {
            'event_id': self.event_id,
            'target_audience': 'checked_in',
            'tag_id': tag.id,
            'translations': [{'language': 'en', 'title': 'Accommodation Info', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['audience_count'], 0)

    def test_tag_filter_with_unknown_tag_id_returns_error(self):
        payload = {
            'event_id': self.event_id,
            'tag_id': 999999,
            'translations': [{'language': 'en', 'title': 'Hi', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 404)

    def test_tag_filter_with_tag_from_another_event_returns_error(self):
        other_event = self.add_event(key='OTHERTAGEVENT')
        other_tag = self.add_tag(event_id=other_event.id, tag_type='GRANT', names={'en': 'Other'})

        payload = {
            'event_id': self.event_id,
            'tag_id': other_tag.id,
            'translations': [{'language': 'en', 'title': 'Hi', 'body_markdown': 'body'}],
        }
        resp = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        self.assertEqual(resp.status_code, 404)

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


class AnnouncementQueueingTest(ApiTestCase):
    """Sending an announcement must queue delivery, never perform it inline."""

    def setUp(self):
        super().setUp()
        event = self.add_event(key='QUEUE2025')
        self.event_id = event.id

        comms = self.add_user('comms@test.com')
        self.add_event_role('comms-officer', comms.id, self.event_id)

        self.attendee1_id = self.add_user('a1@test.com').id
        self.attendee2_id = self.add_user('a2@test.com').id
        for user_id in (self.attendee1_id, self.attendee2_id):
            _invited_guest(self.event_id, user_id)
            _checkin(self.event_id, user_id)

        # Authenticating issues a request, which tears down the session and
        # detaches everything above, so it has to come last.
        self.comms_header = self.get_auth_header_for('comms@test.com')

    def _send(self, critical=False, translations=None, **extra):
        payload = {
            'event_id': self.event_id,
            'translations': translations or [
                {'language': 'en', 'title': 'Fire drill', 'body_markdown': 'Please leave.'},
            ],
            'critical': critical,
        }
        payload.update(extra)
        response = self.app.post(
            '/api/v1/announcement',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        return response, json.loads(response.data)

    def _messages(self, channel=None):
        query = db.session.query(OutboxMessage).filter(OutboxMessage.source_type == 'announcement')
        if channel:
            query = query.filter(OutboxMessage.channel == channel)
        return query.all()

    @patch('app.utils.emailer.smtplib.SMTP')
    def test_sending_opens_no_smtp_connection(self, mock_smtp):
        response, _ = self._send(critical=True)

        self.assertEqual(response.status_code, 201)
        mock_smtp.assert_not_called()

    def test_a_critical_announcement_queues_email_and_push_per_recipient(self):
        _, data = self._send(critical=True)

        self.assertEqual(data['audience_count'], 2)
        self.assertEqual(data['queued_count'], 4)
        self.assertEqual(len(self._messages(OutboxChannel.EMAIL)), 2)
        self.assertEqual(len(self._messages(OutboxChannel.PUSH)), 2)

    def test_a_non_critical_announcement_queues_push_only(self):
        _, data = self._send(critical=False)

        self.assertEqual(data['queued_count'], 2)
        self.assertEqual(self._messages(OutboxChannel.EMAIL), [])
        self.assertEqual(len(self._messages(OutboxChannel.PUSH)), 2)

    def test_queued_messages_start_pending_and_addressed(self):
        self._send(critical=True)

        recipients = sorted(m.recipient for m in self._messages(OutboxChannel.EMAIL))
        self.assertEqual(recipients, ['a1@test.com', 'a2@test.com'])
        for message in self._messages(OutboxChannel.EMAIL):
            self.assertEqual(message.status, OutboxStatus.PENDING)
            self.assertEqual(message.event_id, self.event_id)
            self.assertEqual(message.sender_email, 'contact@org.com')

    def test_queued_push_carries_a_usable_payload(self):
        """Bulk insert must round-trip the JSON payload, or push delivers nothing."""
        _, data = self._send()

        payload = self._messages(OutboxChannel.PUSH)[0].payload
        self.assertEqual(payload['title'], 'Fire drill')
        self.assertEqual(payload['body'], 'Please leave.')
        self.assertEqual(payload['url'],
                         '/QUEUE2025/event-app/announcements/{}'.format(data['id']))
        self.assertEqual(payload['tag'], 'ann-{}'.format(data['id']))

    def test_the_inbox_is_populated_before_anything_is_delivered(self):
        """Receipts are the inbox, so they can't wait on the worker."""
        _, data = self._send(critical=True)

        receipts = (db.session.query(AnnouncementReceipt)
                    .filter_by(announcement_id=data['id']).all())
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(r.delivered_at is not None for r in receipts))

    def test_each_recipient_is_queued_their_own_language(self):
        db.session.query(AppUser).filter_by(id=self.attendee1_id).update(
            {'user_primaryLanguage': 'fr'})
        db.session.commit()

        self._send(critical=True, translations=[
            {'language': 'en', 'title': 'Hello', 'body_markdown': 'Hello body'},
            {'language': 'fr', 'title': 'Bonjour', 'body_markdown': 'Corps Bonjour'},
        ])

        subjects = {m.recipient: m.subject for m in self._messages(OutboxChannel.EMAIL)}
        self.assertEqual(subjects['a1@test.com'], 'Bonjour')
        self.assertEqual(subjects['a2@test.com'], 'Hello')

    def test_resending_the_same_announcement_does_not_duplicate_messages(self):
        _, data = self._send(critical=True)
        ann = AnnouncementRepository.get_by_id(data['id'])
        event = db.session.query(Event).get(self.event_id)

        queued = _enqueue(ann, event, critical=True, target_audience='checked_in')[1]

        self.assertEqual(queued, 0)
        self.assertEqual(len(self._messages()), 4)

    def test_deleting_an_announcement_unqueues_its_messages(self):
        _, data = self._send(critical=True)

        response = self.app.delete(
            '/api/v1/announcement/{}?event_id={}'.format(data['id'], self.event_id),
            headers=self.comms_header,
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self._messages(), [])

    def test_admin_dashboard_reports_queue_progress(self):
        self._send(critical=True)

        response = self.app.get(
            '/api/v1/announcement/admin?event_id={}'.format(self.event_id),
            headers=self.comms_header,
        )
        announcement = json.loads(response.data)[0]

        self.assertEqual(announcement['email_delivery'], {'queued': 2, 'sent': 0, 'skipped': 0, 'failed': 0})
        self.assertEqual(announcement['push_delivery'], {'queued': 2, 'sent': 0, 'skipped': 0, 'failed': 0})

    @patch('app.utils.emailer.DEBUG', False)
    @patch('app.utils.emailer.smtplib.SMTP')
    def test_the_worker_delivers_what_sending_queued(self, mock_smtp):
        self._send(critical=True)

        response = self.app.post('/api/v1/tasks/outbox', headers={'X-Appengine-Cron': 'true'})

        summary = json.loads(response.data)
        self.assertEqual(summary['sent'], 2)      # two emails
        self.assertEqual(summary['skipped'], 2)   # two pushes, no subscriptions registered
        self.assertEqual(mock_smtp.call_count, 1)

        admin = self.app.get(
            '/api/v1/announcement/admin?event_id={}'.format(self.event_id),
            headers=self.comms_header,
        )
        announcement = json.loads(admin.data)[0]
        self.assertEqual(announcement['email_delivery']['sent'], 2)
        self.assertEqual(announcement['email_delivery']['queued'], 0)

    # --- Resend ---

    def _resend(self, announcement_id, **extra):
        payload = {'event_id': self.event_id}
        payload.update(extra)
        response = self.app.post(
            '/api/v1/announcement/{}/resend'.format(announcement_id),
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.comms_header,
        )
        return response, json.loads(response.data)

    def _set_status(self, channel, status, recipient=None):
        query = (db.session.query(OutboxMessage)
                 .filter(OutboxMessage.channel == channel))
        if recipient:
            query = query.filter(OutboxMessage.recipient == recipient)
        for message in query.all():
            message.status = status
            message.attempts = 3
            message.last_error = 'boom'
        db.session.commit()

    def test_resend_queues_nothing_when_everything_is_already_in_flight(self):
        _, data = self._send(critical=True)

        response, result = self._resend(data['id'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['queued_count'], 0)
        self.assertEqual(result['retried_count'], 0)
        self.assertEqual(len(self._messages()), 4)

    def test_resend_never_re_sends_to_someone_already_delivered(self):
        """The safety property: pressing resend can't duplicate a delivered email."""
        _, data = self._send(critical=True)
        self._set_status(OutboxChannel.EMAIL, OutboxStatus.SENT)

        _, result = self._resend(data['id'])

        self.assertEqual(result['queued_count'], 0)
        self.assertEqual(result['retried_count'], 0)
        emails = self._messages(OutboxChannel.EMAIL)
        self.assertEqual(len(emails), 2)
        self.assertTrue(all(m.status == OutboxStatus.SENT for m in emails))

    def test_resend_retries_failed_messages(self):
        _, data = self._send(critical=True)
        self._set_status(OutboxChannel.EMAIL, OutboxStatus.SENT, recipient='a1@test.com')
        self._set_status(OutboxChannel.EMAIL, OutboxStatus.FAILED, recipient='a2@test.com')

        _, result = self._resend(data['id'])

        self.assertEqual(result['retried_count'], 1)
        by_recipient = {m.recipient: m for m in self._messages(OutboxChannel.EMAIL)}
        self.assertEqual(by_recipient['a1@test.com'].status, OutboxStatus.SENT)
        retried = by_recipient['a2@test.com']
        self.assertEqual(retried.status, OutboxStatus.PENDING)
        self.assertEqual(retried.attempts, 0)
        self.assertIsNone(retried.last_error)

    def test_resend_retries_push_that_had_no_device(self):
        _, data = self._send()
        self._set_status(OutboxChannel.PUSH, OutboxStatus.SKIPPED)

        _, result = self._resend(data['id'])

        self.assertEqual(result['retried_count'], 2)
        self.assertTrue(all(m.status == OutboxStatus.PENDING
                            for m in self._messages(OutboxChannel.PUSH)))

    def test_resend_reaches_guests_who_joined_after_the_original_send(self):
        _, data = self._send(critical=True, target_audience='guest_list')
        latecomer = self.add_user('late@test.com')
        _invited_guest(self.event_id, latecomer.id)

        _, result = self._resend(data['id'])

        self.assertEqual(result['audience_count'], 3)
        self.assertEqual(result['queued_count'], 2)  # one email + one push
        recipients = sorted(m.recipient for m in self._messages(OutboxChannel.EMAIL))
        self.assertEqual(recipients, ['a1@test.com', 'a2@test.com', 'late@test.com'])

    def test_resend_reuses_the_audience_recorded_on_the_announcement(self):
        """A checked-in-only send must not silently widen to the guest list."""
        not_checked_in = self.add_user('a3@test.com')
        _invited_guest(self.event_id, not_checked_in.id)
        _, data = self._send(critical=True, target_audience='checked_in')

        _, result = self._resend(data['id'])

        self.assertEqual(result['audience_count'], 2)
        self.assertEqual(result['queued_count'], 0)

    def test_resend_can_widen_the_audience_to_the_guest_list(self):
        not_checked_in = self.add_user('a3@test.com')
        _invited_guest(self.event_id, not_checked_in.id)
        _, data = self._send(critical=True, target_audience='checked_in')

        _, result = self._resend(data['id'], target_audience='guest_list')

        self.assertEqual(result['audience_count'], 3)
        self.assertEqual(result['queued_count'], 2)

    def test_resend_of_a_legacy_announcement_infers_critical_from_its_email(self):
        """Announcements predating the stored flag still resend as they were sent."""
        _, data = self._send(critical=True)
        db.session.query(Announcement).filter_by(id=data['id']).update(
            {'critical': None, 'target_audience': None})
        db.session.commit()
        # Simulate a send that was cut short: drop one guest's messages entirely.
        (db.session.query(OutboxMessage)
         .filter(OutboxMessage.recipient == 'a2@test.com').delete(synchronize_session=False))
        (db.session.query(OutboxMessage)
         .filter(OutboxMessage.user_id == self.attendee2_id,
                 OutboxMessage.channel == OutboxChannel.PUSH).delete(synchronize_session=False))
        db.session.commit()

        _, result = self._resend(data['id'])

        self.assertEqual(result['queued_count'], 2)
        recipients = sorted(m.recipient for m in self._messages(OutboxChannel.EMAIL))
        self.assertEqual(recipients, ['a1@test.com', 'a2@test.com'])

    def test_resend_of_a_legacy_non_critical_announcement_stays_push_only(self):
        _, data = self._send(critical=False)
        db.session.query(Announcement).filter_by(id=data['id']).update({'critical': None})
        db.session.commit()

        self._resend(data['id'])

        self.assertEqual(self._messages(OutboxChannel.EMAIL), [])

    def test_resend_requires_a_comms_officer(self):
        _, data = self._send()
        outsider_header = self.get_auth_header_for('a1@test.com')

        response = self.app.post(
            '/api/v1/announcement/{}/resend'.format(data['id']),
            data=json.dumps({'event_id': self.event_id}),
            content_type='application/json',
            headers=outsider_header,
        )

        self.assertEqual(response.status_code, 403)

    def test_resend_of_an_unknown_announcement_is_a_404(self):
        response, _ = self._resend(9999)

        self.assertEqual(response.status_code, 404)

    @patch('app.utils.emailer.DEBUG', False)
    @patch('app.utils.emailer.smtplib.SMTP')
    def test_resent_messages_are_actually_delivered_by_the_worker(self, mock_smtp):
        _, data = self._send(critical=True)
        self._set_status(OutboxChannel.EMAIL, OutboxStatus.FAILED)
        self._resend(data['id'])

        self.app.post('/api/v1/tasks/outbox', headers={'X-Appengine-Cron': 'true'})

        self.assertEqual(mock_smtp.return_value.sendmail.call_count, 2)
        self.assertTrue(all(m.status == OutboxStatus.SENT
                            for m in self._messages(OutboxChannel.EMAIL)))

    def test_a_guest_list_send_reaches_guests_who_never_checked_in(self):
        not_checked_in = self.add_user('a3@test.com')
        _invited_guest(self.event_id, not_checked_in.id)

        _, data = self._send(critical=True, target_audience='guest_list')

        self.assertEqual(data['audience_count'], 3)
        recipients = sorted(m.recipient for m in self._messages(OutboxChannel.EMAIL))
        self.assertEqual(recipients, ['a1@test.com', 'a2@test.com', 'a3@test.com'])


if __name__ == '__main__':
    unittest.main()
