import json
from unittest.mock import patch

from app import db
from app.documents.tests.base import DocumentsTestCase
from app.documents.google_client import AccessCheckResult, AccessStatus
from app.documents.models import DocumentTemplate, DocumentTemplateVariant, UserEventData


class FakeGoogleClient:
    def __init__(self, placeholders=None, pdf_bytes=b'%PDF-1.4 fake'):
        self.placeholders = placeholders or {'firstname'}
        self.pdf_bytes = pdf_bytes

    def check_access(self, file_id):
        return AccessCheckResult(AccessStatus.OK, file_id=file_id, file_name='Test Doc', file_type='document')

    def scan_placeholders(self, file_id, file_type):
        return self.placeholders

    def generate_pdf(self, google_file_id, google_file_type, replacements):
        return self.pdf_bytes


class DocumentApiTestCase(DocumentsTestCase):
    def setUp(self):
        super().setUp()
        self.add_event_role('admin', self.user_id, self.event_id)
        self.headers = self.get_auth_header_for(self.user.email)

    def post_json(self, url, body, headers=None):
        return self.app.post(url, data=json.dumps(body), content_type='application/json',
                              headers=headers or self.headers)

    def put_json(self, url, body, headers=None):
        return self.app.put(url, data=json.dumps(body), content_type='application/json',
                             headers=headers or self.headers)


