"""GoogleWorkspaceClient - design section 6. No test here touches the network:
every Drive/Docs/Slides call goes through a fake service object built below,
matching the shape googleapiclient's discovery-built services present
(chained .files().get(...).execute() etc).
"""
import unittest

from googleapiclient.errors import HttpError

from app.documents.google_client import (
    GoogleWorkspaceClient, AccessStatus, GoogleApiError, extract_file_id,
)


def _http_error(status):
    class FakeResponse:
        pass
    resp = FakeResponse()
    resp.status = status
    resp.reason = 'error'
    return HttpError(resp, b'{}')


class _Execuatable:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error

    def execute(self):
        if self._error is not None:
            raise self._error
        return self._result


class FakeDriveFiles:
    def __init__(self, get_result=None, get_error=None, copy_result=None,
                 export_result=None, delete_error=None, create_result=None):
        self._get_result = get_result
        self._get_error = get_error
        self._copy_result = copy_result
        self._export_result = export_result
        self._delete_error = delete_error
        self._create_result = create_result or {'id': 'new-file-id'}
        self.delete_calls = []
        self.copy_calls = []
        self.create_calls = []

    def get(self, **kwargs):
        return _Execuatable(self._get_result, self._get_error)

    def copy(self, **kwargs):
        self.copy_calls.append(kwargs)
        return _Execuatable(self._copy_result)

    def export(self, **kwargs):
        return _Execuatable(self._export_result)

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        return _Execuatable(None, self._delete_error)

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return _Execuatable(self._create_result)


class FakeDrivePermissions:
    def __init__(self):
        self.create_calls = []

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return _Execuatable({})


class FakeDriveService:
    def __init__(self, files, permissions=None):
        self._files = files
        self._permissions = permissions or FakeDrivePermissions()

    def files(self):
        return self._files

    def permissions(self):
        return self._permissions


class FakeSheetsService:
    def __init__(self, create_result=None):
        self._create_result = create_result or {
            'spreadsheetId': 'sheet-1',
            'spreadsheetUrl': 'https://docs.google.com/spreadsheets/d/sheet-1/edit',
        }
        self.create_calls = []
        self.update_calls = []

    def spreadsheets(self):
        service = self

        class _Values:
            def update(inner_self, **kwargs):
                service.update_calls.append(kwargs)
                return _Execuatable({})

        class _Spreadsheets:
            def create(inner_self, **kwargs):
                service.create_calls.append(kwargs)
                return _Execuatable(service._create_result)

            def values(inner_self):
                return _Values()

        return _Spreadsheets()


class FakeDocsService:
    def __init__(self, doc=None):
        self._doc = doc
        self.batch_calls = []

    def documents(self):
        service = self

        class _Docs:
            def get(inner_self, **kwargs):
                return _Execuatable(service._doc)

            def batchUpdate(inner_self, **kwargs):
                service.batch_calls.append(kwargs)
                return _Execuatable({})

        return _Docs()


class FakeSlidesService:
    def __init__(self, presentation=None):
        self._presentation = presentation
        self.batch_calls = []

    def presentations(self):
        service = self

        class _Slides:
            def get(inner_self, **kwargs):
                return _Execuatable(service._presentation)

            def batchUpdate(inner_self, **kwargs):
                service.batch_calls.append(kwargs)
                return _Execuatable({})

        return _Slides()


def _client(drive=None, docs=None, slides=None, sheets=None, working_folder_id=None):
    return GoogleWorkspaceClient(
        docs_service=docs, slides_service=slides, drive_service=drive,
        sheets_service=sheets, working_folder_id=working_folder_id,
        sleep_fn=lambda seconds: None,
    )


