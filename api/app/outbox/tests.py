import json
from datetime import datetime, timedelta
from unittest.mock import patch

from app import db
from app.outbox.models import MAX_ATTEMPTS, OutboxChannel, OutboxMessage, OutboxStatus
from app.outbox.repository import OutboxRepository
from app.outbox.sender import deliver_pending
from app.utils.emailer import resolve_sender
from app.utils.testing import ApiTestCase


CRON_HEADER = {'X-Appengine-Cron': 'true'}


class OutboxTestCase(ApiTestCase):

    def setUp(self):
        super().setUp()
        event = self.add_event(key='OUTBOX2025')
        self.event_id = event.id
        self.user_id = self.add_user('recipient@test.com').id

    def _message(self, channel=OutboxChannel.EMAIL, source_id=1, status=OutboxStatus.PENDING,
                 scheduled_at=None, user_id=None, **kwargs):
        message = OutboxMessage(
            organisation_id=self.dummy_org_id,
            event_id=self.event_id,
            user_id=self.user_id if user_id is None else user_id,
            channel=channel,
            recipient=kwargs.pop('recipient', 'recipient@test.com'),
            subject=kwargs.pop('subject', 'Subject'),
            body_text=kwargs.pop('body_text', 'Body'),
            body_html=kwargs.pop('body_html', '<p>Body</p>'),
            sender_name='My Org',
            sender_email='contact@org.com',
            status=status,
            attempts=0,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at or datetime.utcnow(),
            source_type='test',
            source_id=source_id,
            **kwargs
        )
        db.session.add(message)
        db.session.commit()
        return message


class OutboxClaimTest(OutboxTestCase):

    def test_claim_batch_takes_ownership_of_due_messages(self):
        self._message(source_id=1)
        self._message(source_id=2)

        claimed = OutboxRepository.claim_batch(10)

        self.assertEqual(len(claimed), 2)
        for message in claimed:
            self.assertEqual(message.status, OutboxStatus.SENDING)
            self.assertIsNotNone(message.claim_token)
            self.assertIsNotNone(message.claimed_at)

    def test_claim_batch_ignores_messages_not_yet_due(self):
        self._message(source_id=1, scheduled_at=datetime.utcnow() + timedelta(hours=1))

        self.assertEqual(OutboxRepository.claim_batch(10), [])

    def test_claim_batch_respects_limit(self):
        for i in range(5):
            self._message(source_id=i)

        self.assertEqual(len(OutboxRepository.claim_batch(2)), 2)

    def test_a_claimed_message_is_not_claimed_again(self):
        """A second worker running concurrently must not pick up claimed work."""
        self._message(source_id=1)

        first = OutboxRepository.claim_batch(10)
        second = OutboxRepository.claim_batch(10)

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    def test_release_returns_messages_without_charging_an_attempt(self):
        self._message(source_id=1)
        claimed = OutboxRepository.claim_batch(10)

        OutboxRepository.release(claimed)
        db.session.commit()

        message = db.session.query(OutboxMessage).one()
        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.attempts, 0)
        self.assertIsNone(message.claim_token)

    def test_requeue_stale_recovers_abandoned_messages(self):
        message = self._message(source_id=1, status=OutboxStatus.SENDING)
        message.claimed_at = datetime.utcnow() - timedelta(hours=1)
        message.claim_token = 'abandoned'
        db.session.commit()

        recovered = OutboxRepository.requeue_stale()

        self.assertEqual(recovered, 1)
        message = db.session.query(OutboxMessage).one()
        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.attempts, 1)

    def test_requeue_stale_leaves_recently_claimed_messages_alone(self):
        message = self._message(source_id=1, status=OutboxStatus.SENDING)
        message.claimed_at = datetime.utcnow()
        db.session.commit()

        self.assertEqual(OutboxRepository.requeue_stale(), 0)


class OutboxRetryTest(OutboxTestCase):

    def test_failure_schedules_a_retry(self):
        message = self._message(source_id=1)

        OutboxRepository.mark_failed(message, 'SMTP said no')
        db.session.commit()

        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.attempts, 1)
        self.assertEqual(message.last_error, 'SMTP said no')
        self.assertGreater(message.scheduled_at, datetime.utcnow())

    def test_retry_terminal_refuses_to_retry_sent_messages(self):
        """Guards the resend path: retrying a delivered message is a duplicate."""
        with self.assertRaises(ValueError):
            OutboxRepository.retry_terminal(
                'test', 1, statuses=(OutboxStatus.FAILED, OutboxStatus.SENT))

    def test_retry_terminal_resets_failed_messages(self):
        failed = self._message(source_id=1, status=OutboxStatus.FAILED)
        failed.attempts = MAX_ATTEMPTS
        failed.last_error = 'boom'
        sent = self._message(source_id=1, channel=OutboxChannel.PUSH, status=OutboxStatus.SENT)
        db.session.commit()

        retried = OutboxRepository.retry_terminal('test', 1, statuses=(OutboxStatus.FAILED,))
        db.session.commit()

        self.assertEqual(retried, 1)
        db.session.refresh(failed)
        db.session.refresh(sent)
        self.assertEqual(failed.status, OutboxStatus.PENDING)
        self.assertEqual(failed.attempts, 0)
        self.assertIsNone(failed.last_error)
        self.assertEqual(sent.status, OutboxStatus.SENT)

    def test_message_is_abandoned_after_max_attempts(self):
        message = self._message(source_id=1)

        for _ in range(MAX_ATTEMPTS):
            OutboxRepository.mark_failed(message, 'nope')
        db.session.commit()

        self.assertEqual(message.status, OutboxStatus.FAILED)
        self.assertEqual(message.attempts, MAX_ATTEMPTS)


