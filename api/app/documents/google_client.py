"""Thin wrapper around the Drive/Docs/Slides APIs used for document templates.

Everything that talks to Google goes through this one class, built once with
real (or, in tests, fake) service objects injected in - the existing
invitationletter/generator.py calls googleapiclient.discovery.build() inline at
module scope, which is why nothing in it has ever had a unit test. Giving the
three services a single injectable seam is what makes google_client_test.py
possible without a network call.
"""
import random
import re
import time
import uuid

from config import GCP_CREDENTIALS_DICT
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.documents.resolver import extract_placeholder_occurrences


SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
]

NATIVE_MIME_TYPES = {
    'application/vnd.google-apps.document': 'document',
    'application/vnd.google-apps.presentation': 'presentation',
}

RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


class GoogleApiError(Exception):
    """A Drive/Docs/Slides API failure, decoupled from googleapiclient's own
    HttpError shape so callers (and tests) don't need to construct one."""

    def __init__(self, status_code, message=''):
        super().__init__(message or f'Google API error {status_code}')
        self.status_code = status_code


class AccessStatus:
    OK = 'ok'
    NOT_FOUND = 'not_found'
    NO_PERMISSION = 'no_permission'
    COPY_DISABLED = 'copy_disabled'
    WRONG_TYPE = 'wrong_type'
    ERROR = 'error'


class AccessCheckResult:
    def __init__(self, status, file_id=None, file_name=None, file_type=None, detail=None):
        self.status = status
        self.file_id = file_id
        self.file_name = file_name
        self.file_type = file_type
        self.detail = detail

    def to_dict(self):
        return {
            'status': self.status,
            'file_id': self.file_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'detail': self.detail,
        }


_FILE_ID_PATTERNS = (
    re.compile(r'/document/d/([a-zA-Z0-9_-]+)'),
    re.compile(r'/presentation/d/([a-zA-Z0-9_-]+)'),
    re.compile(r'[?&]id=([a-zA-Z0-9_-]+)'),
)
_BARE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{10,}$')


def extract_file_id(value):
    """A Drive file id from a pasted URL in any of Google's link formats, or a
    bare id typed directly. None if nothing recognisable is found."""
    if not value:
        return None
    value = value.strip()
    for pattern in _FILE_ID_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)
    if _BARE_ID_PATTERN.match(value):
        return value
    return None


def _wrap_http_error(error):
    status_code = error.resp.status if getattr(error, 'resp', None) is not None else 0
    # HttpError.reason is the single human-readable message Google sent back
    # (e.g. "Slides API has not been used in project X... Enable it by
    # visiting <url>"). str(error) repeats that same text again inside a
    # "Details: [...]" JSON dump, which is redundant once this reaches an
    # admin-facing error message rather than a log line.
    message = getattr(error, 'reason', None) or str(error)
    return GoogleApiError(status_code, message)


def _with_retry(func, sleep_fn, max_attempts=4):
    attempt = 0
    while True:
        attempt += 1
        try:
            return func()
        except HttpError as e:
            wrapped = _wrap_http_error(e)
            if wrapped.status_code not in RETRYABLE_STATUS_CODES or attempt >= max_attempts:
                raise wrapped
            sleep_fn(min(2 ** attempt, 20) + random.random())
        except GoogleApiError as e:
            if e.status_code not in RETRYABLE_STATUS_CODES or attempt >= max_attempts:
                raise
            sleep_fn(min(2 ** attempt, 20) + random.random())


def _build_credentials():
    if GCP_CREDENTIALS_DICT['private_key'] == 'dummy':
        credentials, _ = default(scopes=SCOPES)
        if not credentials.valid:
            credentials.refresh(Request())
        return credentials

    creds_dict = dict(GCP_CREDENTIALS_DICT)
    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    return service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


