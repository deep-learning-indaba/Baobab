import os
import tempfile
import unittest

from app.utils.emailer import _build_message


def _content_types(message):
    return [part.get_content_type() for part in message.get_payload()]


class BuildMessageTest(unittest.TestCase):
    """A message carrying both a plain text and an HTML body must present them as
    alternatives. In a multipart/mixed a client renders every part in sequence, so
    the reader sees the same message twice — once as unrendered markdown."""

    def _build(self, body_text='Plain body', body_html='<p>HTML body</p>', file_name='', file_path=''):
        return _build_message(
            recipient='guest@example.com',
            subject='Subject',
            body_text=body_text,
            body_html=body_html,
            charset='UTF-8',
            file_name=file_name,
            file_path=file_path,
            sender_name='My Org',
            sender_email='org@example.com',
        )

    def test_text_and_html_are_alternatives_of_each_other(self):
        message = self._build()

        self.assertEqual(message.get_content_type(), 'multipart/alternative')
        self.assertEqual(_content_types(message), ['text/plain', 'text/html'])

    def test_html_comes_last_so_clients_prefer_it(self):
        message = self._build()

        self.assertEqual(message.get_payload()[-1].get_content_type(), 'text/html')

    def test_no_empty_html_part_when_there_is_no_html_body(self):
        """An empty HTML alternative is the one a client picks, so it would render
        as a blank message."""
        message = self._build(body_html='')

        self.assertEqual(_content_types(message), ['text/plain'])

    def test_both_bodies_survive_intact(self):
        message = self._build(body_text='Plain body', body_html='<p>HTML body</p>')

        plain, html_part = message.get_payload()
        self.assertEqual(plain.get_payload(decode=True).decode('utf-8'), 'Plain body')
        self.assertEqual(html_part.get_payload(decode=True).decode('utf-8'), '<p>HTML body</p>')

    def test_headers_are_set_on_the_outermost_message(self):
        message = self._build()

        self.assertEqual(message['Subject'], 'Subject')
        self.assertEqual(message['To'], 'guest@example.com')
        self.assertEqual(message['From'], 'My Org <org@example.com>')

    def test_utf8_body_is_preserved(self):
        message = self._build(body_text='3 Sleeps ✈️', body_html='<p>3 Sleeps ✈️</p>')

        plain = message.get_payload()[0].get_payload(decode=True).decode('utf-8')
        self.assertEqual(plain, '3 Sleeps ✈️')


class BuildMessageWithAttachmentTest(unittest.TestCase):
    """An attachment is not an alternative to the body, so it must sit beside the
    alternative pair rather than replacing it."""

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix='.pdf')
        with os.fdopen(handle, 'wb') as f:
            f.write(b'%PDF-1.4 fake')

    def tearDown(self):
        os.unlink(self.path)

    def _build(self, body_html='<p>HTML body</p>'):
        return _build_message(
            recipient='guest@example.com',
            subject='Subject',
            body_text='Plain body',
            body_html=body_html,
            charset='UTF-8',
            file_name='letter.pdf',
            file_path=self.path,
            sender_name='My Org',
            sender_email='org@example.com',
        )

    def test_attachment_sits_alongside_the_alternative_body(self):
        message = self._build()

        self.assertEqual(message.get_content_type(), 'multipart/mixed')
        self.assertEqual(_content_types(message),
                         ['multipart/alternative', 'application/octet-stream'])

    def test_the_nested_body_still_offers_both_renderings(self):
        message = self._build()

        body = message.get_payload()[0]
        self.assertEqual(_content_types(body), ['text/plain', 'text/html'])

    def test_attachment_is_named_and_base64_encoded(self):
        message = self._build()

        attachment = message.get_payload()[1]
        self.assertIn('letter.pdf', attachment['Content-Disposition'])
        self.assertEqual(attachment['Content-Transfer-Encoding'], 'base64')
        self.assertEqual(attachment.get_payload(decode=True), b'%PDF-1.4 fake')

    def test_a_text_only_body_with_an_attachment_has_no_empty_html_part(self):
        message = self._build(body_html='')

        body = message.get_payload()[0]
        self.assertEqual(_content_types(body), ['text/plain'])


if __name__ == '__main__':
    unittest.main()