class OutboxEnqueueTest(OutboxTestCase):

    def _mapping(self, channel=OutboxChannel.EMAIL, user_id=None):
        return {
            'organisation_id': self.dummy_org_id,
            'event_id': self.event_id,
            'user_id': self.user_id if user_id is None else user_id,
            'channel': channel,
            'recipient': 'recipient@test.com',
            'subject': 'Subject',
            'status': OutboxStatus.PENDING,
            'attempts': 0,
            'created_at': datetime.utcnow(),
            'scheduled_at': datetime.utcnow(),
            'source_type': 'test',
            'source_id': 99,
        }

    def test_enqueue_many_inserts_messages(self):
        queued = OutboxRepository.enqueue_many(
            [self._mapping(), self._mapping(channel=OutboxChannel.PUSH)], 'test', 99)
        db.session.commit()

        self.assertEqual(queued, 2)
        self.assertEqual(db.session.query(OutboxMessage).count(), 2)

    def test_enqueue_many_does_not_duplicate_an_already_queued_source(self):
        OutboxRepository.enqueue_many([self._mapping()], 'test', 99)
        db.session.commit()

        queued = OutboxRepository.enqueue_many([self._mapping()], 'test', 99)
        db.session.commit()

        self.assertEqual(queued, 0)
        self.assertEqual(db.session.query(OutboxMessage).count(), 1)

    def test_status_counts_groups_by_source_channel_and_status(self):
        self._message(source_id=1, channel=OutboxChannel.EMAIL)
        self._message(source_id=1, channel=OutboxChannel.PUSH)
        self._message(source_id=2, channel=OutboxChannel.EMAIL, status=OutboxStatus.SENT)

        counts = OutboxRepository.status_counts('test', [1, 2])

        self.assertEqual(counts[1][OutboxChannel.EMAIL][OutboxStatus.PENDING], 1)
        self.assertEqual(counts[1][OutboxChannel.PUSH][OutboxStatus.PENDING], 1)
        self.assertEqual(counts[2][OutboxChannel.EMAIL][OutboxStatus.SENT], 1)


@patch('app.utils.emailer.DEBUG', False)
@patch('app.utils.emailer.smtplib.SMTP')
class OutboxEmailDeliveryTest(OutboxTestCase):

    def test_a_batch_shares_one_smtp_connection(self, mock_smtp):
        """The whole point of the batching: connection setup dominates cost."""
        for i in range(10):
            self._message(source_id=i)

        summary = deliver_pending()

        self.assertEqual(summary['sent'], 10)
        self.assertEqual(mock_smtp.call_count, 1)
        self.assertEqual(mock_smtp.return_value.login.call_count, 1)
        self.assertEqual(mock_smtp.return_value.sendmail.call_count, 10)

    def test_delivered_messages_are_marked_sent(self, mock_smtp):
        self._message(source_id=1)

        deliver_pending()

        message = db.session.query(OutboxMessage).one()
        self.assertEqual(message.status, OutboxStatus.SENT)
        self.assertEqual(message.attempts, 1)
        self.assertIsNotNone(message.sent_at)

    def test_the_sender_comes_from_the_message_not_the_request(self, mock_smtp):
        """The worker has no organisation in scope, so the row must carry one."""
        self._message(source_id=1)

        deliver_pending()

        from_address = mock_smtp.return_value.sendmail.call_args[0][0]
        self.assertEqual(from_address, 'contact@org.com')

    def test_one_bad_recipient_does_not_abort_the_batch(self, mock_smtp):
        for i in range(3):
            self._message(source_id=i)
        mock_smtp.return_value.sendmail.side_effect = [Exception('rejected'), None, None]

        summary = deliver_pending()

        self.assertEqual(summary['sent'], 2)
        self.assertEqual(summary['failed'], 1)

    def test_time_budget_releases_undelivered_messages(self, mock_smtp):
        for i in range(5):
            self._message(source_id=i)

        summary = deliver_pending(time_budget_seconds=-1)

        self.assertEqual(summary['claimed'], 5)
        self.assertEqual(summary['released'], 5)
        self.assertEqual(summary['sent'], 0)
        pending = (db.session.query(OutboxMessage)
                   .filter(OutboxMessage.status == OutboxStatus.PENDING).count())
        self.assertEqual(pending, 5)


