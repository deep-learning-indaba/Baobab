import mock

from app.utils.testing import ApiTestCase


class FileDownloadApiTest(ApiTestCase):

    def _mock_bucket(self, mock_get_bucket, content_type):
        mock_blob = mock_get_bucket.return_value.blob.return_value
        mock_blob.download_to_filename.return_value = None
        mock_blob.reload.return_value = None
        mock_blob.content_type = content_type
        return mock_blob

    def test_download_succeeds_without_origin_or_referer(self):
        # Regression test: file downloads are opened as direct top-level
        # navigations (e.g. a link opened in a new tab), so there's no
        # Origin header and the link is rel="noreferrer", so there's no
        # Referer either. This must not be rejected by organisation
        # resolution, which the file handler doesn't use.
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            self._mock_bucket(mock_get_bucket, 'application/pdf')

            response = self.app.get(
                '/api/v1/file?filename=abc123',
                headers={'Referer': 'https://some-untrusted-domain.example.com/'}
            )

        self.assertEqual(response.status_code, 200)
        mock_get_bucket.return_value.blob.assert_called_with('abc123')

    def test_download_defaults_to_attachment_for_non_image_content_type(self):
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            self._mock_bucket(mock_get_bucket, 'application/pdf')
            response = self.app.get('/api/v1/file?filename=abc123')

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])

    def test_download_defaults_to_inline_for_image_content_type(self):
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            self._mock_bucket(mock_get_bucket, 'image/png')
            response = self.app.get('/api/v1/file?filename=abc123')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get('Content-Disposition'))
        self.assertEqual(response.headers['Content-Type'], 'image/png')

    def test_download_explicit_disposition_overrides_content_type(self):
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            self._mock_bucket(mock_get_bucket, 'image/png')
            response = self.app.get('/api/v1/file?filename=abc123&disposition=attachment')

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers['Content-Disposition'])

    def test_download_explicit_inline_disposition_skips_reload_decision_but_still_sets_mimetype(self):
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            self._mock_bucket(mock_get_bucket, 'image/jpeg')
            response = self.app.get('/api/v1/file?filename=abc123&disposition=inline')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get('Content-Disposition'))
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