class TestExtractFileId(unittest.TestCase):

    def test_google_docs_edit_url(self):
        url = 'https://docs.google.com/document/d/1AbC-XyZ_123/edit'
        self.assertEqual(extract_file_id(url), '1AbC-XyZ_123')

    def test_google_slides_edit_url(self):
        url = 'https://docs.google.com/presentation/d/1AbC-XyZ_123/edit#slide=id.p'
        self.assertEqual(extract_file_id(url), '1AbC-XyZ_123')

    def test_query_string_id_format(self):
        url = 'https://drive.google.com/open?id=1AbC-XyZ_123'
        self.assertEqual(extract_file_id(url), '1AbC-XyZ_123')

    def test_bare_id(self):
        self.assertEqual(extract_file_id('1AbC-XyZ_123456'), '1AbC-XyZ_123456')

    def test_garbage_returns_none(self):
        self.assertIsNone(extract_file_id('not a link'))

    def test_empty_returns_none(self):
        self.assertIsNone(extract_file_id(''))
        self.assertIsNone(extract_file_id(None))


class TestCheckAccess(unittest.TestCase):

    def test_ok_for_native_google_doc_with_copy_allowed(self):
        files = FakeDriveFiles(get_result={
            'id': 'abc', 'name': 'Invitation Letter',
            'mimeType': 'application/vnd.google-apps.document',
            'capabilities': {'canCopy': True},
        })
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.OK)
        self.assertEqual(result.file_type, 'document')
        self.assertEqual(result.file_name, 'Invitation Letter')

    def test_ok_for_native_slides(self):
        files = FakeDriveFiles(get_result={
            'id': 'abc', 'name': 'Certificate',
            'mimeType': 'application/vnd.google-apps.presentation',
            'capabilities': {'canCopy': True},
        })
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.OK)
        self.assertEqual(result.file_type, 'presentation')

    def test_not_found(self):
        files = FakeDriveFiles(get_error=_http_error(404))
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('missing')

        self.assertEqual(result.status, AccessStatus.NOT_FOUND)

    def test_no_permission(self):
        files = FakeDriveFiles(get_error=_http_error(403))
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('forbidden')

        self.assertEqual(result.status, AccessStatus.NO_PERMISSION)

    def test_copy_disabled(self):
        files = FakeDriveFiles(get_result={
            'id': 'abc', 'name': 'Locked Doc',
            'mimeType': 'application/vnd.google-apps.document',
            'capabilities': {'canCopy': False},
        })
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.COPY_DISABLED)

    def test_wrong_type_for_uploaded_docx(self):
        files = FakeDriveFiles(get_result={
            'id': 'abc', 'name': 'letter.docx',
            'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        })
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.WRONG_TYPE)

    def test_other_error_status(self):
        files = FakeDriveFiles(get_error=_http_error(500))
        client = _client(drive=FakeDriveService(files))

        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.ERROR)


def _text_run(content):
    return {'textRun': {'content': content}}


class TestScanDocumentPlaceholders(unittest.TestCase):

    def test_placeholder_split_across_multiple_text_runs_is_still_detected(self):
        """The critical case from design section 6.3: Google splits a typed
        {firstname} across several textRuns whenever any part of it was
        styled or spell-checked. Scanning each run in isolation would find
        nothing; runs must be concatenated within their paragraph first."""
        doc = {
            'body': {'content': [
                {'paragraph': {'elements': [
                    _text_run('Dear '),
                    _text_run('{first'),
                    _text_run('name}'),
                    _text_run(','),
                ]}},
            ]},
        }
        client = _client(docs=FakeDocsService(doc=doc))

        placeholders = client.scan_placeholders('doc-id', 'document')

        self.assertEqual(placeholders, {'firstname'})

    def test_placeholder_in_table_cell(self):
        doc = {
            'body': {'content': [
                {'table': {'tableRows': [
                    {'tableCells': [
                        {'content': [{'paragraph': {'elements': [_text_run('{lastname}')]}}]},
                    ]},
                ]}},
            ]},
        }
        client = _client(docs=FakeDocsService(doc=doc))

        placeholders = client.scan_placeholders('doc-id', 'document')

        self.assertEqual(placeholders, {'lastname'})

    def test_placeholder_in_header_and_footer(self):
        doc = {
            'body': {'content': []},
            'headers': {'h1': {'content': [{'paragraph': {'elements': [_text_run('{event.name}')]}}]}},
            'footers': {'f1': {'content': [{'paragraph': {'elements': [_text_run('{current_year}')]}}]}},
        }
        client = _client(docs=FakeDocsService(doc=doc))

        placeholders = client.scan_placeholders('doc-id', 'document')

        self.assertEqual(placeholders, {'event.name', 'current_year'})

    def test_no_placeholders_returns_empty_set(self):
        doc = {'body': {'content': [{'paragraph': {'elements': [_text_run('Plain text.')]}}]}}
        client = _client(docs=FakeDocsService(doc=doc))

        self.assertEqual(client.scan_placeholders('doc-id', 'document'), set())