class SenderResolutionTest(ApiTestCase):
    """The worker has no organisation in scope, so a queued row must always carry a
    usable sender — including for an organisation with no email_from set."""

    def test_explicit_sender_is_used_as_given(self):
        self.assertEqual(
            resolve_sender('Org', 'org@example.com'), ('Org', 'org@example.com'))

    @patch('app.utils.emailer.SMTP_SENDER_NAME', 'Fallback Name')
    @patch('app.utils.emailer.SMTP_SENDER_EMAIL', 'fallback@example.com')
    def test_falls_back_to_configured_sender_when_organisation_has_no_email_from(self):
        name, address = resolve_sender('My Org', '')

        self.assertEqual(name, 'My Org')
        self.assertEqual(address, 'fallback@example.com')

    @patch('app.utils.emailer.SMTP_SENDER_NAME', 'Fallback Name')
    @patch('app.utils.emailer.SMTP_SENDER_EMAIL', 'fallback@example.com')
    def test_falls_back_entirely_when_nothing_is_in_scope(self):
        self.assertEqual(resolve_sender(None, None), ('Fallback Name', 'fallback@example.com'))

    @patch('app.utils.emailer.SMTP_SENDER_EMAIL', '')
    def test_raises_a_clear_error_when_no_sender_can_be_found(self):
        with self.assertRaises(ValueError) as raised:
            resolve_sender('My Org', '')

        self.assertIn('no sender address', str(raised.exception))


class OutboxPushDeliveryTest(OutboxTestCase):

    def test_push_is_sent_to_subscribed_users(self):
        self._message(channel=OutboxChannel.PUSH, recipient=None,
                      payload={'title': 'Hi', 'body': 'There'})

        with patch('app.utils.push.push_to_user',
                   return_value={'subscriptions': 1, 'sent': 1, 'failed': 0, 'errors': []}) as mock_push:
            with patch('app.outbox.sender.push_to_user', mock_push):
                summary = deliver_pending()

        self.assertEqual(summary['sent'], 1)
        self.assertEqual(db.session.query(OutboxMessage).one().status, OutboxStatus.SENT)

    def test_push_to_a_user_with_no_subscriptions_is_skipped_not_retried(self):
        """Nothing to deliver to isn't a failure, and retrying won't help."""
        self._message(channel=OutboxChannel.PUSH, recipient=None, payload={'title': 'Hi'})

        summary = deliver_pending()

        self.assertEqual(summary['skipped'], 1)
        message = db.session.query(OutboxMessage).one()
        self.assertEqual(message.status, OutboxStatus.SKIPPED)

    def test_push_failure_is_retried(self):
        self._message(channel=OutboxChannel.PUSH, recipient=None, payload={'title': 'Hi'})

        with patch('app.outbox.sender.push_to_user',
                   return_value={'subscriptions': 2, 'sent': 0, 'failed': 2,
                                 'errors': ['gone']}):
            summary = deliver_pending()

        self.assertEqual(summary['failed'], 1)
        message = db.session.query(OutboxMessage).one()
        self.assertEqual(message.status, OutboxStatus.PENDING)
        self.assertEqual(message.attempts, 1)

    def test_a_push_only_batch_never_opens_an_smtp_connection(self):
        self._message(channel=OutboxChannel.PUSH, recipient=None, payload={'title': 'Hi'})

        with patch('app.utils.emailer.smtplib.SMTP') as mock_smtp:
            deliver_pending()

        mock_smtp.assert_not_called()


class OutboxWorkerApiTest(OutboxTestCase):

    def test_worker_rejects_requests_without_the_cron_header(self):
        response = self.app.post('/api/v1/tasks/outbox')

        self.assertEqual(response.status_code, 403)

    def test_worker_rejects_a_forged_cron_header_value(self):
        response = self.app.post('/api/v1/tasks/outbox',
                                 headers={'X-Appengine-Cron': 'yes-please'})

        self.assertEqual(response.status_code, 403)

    def test_worker_delivers_the_queue(self):
        self._message(source_id=1)

        response = self.app.post('/api/v1/tasks/outbox', headers=CRON_HEADER)

        self.assertEqual(response.status_code, 200)
        summary = json.loads(response.data)
        self.assertEqual(summary['claimed'], 1)
        self.assertEqual(summary['sent'], 1)

    def test_worker_needs_no_organisation_on_the_request(self):
        """Cron sends no Origin or Referer; resolving one would 400 the request."""
        response = self.app.post('/api/v1/tasks/outbox', headers=CRON_HEADER,
                                 environ_overrides={'HTTP_ORIGIN': '', 'HTTP_REFERER': ''})

        self.assertEqual(response.status_code, 200)
