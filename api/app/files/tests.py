import mock

from app.utils.testing import ApiTestCase


class FileDownloadApiTest(ApiTestCase):

    def test_download_succeeds_without_origin_or_referer(self):
        # Regression test: file downloads are opened as direct top-level
        # navigations (e.g. a link opened in a new tab), so there's no
        # Origin header and the link is rel="noreferrer", so there's no
        # Referer either. This must not be rejected by organisation
        # resolution, which the file handler doesn't use.
        with mock.patch('app.files.api.storage.get_storage_bucket') as mock_get_bucket:
            mock_blob = mock_get_bucket.return_value.blob.return_value
            mock_blob.download_to_filename.return_value = None

            response = self.app.get(
                '/api/v1/file?filename=abc123',
                headers={'Referer': 'https://some-untrusted-domain.example.com/'}
            )

        self.assertEqual(response.status_code, 200)
        mock_get_bucket.return_value.blob.assert_called_with('abc123')