def _slide_text_element(content):
    return {'textRun': {'content': content}}


class TestScanPresentationPlaceholders(unittest.TestCase):

    def test_placeholder_split_across_runs_in_a_shape(self):
        presentation = {
            'slides': [
                {'pageElements': [
                    {'shape': {'text': {'textElements': [
                        _slide_text_element('{first'),
                        _slide_text_element('name}'),
                        _slide_text_element(' has attended.'),
                    ]}}},
                ]},
            ],
        }
        client = _client(slides=FakeSlidesService(presentation=presentation))

        placeholders = client.scan_placeholders('pres-id', 'presentation')

        self.assertEqual(placeholders, {'firstname'})

    def test_placeholder_in_notes_page(self):
        presentation = {
            'slides': [
                {
                    'pageElements': [],
                    'slideProperties': {'notesPage': {'pageElements': [
                        {'shape': {'text': {'textElements': [_slide_text_element('{firstname}')]}}},
                    ]}},
                },
            ],
        }
        client = _client(slides=FakeSlidesService(presentation=presentation))

        placeholders = client.scan_placeholders('pres-id', 'presentation')

        self.assertEqual(placeholders, {'firstname'})

    def test_placeholder_in_layout(self):
        presentation = {
            'slides': [],
            'layouts': [
                {'pageElements': [
                    {'shape': {'text': {'textElements': [_slide_text_element('{event.name}')]}}},
                ]},
            ],
        }
        client = _client(slides=FakeSlidesService(presentation=presentation))

        placeholders = client.scan_placeholders('pres-id', 'presentation')

        self.assertEqual(placeholders, {'event.name'})

    def test_placeholder_in_grouped_element(self):
        presentation = {
            'slides': [
                {'pageElements': [
                    {'elementGroup': {'children': [
                        {'shape': {'text': {'textElements': [_slide_text_element('{lastname}')]}}},
                    ]}},
                ]},
            ],
        }
        client = _client(slides=FakeSlidesService(presentation=presentation))

        placeholders = client.scan_placeholders('pres-id', 'presentation')

        self.assertEqual(placeholders, {'lastname'})

    def test_placeholder_in_table_cell(self):
        presentation = {
            'slides': [
                {'pageElements': [
                    {'table': {'tableRows': [
                        {'tableCells': [
                            {'text': {'textElements': [_slide_text_element('{gender}')]}},
                        ]},
                    ]}},
                ]},
            ],
        }
        client = _client(slides=FakeSlidesService(presentation=presentation))

        placeholders = client.scan_placeholders('pres-id', 'presentation')

        self.assertEqual(placeholders, {'gender'})


