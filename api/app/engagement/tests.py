import json
from datetime import datetime, timedelta

from app import db
from app.utils.testing import ApiTestCase
from app.engagement.models import EngagementEvent
from app.engagement.repository import EngagementRepository


class EngagementInstallAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.user = self.add_user('installer@test.com')
        self.user_id = self.user.id
        self.event = self.add_event(
            {'en': 'Install Event'}, {'en': 'Desc'},
            datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60), 'INSTEV'
        )
        self.event_id = self.event.id

    def test_records_install_event_for_current_user(self):
        self.seed_static_data()
        header = self.get_auth_header_for('installer@test.com')
        response = self.app.post(
            '/api/v1/engagement/install',
            data=json.dumps({'event_id': self.event_id}),
            content_type='application/json', headers=header
        )
        self.assertEqual(response.status_code, 201)

        rows = db.session.query(EngagementEvent).filter_by(
            event_id=self.event_id, user_id=self.user_id, event_type='app_installed'
        ).all()
        self.assertEqual(len(rows), 1)

    def test_missing_event_id_returns_400(self):
        self.seed_static_data()
        header = self.get_auth_header_for('installer@test.com')
        response = self.app.post(
            '/api/v1/engagement/install',
            data=json.dumps({}),
            content_type='application/json', headers=header
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_event_returns_404(self):
        self.seed_static_data()
        header = self.get_auth_header_for('installer@test.com')
        response = self.app.post(
            '/api/v1/engagement/install',
            data=json.dumps({'event_id': 999999}),
            content_type='application/json', headers=header
        )
        self.assertEqual(response.status_code, 404)

    def test_requires_auth(self):
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/engagement/install',
            data=json.dumps({'event_id': self.event_id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)


class EngagementRepositoryTest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.user1 = self.add_user('user1@test.com')
        self.user2 = self.add_user('user2@test.com')
        self.event = self.add_event(
            {'en': 'Install Event'}, {'en': 'Desc'},
            datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60), 'INSTEV'
        )

    def test_count_distinct_users_ignores_duplicate_rows_from_same_user(self):
        self.seed_static_data()
        EngagementRepository.record(self.event, self.user1.id, 'app_installed')
        EngagementRepository.record(self.event, self.user1.id, 'app_installed')
        EngagementRepository.record(self.event, self.user2.id, 'app_installed')

        self.assertEqual(EngagementRepository.count_distinct_users(self.event.id, 'app_installed'), 2)
        self.assertEqual(EngagementRepository.count_distinct_users(self.event.id, 'other_type'), 0)
