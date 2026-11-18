import json
import unittest
from unittest.mock import patch

from app import db
from app.connections.models import Connection, ConnectionStatus, ConnectionReport
from app.connections.repository import ConnectionRepository
from app.attendance.models import EventQRToken, Checkin
from app.attendance.repository import QRTokenRepository
from app.invitedGuest.models import InvitedGuest
from app.utils.testing import ApiTestCase


def _invited_guest(event_id, user_id):
    ig = InvitedGuest(event_id=event_id, user_id=user_id, role='Guest')
    db.session.add(ig)
    db.session.commit()
    return ig


def _checkin(event_id, user_id):
    c = Checkin(event_id=event_id, user_id=user_id,
                checked_in_by_user_id=None, method='self', day=None)
    db.session.add(c)
    db.session.commit()
    return c


class ConnectionApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        event = self.add_event(key='CONN2025')
        self.event_id = event.id

        self.user_a = self.add_user('a@test.com')
        self.user_a_id = self.user_a.id
        self.user_b = self.add_user('b@test.com')
        self.user_b_id = self.user_b.id
        self.user_c = self.add_user('c@test.com')
        self.user_c_id = self.user_c.id
        self.non_guest = self.add_user('ng@test.com')
        self.non_guest_id = self.non_guest.id

        for uid in (self.user_a_id, self.user_b_id, self.user_c_id):
            _invited_guest(self.event_id, uid)
            _checkin(self.event_id, uid)

        self.token_a = QRTokenRepository.get_or_create(self.event_id, self.user_a_id).token
        self.token_b = QRTokenRepository.get_or_create(self.event_id, self.user_b_id).token

        self.hdr_a = self.get_auth_header_for('a@test.com')
        self.hdr_b = self.get_auth_header_for('b@test.com')
        self.hdr_c = self.get_auth_header_for('c@test.com')
        self.hdr_ng = self.get_auth_header_for('ng@test.com')

    # ── resolve ──────────────────────────────────────────────────────────────

    def test_resolve_returns_target_profile(self):
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t={}'.format(self.event_id, self.token_b),
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertFalse(data['is_self'])
        self.assertEqual(data['target']['user_id'], self.user_b_id)
        self.assertEqual(data['connection']['state'], 'none')

    def test_resolve_self_returns_is_self(self):
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t={}'.format(self.event_id, self.token_a),
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['is_self'])

    def test_resolve_invalid_token_returns_400(self):
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t=badtoken'.format(self.event_id),
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 400)

    def test_resolve_non_guest_returns_403(self):
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t={}'.format(self.event_id, self.token_b),
            headers=self.hdr_ng,
        )
        self.assertEqual(resp.status_code, 403)

    # ── connect ───────────────────────────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_a_scans_b_creates_pending(self, mock_push):
        resp = self.app.post(
            '/api/v1/connection',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 201)
        row = ConnectionRepository.get(self.event_id, self.user_a_id, self.user_b_id)
        self.assertIsNotNone(row)
        self.assertEqual(row.status, ConnectionStatus.PENDING)

        # B is the target of the scan, so B is the one who should be notified.
        mock_push.assert_called_once_with(self.user_b_id, {
            'title': 'New connection request',
            'body': '{} {} wants to connect with you.'.format(
                self.user_a.firstname, self.user_a.lastname),
            'url': '/CONN2025/app/connections',
        })

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_rescan_is_idempotent(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        resp = self.app.post(
            '/api/v1/connection',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 201)
        count = db.session.query(Connection).filter_by(
            event_id=self.event_id, from_user_id=self.user_a_id, to_user_id=self.user_b_id).count()
        self.assertEqual(count, 1)

    def test_cannot_connect_self(self):
        resp = self.app.post(
            '/api/v1/connection',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_a_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 400)

    def test_non_guest_cannot_connect(self):
        resp = self.app.post(
            '/api/v1/connection',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_ng,
        )
        self.assertEqual(resp.status_code, 403)

    # ── accept / reject ───────────────────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_b_accepts_makes_mutual_connected(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)

        resp = self.app.post(
            '/api/v1/connection/respond',
            data=json.dumps({'event_id': self.event_id, 'from_user_id': self.user_a_id, 'action': 'accept'}),
            content_type='application/json',
            headers=self.hdr_b,
        )
        self.assertEqual(resp.status_code, 200)

        row_ab = ConnectionRepository.get(self.event_id, self.user_a_id, self.user_b_id)
        row_ba = ConnectionRepository.get(self.event_id, self.user_b_id, self.user_a_id)
        self.assertEqual(row_ab.status, ConnectionStatus.CONNECTED)
        self.assertEqual(row_ba.status, ConnectionStatus.CONNECTED)

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_b_rejects_silently(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        resp = self.app.post(
            '/api/v1/connection/respond',
            data=json.dumps({'event_id': self.event_id, 'from_user_id': self.user_a_id, 'action': 'reject'}),
            content_type='application/json',
            headers=self.hdr_b,
        )
        self.assertEqual(resp.status_code, 200)
        row = ConnectionRepository.get(self.event_id, self.user_a_id, self.user_b_id)
        self.assertEqual(row.status, ConnectionStatus.REJECTED)

    # ── block ─────────────────────────────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_block_prevents_further_requests(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        self.app.post(
            '/api/v1/connection/respond',
            data=json.dumps({'event_id': self.event_id, 'from_user_id': self.user_a_id, 'action': 'block'}),
            content_type='application/json',
            headers=self.hdr_b,
        )
        row = ConnectionRepository.get(self.event_id, self.user_a_id, self.user_b_id)
        self.assertEqual(row.status, ConnectionStatus.BLOCKED)

        # A tries again — should get 403
        resp = self.app.post(
            '/api/v1/connection',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 403)

    # ── withdraw ──────────────────────────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_withdraw_sets_withdrawn(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        resp = self.app.post(
            '/api/v1/connection/withdraw',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 200)
        row = ConnectionRepository.get(self.event_id, self.user_a_id, self.user_b_id)
        self.assertEqual(row.status, ConnectionStatus.WITHDRAWN)

    def test_withdraw_nonexistent_returns_404(self):
        resp = self.app.post(
            '/api/v1/connection/withdraw',
            data=json.dumps({'event_id': self.event_id, 'to_user_id': self.user_b_id}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 404)

    # ── list ─────────────────────────────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_list_shows_correct_sections(self, mock_push):
        # A→B = PENDING, B→C = CONNECTED, C→B = CONNECTED
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        ConnectionRepository.set_status(self.event_id, self.user_b_id, self.user_c_id, ConnectionStatus.CONNECTED)
        ConnectionRepository.set_status(self.event_id, self.user_c_id, self.user_b_id, ConnectionStatus.CONNECTED)

        resp = self.app.get(
            '/api/v1/connection/list?event_id={}'.format(self.event_id),
            headers=self.hdr_b,
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        # B sees A's pending request as incoming
        self.assertEqual(len(data['incoming']), 1)
        self.assertEqual(data['incoming'][0]['user_id'], self.user_a_id)
        # B sees connection with C
        connected_ids = {c['user_id'] for c in data['connected']}
        self.assertIn(self.user_c_id, connected_ids)

    # ── report ────────────────────────────────────────────────────────────────

    def test_report_creates_row(self):
        resp = self.app.post(
            '/api/v1/connection/report',
            data=json.dumps({'event_id': self.event_id, 'reported_user_id': self.user_b_id, 'reason': 'spam'}),
            content_type='application/json',
            headers=self.hdr_a,
        )
        self.assertEqual(resp.status_code, 201)
        row = db.session.query(ConnectionReport).filter_by(
            reporter_user_id=self.user_a_id, reported_user_id=self.user_b_id).first()
        self.assertIsNotNone(row)
        self.assertEqual(row.reason, 'spam')

    def _report(self, hdr, reported_id, **extra):
        body = {'event_id': self.event_id, 'reported_user_id': reported_id}
        body.update(extra)
        return self.app.post('/api/v1/connection/report', data=json.dumps(body),
                             content_type='application/json', headers=hdr)

    def test_report_default_category_and_body(self):
        resp = self._report(self.hdr_a, self.user_b_id)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'reported')
        row = db.session.query(ConnectionReport).get(data['id'])
        self.assertEqual(row.category, 'person')
        self.assertEqual(row.status, 'open')

    def test_report_photo_snapshots_photo(self):
        from app.profiles.models import MemberProfile
        db.session.add(MemberProfile(user_id=self.user_b_id, photo_url='a' * 32))
        db.session.commit()
        resp = self._report(self.hdr_a, self.user_b_id, category='photo')
        self.assertEqual(resp.status_code, 201)
        row = db.session.query(ConnectionReport).get(json.loads(resp.data)['id'])
        self.assertEqual(row.category, 'photo')
        self.assertEqual(row.reported_photo_url, 'a' * 32)

    def test_report_invalid_category(self):
        self.assertEqual(self._report(self.hdr_a, self.user_b_id, category='bogus').status_code, 400)

    def test_report_self(self):
        self.assertEqual(self._report(self.hdr_a, self.user_a_id).status_code, 400)

    def test_report_user_not_at_event(self):
        resp = self._report(self.hdr_a, self.non_guest_id)
        self.assertEqual(resp.status_code, 404)

    def test_report_reporter_not_guest(self):
        resp = self._report(self.hdr_ng, self.user_b_id)
        self.assertEqual(resp.status_code, 403)

    def test_report_duplicate_open_is_idempotent(self):
        first = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)
        resp = self._report(self.hdr_a, self.user_b_id, category='photo')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['id'], first['id'])
        self.assertEqual(db.session.query(ConnectionReport).count(), 1)

    def test_report_other_category_creates_new_row(self):
        self._report(self.hdr_a, self.user_b_id, category='photo')
        resp = self._report(self.hdr_a, self.user_b_id, category='profile')
        self.assertEqual(resp.status_code, 201)

    def test_report_after_dismissal_creates_new_row(self):
        first = json.loads(self._report(self.hdr_a, self.user_b_id).data)
        row = db.session.query(ConnectionReport).get(first['id'])
        row.status = 'dismissed'
        db.session.commit()
        resp = self._report(self.hdr_a, self.user_b_id)
        self.assertEqual(resp.status_code, 201)
        self.assertNotEqual(json.loads(resp.data)['id'], first['id'])

    # ── moderation queue ──────────────────────────────────────────────────────

    def _make_moderator(self, email, role):
        from app.events.models import EventRole
        user = self.add_user(email)
        db.session.add(EventRole(role, user.id, self.event_id))
        db.session.commit()
        return self.get_auth_header_for(email)

    def _queue(self, hdr, event_id=None):
        return self.app.get('/api/v1/connection/report?event_id={}'.format(event_id or self.event_id),
                            headers=hdr)

    def _resolve(self, action, hdr, report_id, event_id=None):
        return self.app.post(
            '/api/v1/connection/report/{}/{}'.format(report_id, action),
            data=json.dumps({'event_id': event_id or self.event_id}),
            content_type='application/json', headers=hdr)

    def _give_photo(self, user_id, photo):
        from app.profiles.models import MemberProfile
        db.session.add(MemberProfile(user_id=user_id, photo_url=photo, headline='hi', about='abt'))
        db.session.commit()

    def test_queue_as_comms_officer(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._give_photo(self.user_b_id, 'a' * 32)
        first = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo', reason='bad').data)['id']
        second = json.loads(self._report(self.hdr_c, self.user_b_id, category='profile').data)['id']
        resp = self._queue(hdr)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual([r['report_id'] for r in data], [first, second])
        r = data[0]
        self.assertEqual(r['category'], 'photo')
        self.assertEqual(r['reason'], 'bad')
        self.assertEqual(r['reporter']['user_id'], self.user_a_id)
        self.assertEqual(r['reported']['user_id'], self.user_b_id)
        self.assertEqual(r['reported']['photo_url'], 'a' * 32)
        self.assertEqual(r['reported']['headline'], 'hi')
        self.assertEqual(r['reported']['about'], 'abt')
        self.assertEqual(r['reported']['visibility'], 'community')
        self.assertEqual(r['reported_photo_url'], 'a' * 32)
        self.assertTrue(r['created_at'].endswith('Z'))

    def test_queue_user_without_profile(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._report(self.hdr_a, self.user_b_id)
        data = json.loads(self._queue(hdr).data)
        self.assertIsNone(data[0]['reported']['photo_url'])
        self.assertIsNone(data[0]['reported']['headline'])
        self.assertEqual(data[0]['reported']['visibility'], 'community')
        self.assertFalse(data[0]['photo_changed'])

    def test_queue_as_event_admin(self):
        hdr = self._make_moderator('adm@test.com', 'admin')
        self._report(self.hdr_a, self.user_b_id)
        resp = self._queue(hdr)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(json.loads(resp.data)), 1)

    def test_queue_as_guest_forbidden(self):
        self.assertEqual(self._queue(self.hdr_a).status_code, 403)

    def test_queue_role_in_other_event_forbidden(self):
        other = self.add_event(key='OTHER2025')
        other_id = other.id
        from app.events.models import EventRole
        user = self.add_user('oco@test.com')
        db.session.add(EventRole('comms-officer', user.id, other_id))
        db.session.commit()
        hdr = self.get_auth_header_for('oco@test.com')
        self.assertEqual(self._queue(hdr).status_code, 403)

    def test_photo_changed_flag(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._give_photo(self.user_b_id, 'a' * 32)
        self._report(self.hdr_a, self.user_b_id, category='photo')
        self.assertFalse(json.loads(self._queue(hdr).data)[0]['photo_changed'])
        from app.profiles.models import MemberProfile
        db.session.query(MemberProfile).filter_by(user_id=self.user_b_id).update({'photo_url': 'b' * 32})
        db.session.commit()
        data = json.loads(self._queue(hdr).data)
        self.assertTrue(data[0]['photo_changed'])
        self.assertEqual(data[0]['reported_photo_url'], 'a' * 32)
        self.assertEqual(data[0]['reported']['photo_url'], 'b' * 32)

    def test_dismiss_removes_from_queue(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        rid = json.loads(self._report(self.hdr_a, self.user_b_id).data)['id']
        resp = self._resolve('dismiss', hdr, rid)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(self._queue(hdr).data), [])
        row = db.session.query(ConnectionReport).get(rid)
        self.assertEqual(row.status, 'dismissed')
        self.assertIsNotNone(row.resolved_by_user_id)
        self.assertIsNotNone(row.resolved_at)

    def test_dismiss_already_resolved_is_idempotent(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        rid = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        self._resolve('remove-photo', hdr, rid)
        resp = self._resolve('dismiss', hdr, rid)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(db.session.query(ConnectionReport).get(rid).status, 'actioned')

    def test_dismiss_other_event_404(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        other = self.add_event(key='OTHER2025')
        other_id = other.id
        from app.events.models import EventRole
        admin = self.add_user('oadm@test.com')
        db.session.add(EventRole('admin', admin.id, other_id))
        db.session.commit()
        other_hdr = self.get_auth_header_for('oadm@test.com')
        rid = json.loads(self._report(self.hdr_a, self.user_b_id).data)['id']
        self.assertEqual(self._resolve('dismiss', other_hdr, rid, event_id=other_id).status_code, 404)
        self.assertEqual(self._resolve('dismiss', hdr, 99999).status_code, 404)
        self.assertEqual(db.session.query(ConnectionReport).get(rid).status, 'open')

    def test_resolve_as_guest_forbidden(self):
        rid = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        self.assertEqual(self._resolve('dismiss', self.hdr_c, rid).status_code, 403)
        self.assertEqual(self._resolve('remove-photo', self.hdr_c, rid).status_code, 403)
        self.assertEqual(db.session.query(ConnectionReport).get(rid).status, 'open')

    def test_remove_photo_actions_only_open_photo_reports(self):
        from app.profiles.models import MemberProfile
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._give_photo(self.user_b_id, 'a' * 32)
        p1 = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        p2 = json.loads(self._report(self.hdr_c, self.user_b_id, category='photo').data)['id']
        prof = json.loads(self._report(self.hdr_a, self.user_b_id, category='profile').data)['id']
        person = json.loads(self._report(self.hdr_a, self.user_b_id, category='person').data)['id']
        old = json.loads(self._report(self.hdr_c, self.user_a_id, category='photo').data)['id']
        resp = self._resolve('remove-photo', hdr, p1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['actioned_report_ids'], sorted([p1, p2]))
        profile = db.session.query(MemberProfile).filter_by(user_id=self.user_b_id).first()
        self.assertIsNone(profile.photo_url)
        self.assertIsNotNone(profile.photo_removed_at)
        status = {r.id: r.status for r in db.session.query(ConnectionReport).all()}
        self.assertEqual(status[p1], 'actioned')
        self.assertEqual(status[p2], 'actioned')
        self.assertEqual(status[prof], 'open')
        self.assertEqual(status[person], 'open')
        self.assertEqual(status[old], 'open')
        self.assertIsNotNone(db.session.query(ConnectionReport).get(p1).resolved_by_user_id)
        from app.engagement.models import EngagementEvent
        self.assertEqual(db.session.query(EngagementEvent).filter_by(
            event_type='profile_photo_moderated').count(), 1)

    def test_remove_photo_already_gone_returns_200(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._give_photo(self.user_b_id, None)
        rid = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        resp = self._resolve('remove-photo', hdr, rid)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['actioned_report_ids'], [rid])

    def test_remove_photo_on_profile_report_actions_it_too(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        self._give_photo(self.user_b_id, 'a' * 32)
        photo = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        prof = json.loads(self._report(self.hdr_a, self.user_b_id, category='profile').data)['id']
        resp = self._resolve('remove-photo', hdr, prof)
        self.assertEqual(json.loads(resp.data)['actioned_report_ids'], sorted([photo, prof]))

    def test_remove_photo_without_profile_row(self):
        hdr = self._make_moderator('co@test.com', 'comms-officer')
        rid = json.loads(self._report(self.hdr_a, self.user_b_id, category='photo').data)['id']
        self.assertEqual(self._resolve('remove-photo', hdr, rid).status_code, 200)

    # ── resolve shows connection state ────────────────────────────────────────

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_resolve_shows_outgoing_pending_state(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        token_b_id = self.token_b
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t={}'.format(self.event_id, token_b_id),
            headers=self.hdr_a,
        )
        data = json.loads(resp.data)
        self.assertEqual(data['connection']['state'], 'outgoing_pending')

    @patch('app.connections.api.push_to_user', return_value=0)
    def test_resolve_shows_blocked_neutral(self, mock_push):
        ConnectionRepository.upsert_request(self.event_id, self.user_a_id, self.user_b_id)
        ConnectionRepository.set_status(self.event_id, self.user_a_id, self.user_b_id, ConnectionStatus.BLOCKED)
        resp = self.app.get(
            '/api/v1/connection/resolve?event_id={}&t={}'.format(self.event_id, self.token_b),
            headers=self.hdr_a,
        )
        data = json.loads(resp.data)
        self.assertEqual(data['connection']['state'], 'blocked')


if __name__ == '__main__':
    unittest.main()