class TestDocumentTemplateCrud(DocumentApiTestCase):

    def test_create_list_get_update_delete(self):
        create_resp = self.post_json(
            f'/api/v1/documents/templates?event_id={self.event_id}',
            {'key': 'invitation-letter', 'name': 'Invitation Letter', 'self_service': True},
        )
        self.assertEqual(create_resp.status_code, 201)
        template_id = json.loads(create_resp.data)['id']

        list_resp = self.app.get(f'/api/v1/documents/templates?event_id={self.event_id}', headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(json.loads(list_resp.data)), 1)

        get_resp = self.app.get(f'/api/v1/documents/templates/{template_id}', headers=self.headers)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(json.loads(get_resp.data)['key'], 'invitation-letter')

        update_resp = self.put_json(
            f'/api/v1/documents/templates/{template_id}',
            {'delivery_mode': 'link', 'translations': {'en': {'name': 'Renamed Letter'}}},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(json.loads(update_resp.data)['delivery_mode'], 'link')
        self.assertEqual(json.loads(update_resp.data)['name'], 'Renamed Letter')

        delete_resp = self.app.delete(f'/api/v1/documents/templates/{template_id}', headers=self.headers)
        self.assertEqual(delete_resp.status_code, 204)
        self.assertIsNone(db.session.query(DocumentTemplate).filter_by(id=template_id).first())

    def test_duplicate_key_rejected(self):
        self.post_json(f'/api/v1/documents/templates?event_id={self.event_id}', {'key': 'dup'})
        resp = self.post_json(f'/api/v1/documents/templates?event_id={self.event_id}', {'key': 'dup'})
        self.assertEqual(resp.status_code, 409)

    def test_missing_key_rejected(self):
        resp = self.post_json(f'/api/v1/documents/templates?event_id={self.event_id}', {})
        self.assertEqual(resp.status_code, 400)

    def test_get_nonexistent_template_404(self):
        resp = self.app.get('/api/v1/documents/templates/99999', headers=self.headers)
        self.assertEqual(resp.status_code, 404)


class TestDocumentTemplateVariants(DocumentApiTestCase):

    def setUp(self):
        super().setUp()
        self.document_template = self.make_document_template()

    @patch('app.documents.api.build_default_client')
    def test_add_variant_scans_and_stores_placeholders(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient(placeholders={'firstname', 'lastname'})

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/variants',
            {'google_file_url': 'https://docs.google.com/document/d/abc123/edit', 'name': 'Default'},
        )

        self.assertEqual(resp.status_code, 201)
        body = json.loads(resp.data)
        self.assertEqual(sorted(body['detected_placeholders']), ['firstname', 'lastname'])
        self.assertEqual(body['access_status'], 'ok')

    def test_add_variant_without_recognisable_link_is_rejected(self):
        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/variants',
            {'google_file_url': 'not a link'},
        )
        self.assertEqual(resp.status_code, 400)

    @patch('app.documents.api.build_default_client')
    def test_add_variant_with_inaccessible_file_returns_access_detail(self, mock_build_client):
        class DeniedClient(FakeGoogleClient):
            def check_access(self, file_id):
                return AccessCheckResult(AccessStatus.NO_PERMISSION)
        mock_build_client.return_value = DeniedClient()

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/variants',
            {'google_file_url': 'https://docs.google.com/document/d/abc123/edit'},
        )

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(json.loads(resp.data)['access']['status'], 'no_permission')

    def test_update_and_delete_variant(self):
        variant = self.make_variant(self.document_template, {'firstname'})
        # Captured before the first request below: a request through the test
        # client tears down db.session on completion, and re-reading an
        # attribute off an object loaded through the old session raises
        # DetachedInstanceError - see app.documents.tests.base._pk.
        document_template_id = self.document_template.id
        variant_id = variant.id

        update_resp = self.put_json(
            f'/api/v1/documents/templates/{document_template_id}/variants/{variant_id}',
            {'priority': 5, 'is_active': False},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(json.loads(update_resp.data)['priority'], 5)

        delete_resp = self.app.delete(
            f'/api/v1/documents/templates/{document_template_id}/variants/{variant_id}',
            headers=self.headers,
        )
        self.assertEqual(delete_resp.status_code, 204)
        self.assertIsNone(db.session.query(DocumentTemplateVariant).filter_by(id=variant_id).first())


class TestDocumentTemplateForms(DocumentApiTestCase):

    def test_replace_form_links_sets_order_and_requirement(self):
        document_template = self.make_document_template()
        registration = self.make_form(name='Registration Form')
        application = self.make_form(name='Application Form')
        document_template_id, registration_id, application_id = (
            document_template.id, registration.id, application.id)

        resp = self.put_json(
            f'/api/v1/documents/templates/{document_template_id}/forms',
            {'form_links': [
                {'form_id': registration_id, 'order': 20, 'requirement': 'required',
                 'prompt_messages': {'en': 'Please register first.'}},
                {'form_id': application_id, 'order': 10, 'requirement': 'none'},
            ]},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(len(body['form_links']), 2)
        self.assertEqual(body['form_links'][0]['form_id'], registration_id)
        self.assertEqual(body['form_links'][0]['requirement'], 'required')
        self.assertEqual(body['form_links'][0]['prompt_message'], 'Please register first.')

    def test_linking_form_from_another_event_is_rejected(self):
        document_template = self.make_document_template()
        other_event = self.add_event(key='OTHEREVT')
        other_form = self.make_form(event_id=other_event.id)

        resp = self.put_json(
            f'/api/v1/documents/templates/{document_template.id}/forms',
            {'form_links': [{'form_id': other_form.id, 'order': 10}]},
        )

        self.assertEqual(resp.status_code, 404)


class TestDocumentValidateSource(DocumentApiTestCase):

    @patch('app.documents.api.build_default_client')
    def test_validate_source_returns_access_and_placeholders(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient(placeholders={'firstname'})

        resp = self.post_json(
            f'/api/v1/documents/validate-source?event_id={self.event_id}',
            {'url': 'https://docs.google.com/document/d/abc123/edit'},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['status'], 'ok')
        self.assertIn('service_account_email', body)
        self.assertEqual(body['detected_placeholders'], ['firstname'])


class TestDocumentTemplatePreview(DocumentApiTestCase):

    def test_preview_dry_run_resolves_without_generating(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'firstname'})

        resp = self.post_json(
            f'/api/v1/documents/templates/{document_template.id}/preview',
            {'user_id': self.user_id},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertTrue(body['eligible'])
        self.assertEqual(body['resolution']['values']['firstname']['value'], self.user_firstname)

        from app.documents.models import GeneratedDocument
        self.assertEqual(db.session.query(GeneratedDocument).count(), 0)


class TestDocumentGenerateAndDownload(DocumentApiTestCase):

    @patch('app.documents.generator.build_default_client')
    def test_admin_generate_then_download(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        document_template = self.make_document_template(delivery_mode='none')
        self.make_variant(document_template, {'firstname'})

        generate_resp = self.post_json('/api/v1/documents/generate', {
            'template_id': document_template.id, 'user_id': self.user_id,
        })
        self.assertEqual(generate_resp.status_code, 201)
        doc_id = json.loads(generate_resp.data)['id']

        download_resp = self.app.get(f'/api/v1/documents/generated/{doc_id}/download', headers=self.headers)
        self.assertEqual(download_resp.status_code, 200)

    @patch('app.documents.generator.build_default_client')
    def test_generate_for_ineligible_person_returns_422(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        document_template = self.make_document_template(eligibility_expression={'tag_id': 999})
        self.make_variant(document_template, {'firstname'})

        resp = self.post_json('/api/v1/documents/generate', {
            'template_id': document_template.id, 'user_id': self.user_id,
        })

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(json.loads(resp.data)['code'], 'NOT_ELIGIBLE')


class TestDocumentAvailableAndRequest(DocumentApiTestCase):

    def test_available_lists_self_service_templates_with_prompts(self):
        document_template = self.make_document_template(self_service=True)
        form = self.make_form(name='Post-Event Survey')
        from app.documents.models import DocumentTemplateForm
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED,
                        prompt_message='Please complete the survey.')

        # self.headers already authenticates as self.user (see setUp) - no
        # need to re-authenticate.
        resp = self.app.get(f'/api/v1/documents/available?event_id={self.event_id}', headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(len(body), 1)
        self.assertEqual(len(body[0]['prompts']), 1)
        self.assertEqual(body[0]['blockers'], [])

    def test_non_self_service_template_is_not_listed(self):
        self.make_document_template(self_service=False)

        resp = self.app.get(f'/api/v1/documents/available?event_id={self.event_id}', headers=self.headers)

        self.assertEqual(json.loads(resp.data), [])

    @patch('app.documents.generator.build_default_client')
    def test_self_service_request_generates_document(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        document_template = self.make_document_template(self_service=True, delivery_mode='none')
        self.make_variant(document_template, {'firstname'})

        resp = self.post_json('/api/v1/documents/request', {'template_id': document_template.id})

        self.assertEqual(resp.status_code, 201)

    def test_request_for_non_self_service_template_404s(self):
        document_template = self.make_document_template(self_service=False)

        resp = self.post_json('/api/v1/documents/request', {'template_id': document_template.id})

        self.assertEqual(resp.status_code, 404)


class TestUserEventData(DocumentApiTestCase):

    def test_put_then_get_round_trips(self):
        put_resp = self.put_json(f'/api/v1/events/{self.event_id}/user-data', {
            'entries': [{'user_id': self.user_id, 'key': 'hostel', 'value': 'Bantry Bay Lodge'}],
        })
        self.assertEqual(put_resp.status_code, 200)

        get_resp = self.app.get(f'/api/v1/events/{self.event_id}/user-data', headers=self.headers)
        body = json.loads(get_resp.data)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]['value'], 'Bantry Bay Lodge')

    def test_updating_existing_key_overwrites_value(self):
        self.set_user_data(self.event, self.user, 'hostel', 'Old Value')

        self.put_json(f'/api/v1/events/{self.event_id}/user-data', {
            'entries': [{'user_id': self.user_id, 'key': 'hostel', 'value': 'New Value'}],
        })

        rows = db.session.query(UserEventData).filter_by(event_id=self.event_id, user_id=self.user_id).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].value, 'New Value')
