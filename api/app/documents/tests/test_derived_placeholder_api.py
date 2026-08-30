import json

from app import db
from app.documents.tests.test_api import DocumentApiTestCase
from app.documents.models import DerivedPlaceholder


class TestDerivedPlaceholderCrud(DocumentApiTestCase):

    def test_create_and_list(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {
                'key': 'poster_sentence',
                'description': 'The presenting sentence',
                'rules': [
                    {'order': 1, 'condition_expression': {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'},
                     'texts': {'en': '{firstname} will present a poster.'}},
                    {'order': 2, 'condition_expression': None, 'texts': {'en': ''}},
                ],
            },
        )

        self.assertEqual(resp.status_code, 201)
        body = json.loads(resp.data)
        self.assertEqual(body['key'], 'poster_sentence')
        self.assertEqual(len(body['rules']), 2)
        self.assertTrue(body['rules'][1]['is_otherwise'])

        list_resp = self.app.get(
            f'/api/v1/events/{self.event_id}/documents/placeholders', headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(json.loads(list_resp.data)), 1)

    def test_key_is_normalised_to_lowercase(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'Poster_Sentence', 'rules': []},
        )
        self.assertEqual(json.loads(resp.data)['key'], 'poster_sentence')

    def test_duplicate_key_rejected(self):
        self.post_json(f'/api/v1/events/{self.event_id}/documents/placeholders',
                       {'key': 'dup', 'rules': []})
        resp = self.post_json(f'/api/v1/events/{self.event_id}/documents/placeholders',
                              {'key': 'dup', 'rules': []})
        self.assertEqual(resp.status_code, 409)

    def test_missing_key_rejected(self):
        resp = self.post_json(f'/api/v1/events/{self.event_id}/documents/placeholders',
                              {'rules': []})
        self.assertEqual(resp.status_code, 400)

    def test_otherwise_rule_must_be_last(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'bad', 'rules': [
                {'order': 1, 'condition_expression': None, 'texts': {'en': ''}},
                {'order': 2, 'condition_expression': {'key': 'x', 'operator': 'IS_NOT_EMPTY'}, 'texts': {'en': 'x'}},
            ]},
        )
        self.assertEqual(resp.status_code, 400)

    def test_at_most_one_otherwise_rule(self):
        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'bad', 'rules': [
                {'order': 1, 'condition_expression': None, 'texts': {'en': ''}},
                {'order': 2, 'condition_expression': None, 'texts': {'en': ''}},
            ]},
        )
        self.assertEqual(resp.status_code, 400)

    def test_cycle_between_two_placeholders_rejected(self):
        self.post_json(f'/api/v1/events/{self.event_id}/documents/placeholders',
                       {'key': 'a', 'rules': [
                           {'order': 1, 'condition_expression': None, 'texts': {'en': 'plain'}}]})

        resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'b', 'rules': [
                {'order': 1, 'condition_expression': None, 'texts': {'en': 'refers to {a}'}}]},
        )
        self.assertEqual(resp.status_code, 201)

        # Now edit 'a' to refer back to 'b', closing the loop.
        derived_a = db.session.query(DerivedPlaceholder).filter_by(event_id=self.event_id, key='a').first()
        derived_a_id = derived_a.id

        cycle_resp = self.put_json(
            f'/api/v1/documents/placeholders/{derived_a_id}',
            {'rules': [{'order': 1, 'condition_expression': None, 'texts': {'en': 'refers to {b}'}}]},
        )
        self.assertEqual(cycle_resp.status_code, 400)

    def test_update_replaces_rules(self):
        create_resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'greeting', 'rules': [
                {'order': 1, 'condition_expression': None, 'texts': {'en': 'Hello'}}]},
        )
        derived_id = json.loads(create_resp.data)['id']

        update_resp = self.put_json(
            f'/api/v1/documents/placeholders/{derived_id}',
            {'description': 'Updated', 'rules': [
                {'order': 1, 'condition_expression': None, 'texts': {'en': 'Hi there'}}]},
        )

        self.assertEqual(update_resp.status_code, 200)
        body = json.loads(update_resp.data)
        self.assertEqual(body['description'], 'Updated')
        self.assertEqual(len(body['rules']), 1)
        self.assertEqual(body['rules'][0]['texts']['en'], 'Hi there')

    def test_key_cannot_be_changed_on_update(self):
        create_resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'original_key', 'rules': []},
        )
        derived_id = json.loads(create_resp.data)['id']

        update_resp = self.put_json(
            f'/api/v1/documents/placeholders/{derived_id}',
            {'key': 'renamed_key', 'rules': []},
        )

        self.assertEqual(json.loads(update_resp.data)['key'], 'original_key')

    def test_delete(self):
        create_resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'to_delete', 'rules': []},
        )
        derived_id = json.loads(create_resp.data)['id']

        delete_resp = self.app.delete(
            f'/api/v1/documents/placeholders/{derived_id}', headers=self.headers)

        self.assertEqual(delete_resp.status_code, 204)
        self.assertIsNone(db.session.query(DerivedPlaceholder).filter_by(id=derived_id).first())

    def test_nonexistent_404(self):
        put_resp = self.put_json('/api/v1/documents/placeholders/99999', {'rules': []})
        self.assertEqual(put_resp.status_code, 404)

    def test_non_admin_forbidden(self):
        other_user = self.add_user('outsider@example.com', 'Out', 'Sider')
        other_user_email = other_user.email
        create_resp = self.post_json(
            f'/api/v1/events/{self.event_id}/documents/placeholders',
            {'key': 'secure', 'rules': []},
        )
        derived_id = json.loads(create_resp.data)['id']

        resp = self.put_json(
            f'/api/v1/documents/placeholders/{derived_id}', {'rules': []},
            headers=self.get_auth_header_for(other_user_email),
        )
        self.assertEqual(resp.status_code, 403)
