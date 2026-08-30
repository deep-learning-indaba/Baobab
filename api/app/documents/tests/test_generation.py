"""generate_document - the synchronous single-document pipeline (design
section 8.1), against a fake GoogleWorkspaceClient so no test touches the
network. Covers each GenerationError short-circuit and the happy path through
to a stored GeneratedDocument + GCS blob."""
from app import db
from app.documents.tests.base import DocumentsTestCase
from app.documents.generator import generate_document, GenerationError
from app.documents.models import GeneratedDocument, GeneratedDocumentStatus
from app.documents.google_client import GoogleApiError
from app.utils import storage


class FakeGoogleClient:
    def __init__(self, pdf_bytes=b'%PDF-1.4 fake', raise_error=None):
        self.pdf_bytes = pdf_bytes
        self.raise_error = raise_error
        self.calls = []

    def generate_pdf(self, google_file_id, google_file_type, replacements):
        self.calls.append((google_file_id, google_file_type, dict(replacements)))
        if self.raise_error:
            raise self.raise_error
        return self.pdf_bytes


class TestGenerateDocumentHappyPath(DocumentsTestCase):

    def setUp(self):
        super().setUp()
        storage.get_storage_bucket()  # ensure the local storage emulator bucket exists

    def test_generates_uploads_and_records_generated_document(self):
        document_template = self.make_document_template(key='invitation-letter', delivery_mode='none')
        variant = self.make_variant(document_template, placeholders={'firstname'})
        client = FakeGoogleClient()

        result = generate_document(document_template, self.user, self.user, self.event, client=client)

        self.assertEqual(result.status, GeneratedDocumentStatus.GENERATED)
        self.assertEqual(result.variant_id, variant.id)
        self.assertIsNotNone(result.storage_blob_name)
        self.assertEqual(result.placeholder_snapshot['firstname']['value'], self.user.firstname)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][0], variant.google_file_id)

    def test_filename_pattern_is_rendered(self):
        document_template = self.make_document_template(
            key='cert', delivery_mode='none', filename_pattern='{lastname}_{firstname}.pdf')
        self.make_variant(document_template, placeholders={'firstname'})
        client = FakeGoogleClient()

        result = generate_document(document_template, self.user, self.user, self.event, client=client)

        self.assertEqual(result.filename, f'{self.user.lastname}_{self.user.firstname}.pdf')

    def test_generated_document_persisted_to_db(self):
        document_template = self.make_document_template(key='cert', delivery_mode='none')
        self.make_variant(document_template, placeholders={'firstname'})
        client = FakeGoogleClient()

        result = generate_document(document_template, self.user, self.user, self.event, client=client)

        fetched = db.session.query(GeneratedDocument).filter_by(id=result.id).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, GeneratedDocumentStatus.GENERATED)


class TestGenerateDocumentEligibility(DocumentsTestCase):

    def test_ineligible_user_is_refused(self):
        document_template = self.make_document_template(
            key='invitation-letter', eligibility_expression={'tag_id': 999})
        self.make_variant(document_template, placeholders={'firstname'})

        with self.assertRaises(GenerationError) as ctx:
            generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        self.assertEqual(ctx.exception.code, 'NOT_ELIGIBLE')

    def test_override_eligibility_bypasses_the_check(self):
        document_template = self.make_document_template(
            key='invitation-letter', eligibility_expression={'tag_id': 999}, delivery_mode='none')
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(
            document_template, self.user, self.user, self.event,
            client=FakeGoogleClient(), override_eligibility=True,
        )

        self.assertEqual(result.status, GeneratedDocumentStatus.GENERATED)


class TestGenerateDocumentRequiredForm(DocumentsTestCase):

    def test_required_form_not_submitted_is_refused(self):
        form = self.make_form(name='Registration Form')
        document_template = self.make_document_template(key='invitation-letter')
        self.make_variant(document_template, placeholders={'firstname'})
        from app.documents.models import DocumentTemplateForm
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_REQUIRED)

        with self.assertRaises(GenerationError) as ctx:
            generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        self.assertEqual(ctx.exception.code, 'REQUIRED_FORM_NOT_SUBMITTED')
        self.assertEqual(ctx.exception.details['blockers'][0]['form_name'], 'Registration Form')


