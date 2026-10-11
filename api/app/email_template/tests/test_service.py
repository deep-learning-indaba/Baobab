from datetime import datetime, timedelta
from unittest.mock import patch

from app import db
from app.email_template.engine import EmailRenderError
from app.email_template.models import EmailLayout
from app.email_template.repository import EmailTemplateRepository
from app.email_template.service import (
    Attachment, MissingContextError, queue_email, queue_emails, sample_context)
from app.email_template.registry import EMAIL_TYPES
from app.email_template.views import Recipient
from app.outbox.models import OutboxMessage, OutboxStatus
from app.outbox.repository import OutboxRepository
from app.outbox.sender import deliver_pending
from app.utils.testing import ApiTestCase


class EmailServiceTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.event = self.add_event(name={'en': 'Indaba 2026', 'fr': 'Indaba 2026 FR'},
                                    description={'en': 'the Indaba', 'fr': "l'Indaba"},
                                    languages=['en', 'fr'])
        self.event_id = self.event.id
        self.user = self.add_user(email='thandi@example.org', firstname='Thandi', lastname='Ndlovu',
                                  user_title='Dr')
        self.user_id = self.user.id

    def _messages(self):
        return db.session.query(OutboxMessage).order_by(OutboxMessage.id).all()

    def _offer(self, payment_required=True, grants=True):
        fee = self.add_event_fee(self.event_id, self.user_id, amount=1500, iso_currency_code='ZAR')
        tags = []
        if grants:
            tags.append(self.add_tag(self.event_id, 'GRANT', names={'en': 'Travel grant', 'fr': 'Bourse'},
                                     descriptions={'en': 'Flights', 'fr': 'Vols'}))
        tags.append(self.add_tag(self.event_id, 'OFFER_NOTE', names={'en': 'Bring a laptop', 'fr': 'Portable'},
                                 descriptions={'en': '', 'fr': ''}))
        offer = self.add_offer(self.user_id, self.event_id, payment_required=payment_required,
                               expiry_date=datetime(2026, 6, 5), tags=tags)
        offer.event_fee_id = fee.id
        db.session.commit()
        return offer

    def test_queues_rendered_offer_with_metadata(self):
        queue_email('offer', self.user, event=self.event, context={'offer': self._offer()})
        db.session.commit()

        message = self._messages()[0]
        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.recipient, 'thandi@example.org')
        self.assertEqual(message.user_id, self.user_id)
        self.assertEqual(message.event_id, self.event_id)
        self.assertEqual(message.template_key, 'offer')
        self.assertEqual(message.language, 'en')
        self.assertEqual(message.reply_to, 'abx@indaba.deeplearning')
        self.assertFalse(message.sensitive)
        self.assertEqual(message.subject, 'Indaba 2026 application status update')
        self.assertIn('Dear Dr Thandi Ndlovu', message.body_text)
        self.assertIn('Travel grant', message.body_text)
        self.assertIn('Bring a laptop', message.body_text)
        self.assertIn('1,500.00 ZAR', message.body_text)
        self.assertIn('5 June 2026', message.body_text)
        self.assertIn('<table role="presentation"', message.body_html)
        self.assertIn('/INDABA2025/offer', message.body_html)

    def test_fee_waived_and_no_grants_branch(self):
        queue_email('offer', self.user, event=self.event,
                    context={'offer': self._offer(payment_required=False, grants=False)})
        message = self._messages()[0]
        self.assertIn('Your registration fee has been waived.', message.body_text)
        self.assertNotIn('following grants', message.body_text)

    def test_recipient_language(self):
        self.user.user_primaryLanguage = 'fr'
        db.session.commit()
        queue_email('offer', self.user, event=self.event, context={'offer': self._offer()})
        message = self._messages()[0]
        self.assertEqual(message.language, 'fr')
        self.assertIn('Madame / Monsieur Ndlovu', message.body_text)
        self.assertIn('Indaba 2026 FR', message.subject)
        self.assertIn('5 juin 2026', message.body_text)

    def test_override_precedence(self):
        offer = self._offer()
        EmailTemplateRepository.save('offer', 1, None, 'en', 'Org {{ event.name }}', 'Org body', self.user_id)
        queue_email('offer', self.user, event=self.event, context={'offer': offer})
        EmailTemplateRepository.save('offer', 1, self.event_id, 'en', 'Event subject', 'Event body', self.user_id)
        queue_email('offer', self.user, event=self.event, context={'offer': offer})
        first, second = self._messages()
        self.assertEqual(first.subject, 'Org Indaba 2026')
        self.assertIsNotNone(first.template_revision_id)
        self.assertEqual(second.subject, 'Event subject')
        self.assertIn('Event body', second.body_text)

    def test_context_must_match_declaration(self):
        with self.assertRaises(MissingContextError):
            queue_email('offer', self.user, event=self.event)
        with self.assertRaises(MissingContextError):
            queue_email('offer', self.user, event=self.event, context={'offer': None})

    def test_broken_override_raises_render_error(self):
        EmailTemplateRepository.save('withdrawal', 1, self.event_id, 'en', 'S', '{% if %}', self.user_id)
        with self.assertRaises(EmailRenderError):
            queue_email('withdrawal', self.user, event=self.event)

    def test_non_user_recipient(self):
        referee = Recipient('ref@example.org', firstname='Ama', lastname='Owusu', title='Prof', language='fr')
        request = type('ReferenceRequest', (), {'token': 'abc', 'relation': 'Supervisor'})()
        queue_email('reference-request', referee, event=self.event, context={
            'reference': request, 'candidate': {'name': 'Dr Thandi Ndlovu', 'firstname': 'Thandi'},
            'nominator': None})
        message = self._messages()[0]
        self.assertIsNone(message.user_id)
        self.assertEqual(message.recipient, 'ref@example.org')
        self.assertIn('Madame / Monsieur Owusu', message.body_text)
        self.assertIn('a présenté sa candidature', message.body_text)
        self.assertIn('/reference/abc', message.body_text)

    def test_context_never_contains_organisation_secrets(self):
        email_type = EMAIL_TYPES['offer']
        from app.email_template.service import build_context
        values = build_context(email_type, self.user, self.event.organisation, self.event, 'en',
                               {'offer': self._offer()})
        flattened = repr(values)
        self.assertNotIn('secret_key', flattened)
        self.assertNotIn(self.user.password, flattened)

    def test_layout_brand_colour_footer_and_logo(self):
        db.session.add(EmailLayout(organisation_id=1, event_id=None, language='en', brand_colour='#aa0000',
                                   footer_markdown='Sent by **{{ organisation.name }}**',
                                   logo_url='https://example.org/logo.png'))
        db.session.add(EmailLayout(organisation_id=1, event_id=self.event_id, language='en',
                                   brand_colour='#00aa00'))
        db.session.commit()
        queue_email('offer', self.user, event=self.event, context={'offer': self._offer()})
        message = self._messages()[0]
        self.assertIn('background:#00aa00', message.body_html)
        self.assertIn('Sent by <strong>My Org</strong>', message.body_html)
        self.assertIn('src="https://example.org/logo.png"', message.body_html)
        self.assertTrue(message.body_text.endswith('--\nSent by My Org'))

    def test_attachments_go_in_payload(self):
        queue_email('invitation-letter', self.user, event=self.event,
                    attachments=[Attachment('outbox-attachments/x.pdf', 'Letter.pdf')])
        self.assertEqual(self._messages()[0].payload,
                         {'attachments': [{'blob_name': 'outbox-attachments/x.pdf', 'filename': 'Letter.pdf',
                                           'content_type': 'application/pdf'}]})

    def test_idempotency_key(self):
        self.assertIsNotNone(queue_email('withdrawal', self.user, event=self.event, idempotency_key='k1'))
        db.session.commit()
        self.assertIsNone(queue_email('withdrawal', self.user, event=self.event, idempotency_key='k1'))
        self.assertEqual(len(self._messages()), 1)

    def test_send_now_delivers_and_purges_sensitive_body(self):
        with patch('app.outbox.sender.SmtpConnection.send') as send:
            queue_email('password-reset', self.user, send_now=True,
                        context={'reset': 'https://example.org/resetPassword?resetToken=abc'})
        send.assert_called_once()
        self.assertIn('resetToken=abc', send.call_args.kwargs['body_html'])
        message = self._messages()[0]
        self.assertEqual(message.status, OutboxStatus.SENT)
        self.assertTrue(message.sensitive)
        self.assertIsNone(message.body_html)
        self.assertIsNone(message.body_text)
        self.assertIsNotNone(message.body_purged_at)
        self.assertEqual(message.subject, 'Baobab password reset')

    def test_send_now_failure_leaves_message_for_worker(self):
        with patch('app.outbox.sender.SmtpConnection.send', side_effect=RuntimeError('smtp down')):
            queue_email('password-reset', self.user, send_now=True, context={'reset': 'https://x.org/r'})
        message = self._messages()[0]
        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.attempts, 1)
        self.assertIsNotNone(message.body_html)

    def test_queue_emails_skips_unrenderable(self):
        nobody = self.add_user(email='nobody@example.org')
        nobody.email = ''
        queued, failed = queue_emails('withdrawal', [(self.user, {}), (nobody, {})], event=self.event)
        self.assertEqual(queued, 1)
        self.assertEqual(len(failed), 1)

    def test_worker_delivers_reply_to_and_attachments(self):
        queue_email('withdrawal', self.user, event=self.event)
        db.session.commit()
        db.session.query(OutboxMessage).update({'scheduled_at': datetime.utcnow() - timedelta(seconds=1)})
        db.session.commit()
        with patch('app.outbox.sender.SmtpConnection.send') as send:
            deliver_pending()
        self.assertEqual(send.call_args.kwargs['reply_to'], 'abx@indaba.deeplearning')
        self.assertEqual(send.call_args.kwargs['attachments'], [])

    def test_retention_purge(self):
        queue_email('withdrawal', self.user, event=self.event)
        db.session.commit()
        message = self._messages()[0]
        message.status = OutboxStatus.SENT
        message.created_at = datetime.utcnow() - timedelta(days=400)
        db.session.commit()
        self.assertEqual(OutboxRepository.purge_bodies_older_than(datetime.utcnow() - timedelta(days=365)), 1)
        db.session.commit()
        message = self._messages()[0]
        self.assertIsNone(message.body_html)
        self.assertEqual(message.subject, 'Withdrawal of application for Indaba 2026')

    def test_sample_context_overrides(self):
        values = sample_context(EMAIL_TYPES['offer'], None, None, 'en',
                                {'offer.payment_required': False, 'offer.grants': 0})
        self.assertFalse(values['offer']['payment_required'])
        self.assertEqual(values['offer']['grants'], [])
