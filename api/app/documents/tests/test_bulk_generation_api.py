import json
from unittest.mock import patch

from app import db
from app.documents.tests.test_api import DocumentApiTestCase
from app.documents.models import (
    GeneratedDocument, GeneratedDocumentStatus, DocumentGenerationJob, DocumentGenerationJobStatus,
)


class FakeGoogleClient:
    def __init__(self, placeholders=None, pdf_bytes=b'%PDF-1.4 fake'):
        self.placeholders = placeholders or {'firstname'}
        self.pdf_bytes = pdf_bytes

    def generate_pdf(self, google_file_id, google_file_type, replacements):
        return self.pdf_bytes


class TestPreflight(DocumentApiTestCase):

    def setUp(self):
        super().setUp()
        self.document_template = self.make_document_template()
        self.make_variant(self.document_template, placeholders={'firstname'})

    def test_everyone_selection_reports_will_succeed(self):
        second_user = self.add_user('second@example.com', 'Second', 'User')
        self.add_offer(self.event, self.user)
        self.add_offer(self.event, second_user)

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/preflight',
            {'recipients': {'type': 'everyone'}},
        )

        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertEqual(body['total_candidates'], 2)
        self.assertEqual(body['will_succeed_count'], 2)
        self.assertEqual(body['will_fail_count'], 0)

    def test_ineligible_recipients_are_excluded_not_counted_as_failures(self):
        self.add_offer(self.event, self.user)
        document_template = self.make_document_template(
            key='visa-letter-ineligible', eligibility_expression={'tag_id': 999999})
        self.make_variant(document_template, placeholders={'firstname'})

        resp = self.post_json(
            f'/api/v1/documents/templates/{document_template.id}/generate/preflight',
            {'recipients': {'type': 'everyone'}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['excluded_ineligible_count'], 1)
        self.assertEqual(body['will_fail_count'], 0)
        self.assertEqual(body['will_succeed_count'], 0)

    def test_required_form_not_submitted_is_a_failure(self):
        self.add_offer(self.event, self.user)
        form = self.make_form(name='Registration Form')
        from app.documents.models import DocumentTemplateForm
        self.link_form(self.document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_REQUIRED)

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/preflight',
            {'recipients': {'type': 'everyone'}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['will_fail_count'], 1)
        self.assertEqual(body['failures'][0]['reason'], 'required_form_not_submitted')

    def test_recommended_incomplete_is_informational_not_a_failure(self):
        self.add_offer(self.event, self.user)
        form = self.make_form(name='Post-Event Survey')
        from app.documents.models import DocumentTemplateForm
        self.link_form(self.document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED)

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/preflight',
            {'recipients': {'type': 'everyone'}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['will_fail_count'], 0)
        self.assertEqual(body['will_succeed_count'], 1)
        self.assertEqual(body['recommended_incomplete_count'], 1)

    def test_unresolvable_placeholder_is_a_failure(self):
        self.add_offer(self.event, self.user)
        document_template = self.make_document_template(key='visa-letter')
        self.make_variant(document_template, placeholders={'made_up_key'})

        resp = self.post_json(
            f'/api/v1/documents/templates/{document_template.id}/generate/preflight',
            {'recipients': {'type': 'everyone'}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['will_fail_count'], 1)
        self.assertEqual(body['failures'][0]['reason'], 'placeholder_resolution_failed')

    def test_tag_selection_scopes_the_population(self):
        second_user = self.add_user('second@example.com', 'Second', 'User')
        tag = self.make_tag(self.event, name='Travel')
        self.give_offer_tag(self.event, self.user, tag)
        self.add_offer(self.event, second_user)  # no tag

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/preflight',
            {'recipients': {'type': 'tag', 'tag_id': tag.id}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['total_candidates'], 1)

    def test_emails_selection(self):
        second_user = self.add_user('second@example.com', 'Second', 'User')

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/preflight',
            {'recipients': {'type': 'emails', 'emails': [second_user.email]}},
        )

        body = json.loads(resp.data)
        self.assertEqual(body['total_candidates'], 1)
        self.assertEqual(body['will_succeed_user_ids'], [second_user.id])


@patch('app.documents.api.build_default_client')
class TestBulkGenerate(DocumentApiTestCase):

    def setUp(self):
        super().setUp()
        self.document_template = self.make_document_template()
        self.make_variant(self.document_template, placeholders={'firstname'})

    def test_creates_job_and_pending_rows_for_recipients_only(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        second_user = self.add_user('second@example.com', 'Second', 'User')
        self.add_offer(self.event, self.user)
        self.add_offer(self.event, second_user)

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/bulk',
            {'recipients': {'type': 'everyone'}},
        )

        self.assertEqual(resp.status_code, 201)
        body = json.loads(resp.data)
        self.assertEqual(body['total_count'], 2)
        self.assertEqual(body['status'], DocumentGenerationJobStatus.PENDING)

        rows = db.session.query(GeneratedDocument).filter_by(job_id=body['id']).all()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r.status == GeneratedDocumentStatus.PENDING for r in rows))

    def test_no_recipients_is_rejected(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()

        resp = self.post_json(
            f'/api/v1/documents/templates/{self.document_template.id}/generate/bulk',
            {'recipients': {'type': 'everyone'}},
        )

        self.assertEqual(resp.status_code, 400)

    def test_ineligible_recipients_are_excluded_from_the_job(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        self.add_offer(self.event, self.user)
        document_template = self.make_document_template(
            key='visa-letter-ineligible', eligibility_expression={'tag_id': 999999})
        self.make_variant(document_template, placeholders={'firstname'})

        resp = self.post_json(
            f'/api/v1/documents/templates/{document_template.id}/generate/bulk',
            {'recipients': {'type': 'everyone'}},
        )

        self.assertEqual(resp.status_code, 400)  # nobody eligible => no recipients


class TestGenerationJobStatus(DocumentApiTestCase):

    def test_get_job_status(self):
        document_template = self.make_document_template()
        job = self.make_generation_job(document_template, total_count=5)
        job_id = job.id

        resp = self.app.get(f'/api/v1/documents/jobs/{job_id}', headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['total_count'], 5)

    def test_nonexistent_job_404(self):
        resp = self.app.get('/api/v1/documents/jobs/99999', headers=self.headers)
        self.assertEqual(resp.status_code, 404)

    def test_non_admin_forbidden(self):
        document_template = self.make_document_template()
        job = self.make_generation_job(document_template, total_count=1)
        other_user = self.add_user('outsider@example.com', 'Out', 'Sider')

        resp = self.app.get(
            f'/api/v1/documents/jobs/{job.id}',
            headers=self.get_auth_header_for(other_user.email))

        self.assertEqual(resp.status_code, 403)


class TestGenerationWorkerAuthorization(DocumentApiTestCase):

    def test_rejects_requests_without_cron_header(self):
        resp = self.app.get('/api/v1/tasks/document-generation')
        self.assertEqual(resp.status_code, 403)

    def test_answers_get_with_cron_header(self):
        resp = self.app.get('/api/v1/tasks/document-generation',
                             headers={'X-Appengine-Cron': 'true'})
        self.assertEqual(resp.status_code, 200)


class TestResendAndRegenerate(DocumentApiTestCase):

    def setUp(self):
        super().setUp()
        self.document_template = self.make_document_template(delivery_mode='attachment')
        self.variant = self.make_variant(self.document_template, placeholders={'firstname'})

    def _generated_document(self, status=GeneratedDocumentStatus.GENERATED, storage_blob_name='blob.pdf'):
        doc = GeneratedDocument(
            event_id=self.event_id, document_template_id=self.document_template.id,
            user_id=self.user_id, requested_by_user_id=self.user_id, status=status,
        )
        db.session.add(doc)
        db.session.flush()
        doc.storage_blob_name = storage_blob_name
        doc.filename = 'letter.pdf'
        db.session.commit()
        return doc

    def test_resend_requires_generated_status(self):
        doc = self._generated_document(status=GeneratedDocumentStatus.PENDING)

        resp = self.app.post(f'/api/v1/documents/generated/{doc.id}/resend', headers=self.headers)

        self.assertEqual(resp.status_code, 409)

    def test_resend_with_no_email_template_reports_it(self):
        doc = self._generated_document()

        resp = self.app.post(f'/api/v1/documents/generated/{doc.id}/resend', headers=self.headers)

        self.assertEqual(resp.status_code, 400)

    def test_resend_queues_a_new_outbox_message(self):
        self.add_email_template('generated-document', template='Hi {firstname}', subject='Ready')
        doc = self._generated_document()
        doc_id = doc.id

        resp = self.app.post(f'/api/v1/documents/generated/{doc_id}/resend', headers=self.headers)

        self.assertEqual(resp.status_code, 200)
        from app.outbox.models import OutboxMessage
        count = db.session.query(OutboxMessage).filter_by(
            source_type='document', source_id=doc_id).count()
        self.assertEqual(count, 1)

    def test_resend_none_delivery_mode_rejected(self):
        self.document_template.delivery_mode = 'none'
        db.session.commit()
        doc = self._generated_document()

        resp = self.app.post(f'/api/v1/documents/generated/{doc.id}/resend', headers=self.headers)

        self.assertEqual(resp.status_code, 400)

    @patch('app.documents.generator.build_default_client')
    def test_regenerate_creates_a_new_row(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        original = self._generated_document()
        original_id = original.id
        document_template_id = self.document_template.id

        resp = self.app.post(f'/api/v1/documents/generated/{original_id}/regenerate', headers=self.headers)

        self.assertEqual(resp.status_code, 201)
        new_id = json.loads(resp.data)['id']
        self.assertNotEqual(new_id, original_id)
        self.assertEqual(
            db.session.query(GeneratedDocument).filter_by(document_template_id=document_template_id).count(),
            2,
        )