class TestGeneratePdf(unittest.TestCase):

    def test_copy_replace_export_delete_sequence(self):
        files = FakeDriveFiles(
            copy_result={'id': 'copy-123'},
            export_result=b'%PDF-1.4 fake bytes',
        )
        docs = FakeDocsService()
        client = _client(drive=FakeDriveService(files), docs=docs)

        result = client.generate_pdf('template-id', 'document', {'firstname': 'Amina'})

        self.assertEqual(result, b'%PDF-1.4 fake bytes')
        self.assertEqual(files.copy_calls[0]['fileId'], 'template-id')
        self.assertEqual(len(docs.batch_calls), 1)
        request = docs.batch_calls[0]['body']['requests'][0]['replaceAllText']
        self.assertEqual(request['containsText']['text'], '{firstname}')
        self.assertEqual(request['replaceText'], 'Amina')
        self.assertEqual(files.delete_calls[0]['fileId'], 'copy-123')

    def test_uses_slides_batch_update_for_presentation_type(self):
        files = FakeDriveFiles(copy_result={'id': 'copy-1'}, export_result=b'pdf')
        slides = FakeSlidesService()
        client = _client(drive=FakeDriveService(files), slides=slides)

        client.generate_pdf('template-id', 'presentation', {'firstname': 'Amina'})

        self.assertEqual(len(slides.batch_calls), 1)

    def test_copy_is_deleted_even_when_export_raises(self):
        files = FakeDriveFiles(copy_result={'id': 'copy-999'}, get_error=None)
        files._export_result = None

        class RaisingFiles(FakeDriveFiles):
            def export(self, **kwargs):
                return _Execuatable(None, _http_error(500))

        raising_files = RaisingFiles(copy_result={'id': 'copy-999'})
        client = _client(drive=FakeDriveService(raising_files), docs=FakeDocsService())

        with self.assertRaises(GoogleApiError):
            client.generate_pdf('template-id', 'document', {})

        self.assertEqual(raising_files.delete_calls[0]['fileId'], 'copy-999')

    def test_working_folder_id_passed_to_copy(self):
        files = FakeDriveFiles(copy_result={'id': 'copy-1'}, export_result=b'pdf')
        client = GoogleWorkspaceClient(
            docs_service=FakeDocsService(), slides_service=None,
            drive_service=FakeDriveService(files),
            working_folder_id='folder-42', sleep_fn=lambda s: None,
        )

        client.generate_pdf('template-id', 'document', {})

        self.assertEqual(files.copy_calls[0]['body']['parents'], ['folder-42'])


