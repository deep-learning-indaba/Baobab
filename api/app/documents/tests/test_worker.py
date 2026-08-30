"""run_bulk_generation - the claim-batch worker behind
/api/v1/tasks/document-generation (design section 8.2), against a fake
GoogleWorkspaceClient so no test touches the network."""
from datetime import datetime, timedelta
from unittest.mock import patch

from app import db
from app.documents.tests.base import DocumentsTestCase
from app.documents.models import (
    GeneratedDocument, GeneratedDocumentStatus, DocumentGenerationJobStatus,
)
from app.documents.worker import run_bulk_generation, claim_batch, requeue_stale
from app.outbox.models import OutboxMessage


class FakeGoogleClient:
    def __init__(self, pdf_bytes=b'%PDF-1.4 fake', raise_error=None):
        self.pdf_bytes = pdf_bytes
        self.raise_error = raise_error
        self.calls = []

    def generate_pdf(self, google_file_id, google_file_type, replacements):
        self.calls.append(google_file_id)
        if self.raise_error:
            raise self.raise_error
        return self.pdf_bytes


class WorkerTestCase(DocumentsTestCase):

    def setUp(self):
        super().setUp()
        self.document_template = self.make_document_template(key='certificate')
        self.make_variant(self.document_template, placeholders={'firstname'})

    def _pending_row(self, job, user=None):
        user = user or self.user
        row = GeneratedDocument(
            event_id=self.event_id, document_template_id=self.document_template.id,
            user_id=user.id, requested_by_user_id=self.admin_id,
            status=GeneratedDocumentStatus.PENDING, job_id=job.id,
        )
        db.session.add(row)
        db.session.commit()
        return row