class TestGenerateDocumentVariant(DocumentsTestCase):

    def test_no_matching_variant_is_refused(self):
        document_template = self.make_document_template(key='invitation-letter')
        self.make_variant(document_template, placeholders={'firstname'},
                           selection_expression={'tag_id': 999})

        with self.assertRaises(GenerationError) as ctx:
            generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        self.assertEqual(ctx.exception.code, 'NO_MATCHING_VARIANT')


class TestGenerateDocumentPlaceholderFailure(DocumentsTestCase):

    def test_unresolvable_placeholder_is_refused_before_calling_google(self):
        document_template = self.make_document_template(key='invitation-letter')
        self.make_variant(document_template, placeholders={'made_up_key'})
        client = FakeGoogleClient()

        with self.assertRaises(GenerationError) as ctx:
            generate_document(document_template, self.user, self.user, self.event, client=client)

        self.assertEqual(ctx.exception.code, 'PLACEHOLDER_RESOLUTION_FAILED')
        self.assertEqual(client.calls, [])  # never reached the Google API


class TestGenerateDocumentGoogleFailure(DocumentsTestCase):

    def test_google_api_error_marks_document_failed(self):
        document_template = self.make_document_template(key='invitation-letter')
        self.make_variant(document_template, placeholders={'firstname'})
        client = FakeGoogleClient(raise_error=GoogleApiError(500, 'boom'))

        with self.assertRaises(GenerationError) as ctx:
            generate_document(document_template, self.user, self.user, self.event, client=client)

        self.assertEqual(ctx.exception.code, 'GOOGLE_API_ERROR')

        failed = db.session.query(GeneratedDocument).filter_by(
            document_template_id=document_template.id, user_id=self.user.id).first()
        self.assertEqual(failed.status, GeneratedDocumentStatus.FAILED)
        self.assertEqual(failed.error_code, 'GOOGLE_API_ERROR')


class TestGenerateDocumentEmailDelivery(DocumentsTestCase):
    """Delivery is queued through the outbox (design section 8.3), never sent
    inline - see generator._enqueue_delivery_email."""

    def _outbox_message(self, generated_document):
        from app.outbox.models import OutboxMessage
        return db.session.query(OutboxMessage).filter_by(
            source_type='document', source_id=generated_document.id).first()

    def test_attachment_mode_queues_an_email_with_the_pdf_attached(self):
        self.add_email_template('generated-document', template='Hi {firstname}', subject='Your document')
        document_template = self.make_document_template(key='invitation-letter', delivery_mode='attachment')
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        message = self._outbox_message(result)
        self.assertIsNotNone(message)
        self.assertEqual(message.recipient, self.user.email)
        self.assertEqual(message.payload['attachment']['blob_name'], result.storage_blob_name)
        self.assertEqual(message.payload['attachment']['filename'], result.filename)

    def test_link_mode_queues_an_email_without_an_attachment(self):
        self.add_email_template('generated-document', template='Hi {firstname}', subject='Your document')
        document_template = self.make_document_template(key='invitation-letter', delivery_mode='link')
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        message = self._outbox_message(result)
        self.assertIsNotNone(message)
        self.assertIsNone(message.payload)

    def test_none_mode_does_not_queue_an_email(self):
        self.add_email_template('generated-document', template='Hi {firstname}', subject='Your document')
        document_template = self.make_document_template(key='invitation-letter', delivery_mode='none')
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        self.assertIsNone(self._outbox_message(result))

    def test_missing_email_template_is_skipped_not_fatal(self):
        document_template = self.make_document_template(key='invitation-letter', delivery_mode='attachment')
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        self.assertEqual(result.status, GeneratedDocumentStatus.GENERATED)
        self.assertIsNone(self._outbox_message(result))

    def test_custom_email_template_key_is_used(self):
        self.add_email_template('visa-letter-ready', template='Hi {firstname}', subject='Visa letter ready')
        document_template = self.make_document_template(key='visa-letter', delivery_mode='attachment')
        document_template.email_template_key = 'visa-letter-ready'
        db.session.commit()
        self.make_variant(document_template, placeholders={'firstname'})

        result = generate_document(document_template, self.user, self.user, self.event, client=FakeGoogleClient())

        message = self._outbox_message(result)
        self.assertEqual(message.subject, 'Visa letter ready')
