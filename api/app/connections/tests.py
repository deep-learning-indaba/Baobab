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
