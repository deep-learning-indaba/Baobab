"""Cross-event isolation and download access control.

Authorisation on every template-scoped endpoint is derived from the
template's own event_id (via document_admin_required in app/documents/mixins.py),
never from a caller-supplied one - the same hazard app/forms/mixins.py's
verify_form_event guards against: an admin of event A must not be able to
read or mutate event B's document templates just by knowing a template id.
"""
import json

from app.documents.tests.base import DocumentsTestCase


class DocumentAuthorizationTestCase(DocumentsTestCase):
    def setUp(self):
        super().setUp()
        # self.user is this event's admin.
        self.add_event_role('admin', self.user_id, self.event_id)
        self.owner_headers = self.get_auth_header_for(self.user_email)

        # An unrelated event with its own admin.
        other_event = self.add_event(key='OTHEREVT')
        self.other_event_id = other_event.id
        other_admin = self.add_user('otheradmin@example.com', 'Other', 'Admin', password='pw')
        self.add_event_role('admin', other_admin.id, self.other_event_id)
        self.other_admin_headers = self.get_auth_header_for('otheradmin@example.com', 'pw')

        # A plain registered user with no admin role anywhere.
        plain_user = self.add_user('plain@example.com', 'Plain', 'User', password='pw')
        self.plain_user_id = plain_user.id
        self.plain_headers = self.get_auth_header_for('plain@example.com', 'pw')

        self.document_template = self.make_document_template()
        self.document_template_id = self.document_template.id


class TestTemplateCrossEventAuthorization(DocumentAuthorizationTestCase):

    def test_other_events_admin_cannot_read_this_templates(self):
        resp = self.app.get(f'/api/v1/documents/templates/{self.document_template_id}',
                             headers=self.other_admin_headers)
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_update_this_template(self):
        resp = self.app.put(
            f'/api/v1/documents/templates/{self.document_template_id}',
            data=json.dumps({'delivery_mode': 'link'}), content_type='application/json',
            headers=self.other_admin_headers,
        )
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_delete_this_template(self):
        resp = self.app.delete(f'/api/v1/documents/templates/{self.document_template_id}',
                                headers=self.other_admin_headers)
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_add_a_variant(self):
        resp = self.app.post(
            f'/api/v1/documents/templates/{self.document_template_id}/variants',
            data=json.dumps({'google_file_url': 'https://docs.google.com/document/d/abc/edit'}),
            content_type='application/json', headers=self.other_admin_headers,
        )
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_replace_form_links(self):
        resp = self.app.put(
            f'/api/v1/documents/templates/{self.document_template_id}/forms',
            data=json.dumps({'form_links': []}), content_type='application/json',
            headers=self.other_admin_headers,
        )
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_preview(self):
        resp = self.app.post(
            f'/api/v1/documents/templates/{self.document_template_id}/preview',
            data=json.dumps({'user_id': self.user_id}), content_type='application/json',
            headers=self.other_admin_headers,
        )
        self.assertEqual(resp.status_code, 403)

    def test_plain_user_cannot_read_templates(self):
        resp = self.app.get(f'/api/v1/documents/templates/{self.document_template_id}',
                             headers=self.plain_headers)
        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_request_is_rejected(self):
        resp = self.app.get(f'/api/v1/documents/templates/{self.document_template_id}')
        self.assertEqual(resp.status_code, 401)

    def test_owner_admin_can_still_read_their_own_template(self):
        resp = self.app.get(f'/api/v1/documents/templates/{self.document_template_id}',
                             headers=self.owner_headers)
        self.assertEqual(resp.status_code, 200)

    def test_admin_endpoints_reject_a_caller_supplied_event_id_for_another_event(self):
        """Passing this event's template_id but querying under another event's
        admin session must not leak - authorisation reads the template's own
        event_id, never anything the caller could pass in."""
        list_resp = self.app.get(f'/api/v1/documents/templates?event_id={self.event_id}',
                                  headers=self.other_admin_headers)
        # The list endpoint IS scoped by event_id via event_admin_required, so
        # an admin of a different event is refused outright rather than being
        # shown this event's templates.
        self.assertEqual(list_resp.status_code, 403)


class TestUserEventDataAuthorization(DocumentAuthorizationTestCase):

    def test_other_events_admin_cannot_read_user_data(self):
        resp = self.app.get(f'/api/v1/events/{self.event_id}/user-data', headers=self.other_admin_headers)
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_write_user_data(self):
        resp = self.app.put(
            f'/api/v1/events/{self.event_id}/user-data',
            data=json.dumps({'entries': [{'user_id': self.user_id, 'key': 'hostel', 'value': 'x'}]}),
            content_type='application/json', headers=self.other_admin_headers,
        )
        self.assertEqual(resp.status_code, 403)

    def test_plain_user_cannot_read_user_data(self):
        resp = self.app.get(f'/api/v1/events/{self.event_id}/user-data', headers=self.plain_headers)
        self.assertEqual(resp.status_code, 403)


class TestGeneratedDocumentDownloadAuthorization(DocumentAuthorizationTestCase):

    def _generate_for(self, target_user_id):
        from unittest.mock import patch
        with patch('app.documents.generator.build_default_client') as mock_client:
            from app.documents.tests.test_api import FakeGoogleClient
            mock_client.return_value = FakeGoogleClient()
            self.make_variant(self.document_template, {'firstname'})
            resp = self.app.post(
                '/api/v1/documents/generate',
                data=json.dumps({'template_id': self.document_template_id, 'user_id': target_user_id}),
                content_type='application/json', headers=self.owner_headers,
            )
        self.assertEqual(resp.status_code, 201)
        return json.loads(resp.data)['id']

    def test_owner_can_download_their_own_document(self):
        document_id = self._generate_for(self.user_id)
        resp = self.app.get(f'/api/v1/documents/generated/{document_id}/download', headers=self.owner_headers)
        self.assertEqual(resp.status_code, 200)

    def test_event_admin_can_download_someone_elses_document(self):
        # Generated for plain_user (not an admin of anything); the event
        # admin (self.user / owner_headers) downloads it on their behalf.
        document_id = self._generate_for(self.plain_user_id)
        resp = self.app.get(f'/api/v1/documents/generated/{document_id}/download', headers=self.owner_headers)
        self.assertEqual(resp.status_code, 200)

    def test_unrelated_user_cannot_download_someone_elses_document(self):
        document_id = self._generate_for(self.user_id)
        resp = self.app.get(f'/api/v1/documents/generated/{document_id}/download', headers=self.plain_headers)
        self.assertEqual(resp.status_code, 403)

    def test_other_events_admin_cannot_download_this_events_document(self):
        document_id = self._generate_for(self.user_id)
        resp = self.app.get(f'/api/v1/documents/generated/{document_id}/download',
                             headers=self.other_admin_headers)
        self.assertEqual(resp.status_code, 403)

    def test_download_of_nonexistent_document_404s(self):
        resp = self.app.get('/api/v1/documents/generated/999999/download', headers=self.owner_headers)
        self.assertEqual(resp.status_code, 404)