def describe_configured_identity():
    """The identity Google API calls will actually authenticate as, for
    display in the admin UI's access-check remediation copy.

    Returns (email_or_None, is_dedicated_service_account).

    GCP_CREDENTIALS_DICT['client_email'] is only meaningful when a real
    service account is configured (the `else` branch of _build_credentials).
    In the 'dummy' branch, _build_credentials never touches that dict at all -
    it falls through to google.auth.default(), i.e. whatever Application
    Default Credentials happen to be available in this environment (a
    developer's own `gcloud auth application-default login`, or nothing).
    Reporting the placeholder client_email as "the service account to share
    the doc with" in that case names an address that both isn't real and
    isn't what's actually authenticating - worse than reporting nothing.
    """
    if GCP_CREDENTIALS_DICT['private_key'] != 'dummy':
        return GCP_CREDENTIALS_DICT.get('client_email'), True

    try:
        credentials, _ = default(scopes=SCOPES)
    except DefaultCredentialsError:
        return None, False

    # Only a service-account-flavoured ADC credential (e.g. GOOGLE_APPLICATION_
    # CREDENTIALS pointed at a key file, or real GCE/Cloud Run metadata) exposes
    # this. User credentials from `gcloud auth application-default login` -
    # what a local dev environment normally has - do not, and aren't a service
    # account regardless.
    return getattr(credentials, 'service_account_email', None), False


def build_default_client(working_folder_id=None):
    """The real client, backed by the service account configured for this deployment."""
    credentials = _build_credentials()
    return GoogleWorkspaceClient(
        docs_service=build('docs', 'v1', credentials=credentials),
        slides_service=build('slides', 'v1', credentials=credentials),
        drive_service=build('drive', 'v3', credentials=credentials),
        sheets_service=build('sheets', 'v4', credentials=credentials),
        working_folder_id=working_folder_id,
    )