class TestCreateSpreadsheet(unittest.TestCase):

    def test_creates_via_drive_api_inside_working_folder(self):
        # A bare service account has no personal Drive storage, so a new file
        # must be created with a Shared Drive folder as parent - something
        # only the Drive API's files().create() (not spreadsheets().create())
        # can express.
        files = FakeDriveFiles(create_result={'id': 'sheet-42'})
        permissions = FakeDrivePermissions()
        sheets = FakeSheetsService()
        client = _client(
            drive=FakeDriveService(files, permissions), sheets=sheets,
            working_folder_id='folder-42',
        )

        url = client.create_spreadsheet(
            title='My Export', rows=[['Name', 'Email'], ['Ada', 'ada@example.com']],
            share_with_email='admin@example.com',
        )

        self.assertEqual(url, 'https://docs.google.com/spreadsheets/d/sheet-42/edit')
        self.assertEqual(files.create_calls[0]['body']['parents'], ['folder-42'])
        self.assertEqual(files.create_calls[0]['body']['mimeType'], 'application/vnd.google-apps.spreadsheet')
        self.assertEqual(sheets.create_calls, [])  # Sheets API create() was not used

        self.assertEqual(sheets.update_calls[0]['spreadsheetId'], 'sheet-42')
        self.assertEqual(sheets.update_calls[0]['body']['values'][0], ['Name', 'Email'])

        self.assertEqual(permissions.create_calls[0]['fileId'], 'sheet-42')
        self.assertEqual(permissions.create_calls[0]['body']['emailAddress'], 'admin@example.com')
        self.assertEqual(permissions.create_calls[0]['body']['role'], 'writer')

    def test_falls_back_to_sheets_api_without_working_folder(self):
        files = FakeDriveFiles()
        permissions = FakeDrivePermissions()
        sheets = FakeSheetsService(create_result={
            'spreadsheetId': 'sheet-7', 'spreadsheetUrl': 'https://docs.google.com/spreadsheets/d/sheet-7/edit',
        })
        client = _client(drive=FakeDriveService(files, permissions), sheets=sheets)

        url = client.create_spreadsheet(
            title='My Export', rows=[['Name']], share_with_email='admin@example.com'
        )

        self.assertEqual(url, 'https://docs.google.com/spreadsheets/d/sheet-7/edit')
        self.assertEqual(len(sheets.create_calls), 1)
        self.assertEqual(files.create_calls, [])  # Drive API create() was not used

    def test_skips_values_update_when_no_rows(self):
        files = FakeDriveFiles(create_result={'id': 'sheet-1'})
        sheets = FakeSheetsService()
        client = _client(
            drive=FakeDriveService(files, FakeDrivePermissions()), sheets=sheets,
            working_folder_id='folder-1',
        )

        client.create_spreadsheet(title='Empty', rows=[], share_with_email='admin@example.com')

        self.assertEqual(sheets.update_calls, [])

    def test_writes_large_row_sets_in_multiple_batches(self):
        # A single values().update() carrying the whole dataset is what risks
        # tripping Google's per-request payload size limit for a large form -
        # this proves large row sets actually go out in more than one call,
        # each starting at the right sheet row, with nothing dropped or
        # duplicated across the batch boundary.
        files = FakeDriveFiles(create_result={'id': 'sheet-1'})
        sheets = FakeSheetsService()
        client = _client(
            drive=FakeDriveService(files, FakeDrivePermissions()), sheets=sheets,
            working_folder_id='folder-1',
        )
        batch_size = client._SHEETS_WRITE_BATCH_ROWS
        rows = [[f'row-{i}'] for i in range(batch_size + 10)]

        client.create_spreadsheet(title='Big Export', rows=rows, share_with_email='admin@example.com')

        self.assertEqual(len(sheets.update_calls), 2)
        self.assertEqual(sheets.update_calls[0]['range'], 'A1')
        self.assertEqual(len(sheets.update_calls[0]['body']['values']), batch_size)
        self.assertEqual(sheets.update_calls[1]['range'], f'A{batch_size + 1}')
        self.assertEqual(sheets.update_calls[1]['body']['values'], rows[batch_size:])

        # Every row appears exactly once, across the two calls, in order.
        written = sheets.update_calls[0]['body']['values'] + sheets.update_calls[1]['body']['values']
        self.assertEqual(written, rows)


class TestRetry(unittest.TestCase):

    def test_retries_on_429_then_succeeds(self):
        attempts = {'count': 0}

        class FlakyFiles(FakeDriveFiles):
            def get(inner_self, **kwargs):
                attempts['count'] += 1
                if attempts['count'] < 3:
                    return _Execuatable(None, _http_error(429))
                return _Execuatable({
                    'id': 'abc', 'name': 'Doc',
                    'mimeType': 'application/vnd.google-apps.document',
                    'capabilities': {'canCopy': True},
                })

        client = _client(drive=FakeDriveService(FlakyFiles()))
        result = client.check_access('abc')

        self.assertEqual(result.status, AccessStatus.OK)
        self.assertEqual(attempts['count'], 3)

    def test_does_not_retry_non_retryable_status(self):
        attempts = {'count': 0}

        class FailingFiles(FakeDriveFiles):
            def get(inner_self, **kwargs):
                attempts['count'] += 1
                return _Execuatable(None, _http_error(404))

        client = _client(drive=FakeDriveService(FailingFiles()))
        client.check_access('abc')

        self.assertEqual(attempts['count'], 1)