@patch('app.documents.worker.build_default_client')
class TestRunBulkGeneration(WorkerTestCase):

    def test_claims_and_generates_pending_rows(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)

        summary = run_bulk_generation()

        self.assertEqual(summary['claimed'], 1)
        self.assertEqual(summary['generated'], 1)
        db.session.refresh(row)
        self.assertEqual(row.status, GeneratedDocumentStatus.GENERATED)
        self.assertIsNotNone(row.storage_blob_name)

    def test_job_counters_update_on_success(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        second_user = self.add_user('second@example.com', 'Second', 'User')
        job = self.make_generation_job(self.document_template, total_count=2)
        self._pending_row(job)
        self._pending_row(job, user=second_user)

        run_bulk_generation()

        db.session.refresh(job)
        self.assertEqual(job.succeeded_count, 2)
        self.assertEqual(job.failed_count, 0)
        self.assertEqual(job.status, DocumentGenerationJobStatus.COMPLETED)
        self.assertIsNotNone(job.completed_at)

    def test_resolution_failure_marks_row_failed_not_retried(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        template = self.make_document_template(key='needs-passport')
        self.make_variant(template, placeholders={'passport_no'})
        job = self.make_generation_job(template, total_count=1)
        row = GeneratedDocument(
            event_id=self.event_id, document_template_id=template.id,
            user_id=self.user_id, requested_by_user_id=self.admin_id,
            status=GeneratedDocumentStatus.PENDING, job_id=job.id,
        )
        db.session.add(row)
        db.session.commit()

        summary = run_bulk_generation()

        self.assertEqual(summary['failed'], 1)
        db.session.refresh(row)
        # Straight to `failed` on the very first attempt (attempts=1, well
        # under MAX_ATTEMPTS) - a resolution failure is never retried
        # regardless of attempts remaining, unlike a transport failure.
        self.assertEqual(row.status, GeneratedDocumentStatus.FAILED)
        self.assertEqual(row.error_code, 'PLACEHOLDER_RESOLUTION_FAILED')

        db.session.refresh(job)
        self.assertEqual(job.failed_count, 1)
        self.assertEqual(job.status, DocumentGenerationJobStatus.COMPLETED_WITH_ERRORS)

    def test_google_api_error_is_retried_then_eventually_fails(self, mock_build_client):
        from app.documents.google_client import GoogleApiError
        mock_build_client.return_value = FakeGoogleClient(raise_error=GoogleApiError(500, 'boom'))
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)

        for _ in range(GeneratedDocument.MAX_ATTEMPTS):
            summary = run_bulk_generation()
            db.session.refresh(row)
            if row.status == GeneratedDocumentStatus.FAILED:
                break
            self.assertEqual(row.status, GeneratedDocumentStatus.PENDING)
            self.assertEqual(summary['failed'], 1)

        self.assertEqual(row.status, GeneratedDocumentStatus.FAILED)
        self.assertEqual(row.attempts, GeneratedDocument.MAX_ATTEMPTS)

        db.session.refresh(job)
        self.assertEqual(job.failed_count, 1)

    def test_override_eligibility_is_read_from_the_job(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        template = self.make_document_template(
            key='invitation-letter', eligibility_expression={'tag_id': 999})
        self.make_variant(template, placeholders={'firstname'})
        job = self.make_generation_job(template, total_count=1, override_eligibility=True)
        row = GeneratedDocument(
            event_id=self.event_id, document_template_id=template.id,
            user_id=self.user_id, requested_by_user_id=self.admin_id,
            status=GeneratedDocumentStatus.PENDING, job_id=job.id,
        )
        db.session.add(row)
        db.session.commit()

        run_bulk_generation()

        db.session.refresh(row)
        self.assertEqual(row.status, GeneratedDocumentStatus.GENERATED)

    def test_delivery_email_is_queued_for_each_generated_document(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        self.add_email_template('generated-document', template='Hi {firstname}', subject='Ready')
        self.document_template.delivery_mode = 'attachment'
        db.session.commit()
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)

        run_bulk_generation()

        message = db.session.query(OutboxMessage).filter_by(
            source_type='document', source_id=row.id).first()
        self.assertIsNotNone(message)

    def test_time_budget_releases_remaining_rows(self, mock_build_client):
        mock_build_client.return_value = FakeGoogleClient()
        job = self.make_generation_job(self.document_template, total_count=3)
        rows = [self._pending_row(job) for _ in range(3)]

        summary = run_bulk_generation(time_budget_seconds=-1)

        self.assertEqual(summary['claimed'], 3)
        self.assertEqual(summary['released'], 3)
        for row in rows:
            db.session.refresh(row)
            self.assertEqual(row.status, GeneratedDocumentStatus.PENDING)
            self.assertIsNone(row.claim_token)

    def test_a_synchronous_single_generation_row_is_never_claimed(self, mock_build_client):
        """A row with no job_id (generator.generate_document's synchronous
        path) must never be picked up by the bulk worker."""
        mock_build_client.return_value = FakeGoogleClient()
        row = GeneratedDocument(
            event_id=self.event_id, document_template_id=self.document_template.id,
            user_id=self.user_id, requested_by_user_id=self.admin_id,
            status=GeneratedDocumentStatus.PENDING, job_id=None,
        )
        db.session.add(row)
        db.session.commit()

        summary = run_bulk_generation()

        self.assertEqual(summary['claimed'], 0)
        db.session.refresh(row)
        self.assertEqual(row.status, GeneratedDocumentStatus.PENDING)


class TestClaimBatch(WorkerTestCase):

    def test_claim_takes_exclusive_ownership(self):
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)

        claimed = claim_batch(10)

        self.assertEqual([r.id for r in claimed], [row.id])
        db.session.refresh(row)
        self.assertEqual(row.status, GeneratedDocumentStatus.GENERATING)
        self.assertIsNotNone(row.claim_token)

    def test_claim_respects_limit(self):
        job = self.make_generation_job(self.document_template, total_count=3)
        for _ in range(3):
            self._pending_row(job)

        claimed = claim_batch(2)

        self.assertEqual(len(claimed), 2)


class TestRequeueStale(WorkerTestCase):

    def test_abandoned_claim_is_recovered_as_failed_or_pending(self):
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)
        row.status = GeneratedDocumentStatus.GENERATING
        row.claimed_at = datetime.utcnow() - timedelta(seconds=700)
        row.claim_token = 'stale-token'
        db.session.commit()

        recovered = requeue_stale()

        self.assertEqual(recovered, 1)
        db.session.refresh(row)
        self.assertIn(row.status, (GeneratedDocumentStatus.PENDING, GeneratedDocumentStatus.FAILED))
        self.assertEqual(row.attempts, 1)

    def test_recently_claimed_row_is_left_alone(self):
        job = self.make_generation_job(self.document_template, total_count=1)
        row = self._pending_row(job)
        row.status = GeneratedDocumentStatus.GENERATING
        row.claimed_at = datetime.utcnow()
        row.claim_token = 'fresh-token'
        db.session.commit()

        recovered = requeue_stale()

        self.assertEqual(recovered, 0)
        db.session.refresh(row)
        self.assertEqual(row.status, GeneratedDocumentStatus.GENERATING)