class GoogleWorkspaceClient:
    def __init__(self, docs_service, slides_service, drive_service,
                 sheets_service=None, working_folder_id=None, sleep_fn=time.sleep):
        self.docs = docs_service
        self.slides = slides_service
        self.drive = drive_service
        self.sheets = sheets_service
        self.working_folder_id = working_folder_id
        self._sleep_fn = sleep_fn

    def _call(self, func):
        return _with_retry(func, self._sleep_fn)

    def _drive_file_body(self, **fields):
        """Drive file metadata with `parents` set to the configured Shared
        Drive working folder, if any.

        A bare service account has no personal Drive storage of its own, so
        a newly created or copied file needs a Shared Drive parent to have
        anywhere to be written - both generate_pdf's template copy and
        create_spreadsheet's new file need this.
        """
        body = dict(fields)
        if self.working_folder_id:
            body['parents'] = [self.working_folder_id]
        return body

    # -- Access checking (design section 6.2) --------------------------------

    def check_access(self, file_id):
        try:
            meta = self._call(lambda: self.drive.files().get(
                fileId=file_id,
                fields='id,name,mimeType,capabilities/canCopy',
                supportsAllDrives=True,
            ).execute())
        except GoogleApiError as e:
            if e.status_code == 404:
                return AccessCheckResult(AccessStatus.NOT_FOUND)
            if e.status_code == 403:
                return AccessCheckResult(AccessStatus.NO_PERMISSION)
            return AccessCheckResult(AccessStatus.ERROR, detail=str(e))

        mime_type = meta.get('mimeType')
        file_type = NATIVE_MIME_TYPES.get(mime_type)
        if file_type is None:
            return AccessCheckResult(
                AccessStatus.WRONG_TYPE, file_id=file_id,
                file_name=meta.get('name'), detail=mime_type)

        can_copy = (meta.get('capabilities') or {}).get('canCopy', True)
        if not can_copy:
            return AccessCheckResult(
                AccessStatus.COPY_DISABLED, file_id=file_id,
                file_name=meta.get('name'), file_type=file_type)

        return AccessCheckResult(
            AccessStatus.OK, file_id=file_id, file_name=meta.get('name'), file_type=file_type)

    # -- Placeholder scanning (design section 6.3) ---------------------------

    def scan_placeholders(self, file_id, file_type):
        if file_type == 'document':
            return self._scan_document(file_id)
        if file_type == 'presentation':
            return self._scan_presentation(file_id)
        raise ValueError(f'Unknown file_type: {file_type}')

    def _scan_document(self, file_id):
        doc = self._call(lambda: self.docs.documents().get(documentId=file_id).execute())

        texts = list(_walk_docs_body(doc.get('body', {}).get('content', [])))
        for header in (doc.get('headers') or {}).values():
            texts.extend(_walk_docs_body(header.get('content', [])))
        for footer in (doc.get('footers') or {}).values():
            texts.extend(_walk_docs_body(footer.get('content', [])))
        for footnote in (doc.get('footnotes') or {}).values():
            texts.extend(_walk_docs_body(footnote.get('content', [])))

        occurrences = set()
        for text in texts:
            occurrences |= extract_placeholder_occurrences(text)
        return occurrences

    def _scan_presentation(self, file_id):
        pres = self._call(lambda: self.slides.presentations().get(
            presentationId=file_id).execute())

        texts = []
        for slide in pres.get('slides', []):
            texts.extend(_walk_slide_elements(slide.get('pageElements', [])))
            notes_page = (slide.get('slideProperties') or {}).get('notesPage')
            if notes_page:
                texts.extend(_walk_slide_elements(notes_page.get('pageElements', [])))
        for layout in pres.get('layouts', []):
            texts.extend(_walk_slide_elements(layout.get('pageElements', [])))

        occurrences = set()
        for text in texts:
            occurrences |= extract_placeholder_occurrences(text)
        return occurrences

    # -- Generation (design section 6.4) -------------------------------------

    def generate_pdf(self, google_file_id, google_file_type, replacements):
        """Copy the template, substitute every {raw occurrence} in
        `replacements` with its resolved value, export to PDF, delete the copy.

        `replacements` maps the exact raw placeholder occurrence (as returned
        by scan_placeholders / PlaceholderResolver, without braces) to the
        text that should replace `{occurrence}` in the document.

        Returns the PDF bytes. The copy is always deleted, even if replacement
        or export raises.
        """
        copy_body = self._drive_file_body(name=f'baobab-doc-{uuid.uuid4().hex}')

        copied = self._call(lambda: self.drive.files().copy(
            fileId=google_file_id, body=copy_body, supportsAllDrives=True).execute())
        copy_id = copied['id']

        try:
            requests_list = [
                {
                    'replaceAllText': {
                        'containsText': {'text': '{' + raw + '}', 'matchCase': False},
                        'replaceText': value,
                    }
                }
                for raw, value in replacements.items()
            ]
            if requests_list:
                if google_file_type == 'document':
                    self._call(lambda: self.docs.documents().batchUpdate(
                        documentId=copy_id, body={'requests': requests_list}).execute())
                else:
                    self._call(lambda: self.slides.presentations().batchUpdate(
                        presentationId=copy_id, body={'requests': requests_list}).execute())

            return self._call(lambda: self.drive.files().export(
                fileId=copy_id, mimeType='application/pdf').execute())
        finally:
            self._call(lambda: self.drive.files().delete(
                fileId=copy_id, supportsAllDrives=True).execute())

    # -- Sheets export ---------------------------------------------------

    # Rows per values().update() call. Google enforces a per-request payload
    # size limit that isn't published as a precise number, so this chunks
    # defensively rather than trying to size requests exactly - a form with
    # many questions and long free-text answers can otherwise build one
    # request large enough to trip it, and Sheets rejects that request
    # (and only that request) wholesale rather than partially applying it.
    _SHEETS_WRITE_BATCH_ROWS = 500

    def create_spreadsheet(self, title, rows, share_with_email):
        """Create a new Sheet, write `rows` (a list of lists, header first)
        starting at A1, share it with `share_with_email` as a writer, and
        return its URL.

        A bare service account has no personal Drive storage of its own, so
        creating the file with no parent (via the Sheets API's create, which
        has no `parents` field anyway) fails outright with a storage-quota
        error. Creating it via the Drive API instead, inside the same Shared
        Drive working folder generate_pdf's template copies use (see
        _drive_file_body), gives it a parent whose storage the domain owns
        rather than the service account. Unlike those copies, this file is
        the deliverable itself and is deliberately left in place rather than
        swept.
        """
        if self.working_folder_id:
            create_body = self._drive_file_body(
                name=title, mimeType='application/vnd.google-apps.spreadsheet')
            created = self._call(lambda: self.drive.files().create(
                body=create_body, supportsAllDrives=True, fields='id').execute())
            spreadsheet_id = created['id']
            spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit'
        else:
            spreadsheet = self._call(lambda: self.sheets.spreadsheets().create(
                body={'properties': {'title': title}}, fields='spreadsheetId,spreadsheetUrl').execute())
            spreadsheet_id = spreadsheet['spreadsheetId']
            spreadsheet_url = spreadsheet['spreadsheetUrl']

        for start in range(0, len(rows), self._SHEETS_WRITE_BATCH_ROWS):
            self._write_rows_batch(spreadsheet_id, start, rows[start:start + self._SHEETS_WRITE_BATCH_ROWS])

        self._call(lambda: self.drive.permissions().create(
            fileId=spreadsheet_id,
            body={'type': 'user', 'role': 'writer', 'emailAddress': share_with_email},
            sendNotificationEmail=False,
            supportsAllDrives=True,
        ).execute())

        return spreadsheet_url

    def _write_rows_batch(self, spreadsheet_id, start_row_offset, chunk):
        # start_row_offset is 0-indexed into the full `rows` list (header is
        # row 0), so sheet row start_row_offset + 1 is where this chunk goes.
        self._call(lambda: self.sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'A{start_row_offset + 1}',
            valueInputOption='RAW',
            body={'values': chunk},
        ).execute())


