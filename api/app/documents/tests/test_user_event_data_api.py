import json

from app import db
from app.documents.tests.test_api import DocumentApiTestCase
from app.documents.models import UserEventData


class TestUserEventDataGrid(DocumentApiTestCase):

    def test_grid_includes_the_whole_population_not_just_people_with_data(self):
        second_user = self.add_user('second@example.com', 'Second', 'User')
        self.add_offer(self.event, self.user)
        self.add_offer(self.event, second_user)
        self.set_user_data(self.event, self.user, 'hostel', 'Blue House')

        resp = self.app.get(
            f'/api/v1/events/{self.event_id}/documents/user-data/grid', headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['keys'], ['hostel'])
        user_ids = {row['user_id'] for row in body['rows']}
        self.assertIn(self.user_id, user_ids)
        self.assertIn(second_user.id, user_ids)
        row = next(r for r in body['rows'] if r['user_id'] == self.user_id)
        self.assertEqual(row['values']['hostel'], 'Blue House')

    def test_person_with_data_but_no_offer_still_appears(self):
        self.set_user_data(self.event, self.user, 'hostel', 'Blue House')

        resp = self.app.get(
            f'/api/v1/events/{self.event_id}/documents/user-data/grid', headers=self.headers)

        body = json.loads(resp.data)
        self.assertIn(self.user_id, {row['user_id'] for row in body['rows']})


class TestUserEventDataExport(DocumentApiTestCase):

    def test_export_only_includes_people_with_data(self):
        second_user = self.add_user('second@example.com', 'Second', 'User')
        second_user_email = second_user.email
        self.add_offer(self.event, self.user)
        self.add_offer(self.event, second_user)
        self.set_user_data(self.event, self.user, 'hostel', 'Blue House')

        resp = self.app.get(
            f'/api/v1/events/{self.event_id}/documents/user-data/export', headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        content = resp.data.decode('utf-8')
        self.assertIn('email,hostel', content)
        self.assertIn(f'{self.user_email},Blue House', content)
        self.assertNotIn(second_user_email, content)


class TestUserEventDataImport(DocumentApiTestCase):

    def test_preview_does_not_write_anything(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': f'email,hostel\n{self.user_email},Blue House\n', 'apply': False},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['applied'], False)
        self.assertEqual(body['changed_count'], 1)
        self.assertEqual(body['rows'][0]['changes']['hostel'], {'old': None, 'new': 'Blue House'})
        self.assertEqual(db.session.query(UserEventData).count(), 0)

    def test_apply_writes_the_changes(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': f'email,hostel\n{self.user_email},Blue House\n', 'apply': True},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['applied'], True)
        row = db.session.query(UserEventData).filter_by(
            event_id=self.event_id, user_id=self.user_id, key='hostel').first()
        self.assertEqual(row.value, 'Blue House')

    def test_unchanged_value_is_not_in_the_diff(self):
        self.set_user_data(self.event, self.user, 'hostel', 'Blue House')

        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': f'email,hostel\n{self.user_email},Blue House\n', 'apply': False},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['changed_count'], 0)

    def test_unmatched_email_is_reported_not_silently_dropped(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': 'email,hostel\nnobody@example.com,Blue House\n', 'apply': False},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['unmatched_emails'], ['nobody@example.com'])
        self.assertEqual(body['changed_count'], 0)

    def test_missing_email_column_rejected(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': 'name,hostel\nAmina,Blue House\n', 'apply': False},
        )
        self.assertEqual(resp.status_code, 400)

    def test_apply_updates_an_existing_value(self):
        self.set_user_data(self.event, self.user, 'hostel', 'Red House')

        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/user-data/import',
            {'csv': f'email,hostel\n{self.user_email},Blue House\n', 'apply': True},
        )

        self.assertEqual(resp.status_code, 200)
        row = db.session.query(UserEventData).filter_by(
            event_id=self.event_id, user_id=self.user_id, key='hostel').first()
        self.assertEqual(row.value, 'Blue House')
        self.assertEqual(db.session.query(UserEventData).filter_by(
            event_id=self.event_id, user_id=self.user_id, key='hostel').count(), 1)
