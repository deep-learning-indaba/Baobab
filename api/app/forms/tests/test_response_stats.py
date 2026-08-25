from datetime import datetime, timedelta

from app import db
from app.forms.models import Form, FormResponse
from app.utils.testing import ApiTestCase


class TestFormResponseStatsAPI(ApiTestCase):

    def seed_static_data(self):
        # Capture ids before any request - db.session detaches after.
        admin = self.add_user('admin@example.com', 'Admin', 'User', password='password123')
        self.admin_id = admin.id
        event = self.add_event()
        self.event_id = event.id
        self.add_event_role('admin', admin.id, event.id)
        other_user = self.add_user('nonadmin@example.com', 'Non', 'Admin', password='password123')
        self.other_user_id = other_user.id

        self.admin_headers = self.get_auth_header_for('admin@example.com', 'password123')
        self.other_headers = self.get_auth_header_for('nonadmin@example.com', 'password123')

    def _create_form(self):
        form = Form(event_id=self.event_id, created_by_user_id=self.admin_id, is_open=True)
        db.session.add(form)
        db.session.commit()
        return form

    def _add_response(self, form, user, is_submitted=False, is_withdrawn=False,
                       started_timestamp=None, submitted_timestamp=None):
        response = FormResponse(form_id=form.id, user_id=user.id)
        if started_timestamp:
            response.started_timestamp = started_timestamp
        response.is_submitted = is_submitted
        response.submitted_timestamp = submitted_timestamp
        response.is_withdrawn = is_withdrawn
        db.session.add(response)
        db.session.commit()
        return response

    def _get_stats(self, form_id, headers=None):
        return self.app.get(
            f'/api/v1/forms/{form_id}/responses/stats?event_id={self.event_id}',
            headers=headers or self.admin_headers
        )

    def test_stats_with_no_responses(self):
        self.seed_static_data()
        form = self._create_form()

        resp = self._get_stats(form.id)

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['submitted'], 0)
        self.assertEqual(data['draft'], 0)
        self.assertEqual(data['withdrawn'], 0)
        self.assertEqual(data['submission_rate'], 0)
        self.assertIsNone(data['avg_completion_seconds'])
        self.assertIsNone(data['last_submitted_timestamp'])

    def test_stats_counts_by_status(self):
        self.seed_static_data()
        form = self._create_form()

        u1 = self.add_user('u1@example.com', 'A', 'One', password='password123')
        u2 = self.add_user('u2@example.com', 'B', 'Two', password='password123')
        u3 = self.add_user('u3@example.com', 'C', 'Three', password='password123')
        u4 = self.add_user('u4@example.com', 'D', 'Four', password='password123')

        self._add_response(form, u1, is_submitted=True, submitted_timestamp=datetime.now())
        self._add_response(form, u2, is_submitted=True, submitted_timestamp=datetime.now())
        self._add_response(form, u3, is_submitted=False)
        self._add_response(form, u4, is_submitted=False, is_withdrawn=True)

        resp = self._get_stats(form.id)

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 4)
        self.assertEqual(data['submitted'], 2)
        self.assertEqual(data['draft'], 1)
        self.assertEqual(data['withdrawn'], 1)
        self.assertEqual(data['submission_rate'], 50.0)

    def test_stats_withdrawn_after_submit_counts_as_withdrawn_not_submitted(self):
        # Matches the per-row status badge: withdrawn wins over submitted.
        self.seed_static_data()
        form = self._create_form()
        user = self.add_user('u1@example.com', 'A', 'One', password='password123')

        self._add_response(form, user, is_submitted=True, is_withdrawn=True,
                            submitted_timestamp=datetime.now())

        resp = self._get_stats(form.id)

        data = resp.get_json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['submitted'], 0)
        self.assertEqual(data['withdrawn'], 1)

    def test_stats_average_completion_time_and_last_submission(self):
        self.seed_static_data()
        form = self._create_form()
        u1 = self.add_user('u1@example.com', 'A', 'One', password='password123')
        u2 = self.add_user('u2@example.com', 'B', 'Two', password='password123')

        start = datetime(2026, 1, 1, 12, 0, 0)
        self._add_response(
            form, u1, is_submitted=True,
            started_timestamp=start, submitted_timestamp=start + timedelta(hours=1)
        )
        self._add_response(
            form, u2, is_submitted=True,
            started_timestamp=start, submitted_timestamp=start + timedelta(hours=2)
        )

        resp = self._get_stats(form.id)

        data = resp.get_json()
        self.assertEqual(data['avg_completion_seconds'], timedelta(hours=1.5).total_seconds())
        self.assertEqual(data['last_submitted_timestamp'], (start + timedelta(hours=2)).isoformat())

    def test_stats_excludes_draft_and_withdrawn_from_completion_time(self):
        self.seed_static_data()
        form = self._create_form()
        u1 = self.add_user('u1@example.com', 'A', 'One', password='password123')
        u2 = self.add_user('u2@example.com', 'B', 'Two', password='password123')

        start = datetime(2026, 1, 1, 12, 0, 0)
        # Draft: no submitted_timestamp.
        self._add_response(form, u1, is_submitted=False, started_timestamp=start)
        # Withdrawn-after-submit: excluded from completion time too.
        self._add_response(
            form, u2, is_submitted=True, is_withdrawn=True,
            started_timestamp=start, submitted_timestamp=start + timedelta(hours=10)
        )

        resp = self._get_stats(form.id)

        data = resp.get_json()
        self.assertIsNone(data['avg_completion_seconds'])
        self.assertIsNone(data['last_submitted_timestamp'])

    def test_stats_requires_event_admin(self):
        self.seed_static_data()
        form = self._create_form()

        resp = self._get_stats(form.id, headers=self.other_headers)

        self.assertEqual(resp.status_code, 403)

    def test_stats_returns_404_for_unknown_form(self):
        self.seed_static_data()

        resp = self._get_stats(999999)

        self.assertEqual(resp.status_code, 404)