def _walk_docs_body(content):
    """Paragraph/table-cell text from a Docs body, footer, header or footnote,
    one string per paragraph with its text runs concatenated in order.

    The concatenation is the part that matters: Google splits a placeholder
    like {firstname} across several textRuns whenever any part of it was
    styled, spell-checked, or pasted, so scanning each run in isolation finds
    nothing in a real-world document. replaceAllText matches across run
    boundaries on its own; only detection needs this.
    """
    texts = []
    for element in content or []:
        if 'paragraph' in element:
            texts.append(_concat_docs_runs(element['paragraph'].get('elements', [])))
        elif 'table' in element:
            for row in element['table'].get('tableRows', []):
                for cell in row.get('tableCells', []):
                    texts.extend(_walk_docs_body(cell.get('content', [])))
        elif 'tableOfContents' in element:
            texts.extend(_walk_docs_body(element['tableOfContents'].get('content', [])))
    return texts


def _concat_docs_runs(elements):
    return ''.join(
        (el.get('textRun') or {}).get('content', '') for el in elements or [] if 'textRun' in el
    )


def _walk_slide_elements(elements):
    texts = []
    for el in elements or []:
        shape = el.get('shape')
        if shape and shape.get('text'):
            texts.append(_concat_slide_runs(shape['text'].get('textElements', [])))

        table = el.get('table')
        if table:
            for row in table.get('tableRows', []):
                for cell in row.get('tableCells', []):
                    cell_text = cell.get('text')
                    if cell_text:
                        texts.append(_concat_slide_runs(cell_text.get('textElements', [])))

        group = el.get('elementGroup')
        if group:
            texts.extend(_walk_slide_elements(group.get('children', [])))
    return texts


def _concat_slide_runs(text_elements):
    return ''.join(
        (te.get('textRun') or {}).get('content', '')
        for te in text_elements or [] if 'textRun' in te
    )
