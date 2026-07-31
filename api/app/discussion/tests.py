import json
import unittest
from unittest.mock import patch

from app import db
from app.discussion.models import (
    DiscussionThread, DiscussionMessage, DiscussionSubscription, DiscussionReport, DiscussionSpace,
    NO_SUBJECT_PLACEHOLDER)
from app.discussion.repository import DiscussionRepository
from app.invitedGuest.models import InvitedGuest
from app.utils.testing import ApiTestCase


def _invited_guest(event_id, user_id):
    ig = InvitedGuest(event_id=event_id, user_id=user_id, role='Guest')
    db.session.add(ig)
    db.session.commit()
    return ig


class DiscussionApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        event = self.add_event(key='DISC2026')
        self.event_id = event.id

        g1 = self.add_user('g1@test.com')
        self.g1_id = g1.id
        _invited_guest(self.event_id, self.g1_id)
        g2 = self.add_user('g2@test.com')
        self.g2_id = g2.id
        _invited_guest(self.event_id, self.g2_id)
        mod = self.add_user('mod@test.com')
        self.mod_id = mod.id
        _invited_guest(self.event_id, self.mod_id)
        self.add_event_role('comms-officer', self.mod_id, self.event_id)
        self.add_user('out@test.com')  # not a guest

        self.g1_header = self.get_auth_header_for('g1@test.com')
        self.g2_header = self.get_auth_header_for('g2@test.com')
        self.mod_header = self.get_auth_header_for('mod@test.com')
        self.out_header = self.get_auth_header_for('out@test.com')

        # Every post must live in a space; set up one default (auto-subscribing) space
        # used by the bulk of these tests, which predate spaces and don't care about them.
        self.space_id = self._create_space_id(subscribe_on_reply=True)

    def _create_space(self, header=None, name='General', description='', subscribe_on_reply=True):
        return self.app.post(
            '/api/v1/discussion/space',
            data=json.dumps({
                'event_id': self.event_id, 'name': name, 'description': description,
                'subscribe_on_reply': subscribe_on_reply,
            }),
            content_type='application/json', headers=(header or self.mod_header))

    def _create_space_id(self, **kwargs):
        return json.loads(self._create_space(**kwargs).data)['id']

    def _create_thread(self, header, subject='Hi', body='hello', space_id=None):
        return self.app.post(
            '/api/v1/discussion/thread',
            data=json.dumps({
                'event_id': self.event_id, 'space_id': (space_id or self.space_id),
                'subject': subject, 'body_markdown': body,
            }),
            content_type='application/json', headers=header)

    def _reply(self, header, thread_id, body='a reply'):
        return self.app.post(
            '/api/v1/discussion/thread/{}/reply'.format(thread_id),
            data=json.dumps({'event_id': self.event_id, 'body_markdown': body}),
            content_type='application/json', headers=header)

    # ---------- Access control ----------

    @patch('app.discussion.api.push_to_user')
    def test_non_guest_cannot_list_or_post(self, mock_push):
        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.out_header)
        self.assertEqual(resp.status_code, 403)

        resp = self._create_thread(self.out_header)
        self.assertEqual(resp.status_code, 403)

    def test_guest_can_list_empty_board(self):
        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data), [])

    # ---------- Threads & replies ----------

    def test_create_thread_creates_root_and_autosubscribes(self):
        resp = self._create_thread(self.g1_header, subject='Airport shuttle?', body='Anyone sharing?')
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)

        threads = db.session.query(DiscussionThread).all()
        self.assertEqual(len(threads), 1)
        messages = db.session.query(DiscussionMessage).all()
        self.assertEqual(len(messages), 1)
        self.assertIsNone(messages[0].parent_message_id)
        self.assertEqual(messages[0].id, data['message_id'])

        sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=data['thread_id'], user_id=self.g1_id).first()
        self.assertIsNotNone(sub)
        self.assertTrue(sub.subscribed)

    @patch('app.discussion.api.push_to_user')
    def test_reply_appends_message_bumps_activity_and_autosubscribes(self, mock_push):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        activity_before = db.session.query(DiscussionThread).get(thread_id).last_activity_at

        resp = self._reply(self.g2_header, thread_id)
        self.assertEqual(resp.status_code, 201)

        messages = db.session.query(DiscussionMessage).filter_by(thread_id=thread_id).all()
        self.assertEqual(len(messages), 2)

        activity_after = db.session.query(DiscussionThread).get(thread_id).last_activity_at
        self.assertGreaterEqual(activity_after, activity_before)

        sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g2_id).first()
        self.assertIsNotNone(sub)
        self.assertTrue(sub.subscribed)

    def test_thread_list_sorts_pinned_then_recent_activity(self):
        t1_id = json.loads(self._create_thread(self.g1_header, subject='First').data)['thread_id']
        t2_id = json.loads(self._create_thread(self.g1_header, subject='Second').data)['thread_id']

        # Pin the older thread — it should now sort first despite less-recent activity.
        t1 = db.session.query(DiscussionThread).get(t1_id)
        DiscussionRepository.set_pinned(t1, True)

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        ids = [t['id'] for t in json.loads(resp.data)]
        self.assertEqual(ids[0], t1_id)
        self.assertIn(t2_id, ids)

    @patch('app.discussion.api.push_to_user')
    def test_reply_count_excludes_root_and_deleted(self, mock_push):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        reply_resp = self._reply(self.g2_header, thread_id)
        reply_id = json.loads(reply_resp.data)['message_id']

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertEqual(thread_data['reply_count'], 1)

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(reply_id, self.event_id),
            headers=self.g2_header)

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertEqual(thread_data['reply_count'], 0)

    # ---------- Read / unread ----------

    def test_thread_unread_until_viewed(self):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g2_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertTrue(thread_data['unread'])

        self.app.get(
            '/api/v1/discussion/thread/{}?event_id={}'.format(thread_id, self.event_id),
            headers=self.g2_header)

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g2_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertFalse(thread_data['unread'])

    def test_creating_thread_marks_it_read_for_author(self):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertFalse(thread_data['unread'])

    @patch('app.discussion.api.push_to_user')
    def test_reply_marks_thread_read_for_replier_but_unread_for_others(self, mock_push):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        self.app.get(
            '/api/v1/discussion/thread/{}?event_id={}'.format(thread_id, self.event_id),
            headers=self.g2_header)  # g2 views before replying

        self._reply(self.g2_header, thread_id)

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g2_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertFalse(thread_data['unread'])

        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(self.event_id, self.space_id),
            headers=self.g1_header)
        thread_data = next(t for t in json.loads(resp.data) if t['id'] == thread_id)
        self.assertTrue(thread_data['unread'])

    # ---------- Subscriptions (sticky unsubscribe) ----------

    @patch('app.discussion.api.push_to_user')
    def test_explicit_unsubscribe_is_sticky(self, mock_push):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        self._reply(self.g2_header, thread_id)  # g2 auto-subscribes

        resp = self.app.post(
            '/api/v1/discussion/thread/{}/subscription'.format(thread_id),
            data=json.dumps({'event_id': self.event_id, 'subscribed': False}),
            content_type='application/json', headers=self.g2_header)
        self.assertEqual(resp.status_code, 200)

        # Someone else replies again — g2's sticky unsubscribe must not be overridden.
        self._reply(self.g1_header, thread_id)

        sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g2_id).first()
        self.assertFalse(sub.subscribed)

    def test_subscribe_toggle_endpoint(self):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']

        resp = self.app.post(
            '/api/v1/discussion/thread/{}/subscription'.format(thread_id),
            data=json.dumps({'event_id': self.event_id, 'subscribed': False}),
            content_type='application/json', headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.data)['subscribed'])

        sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g1_id).first()
        self.assertFalse(sub.subscribed)

    @patch('app.discussion.api.push_to_user')
    def test_my_subscriptions_lists_only_subscribed_threads(self, mock_push):
        t1_id = json.loads(self._create_thread(self.g1_header, subject='One').data)['thread_id']
        t2_id = json.loads(self._create_thread(self.g2_header, subject='Two').data)['thread_id']
        self._reply(self.g1_header, t2_id)  # g1 now subscribed to both

        resp = self.app.get(
            '/api/v1/discussion/subscription?event_id={}'.format(self.event_id),
            headers=self.g1_header)
        ids = {t['id'] for t in json.loads(resp.data)}
        self.assertEqual(ids, {t1_id, t2_id})

        resp = self.app.get(
            '/api/v1/discussion/subscription?event_id={}'.format(self.event_id),
            headers=self.g2_header)
        ids = {t['id'] for t in json.loads(resp.data)}
        self.assertEqual(ids, {t2_id})

    @patch('app.discussion.api.push_to_user')
    def test_my_subscriptions_spans_every_space(self, mock_push):
        other_space_id = self._create_space_id(name='Ideathon')
        t1_id = json.loads(self._create_thread(self.g1_header, subject='In default space').data)['thread_id']
        t2_id = json.loads(self._create_thread(self.g1_header, subject='In Ideathon', space_id=other_space_id).data)['thread_id']

        resp = self.app.get(
            '/api/v1/discussion/subscription?event_id={}'.format(self.event_id),
            headers=self.g1_header)
        ids = {t['id'] for t in json.loads(resp.data)}
        self.assertEqual(ids, {t1_id, t2_id})

    # ---------- Notifications ----------

    @patch('app.discussion.api.push_to_user')
    def test_reply_notifies_other_subscribers_not_actor(self, mock_push):
        thread_id = json.loads(self._create_thread(self.g1_header).data)['thread_id']
        self._reply(self.g2_header, thread_id)
        mock_push.reset_mock()

        self._reply(self.g1_header, thread_id)

        notified_user_ids = {c.args[0] for c in mock_push.call_args_list}
        self.assertIn(self.g2_id, notified_user_ids)
        self.assertNotIn(self.g1_id, notified_user_ids)

    # ---------- Edit / delete ----------

    def test_author_can_edit_own_sets_edited_at(self):
        message_id = json.loads(self._create_thread(self.g1_header).data)['message_id']
        resp = self.app.put(
            '/api/v1/discussion/message/{}'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'body_markdown': 'edited body'}),
            content_type='application/json', headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(json.loads(resp.data)['edited_at'])

        msg = db.session.query(DiscussionMessage).get(message_id)
        self.assertEqual(msg.body_markdown, 'edited body')
        self.assertIsNotNone(msg.edited_at)

    def test_non_author_cannot_edit(self):
        message_id = json.loads(self._create_thread(self.g1_header).data)['message_id']
        resp = self.app.put(
            '/api/v1/discussion/message/{}'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'body_markdown': 'hijacked'}),
            content_type='application/json', headers=self.g2_header)
        self.assertEqual(resp.status_code, 403)

    def test_author_soft_delete_leaves_tombstone(self):
        thread_id, message_id = self._create_thread_ids(self.g1_header)
        resp = self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 204)

        msg = db.session.query(DiscussionMessage).get(message_id)
        self.assertTrue(msg.is_deleted)
        self.assertEqual(msg.deleted_by, 'author')

        resp = self.app.get(
            '/api/v1/discussion/thread/{}?event_id={}'.format(thread_id, self.event_id),
            headers=self.g1_header)
        root = json.loads(resp.data)['messages'][0]
        self.assertIsNone(root['body_markdown'])

    def test_moderator_can_delete_any_message(self):
        thread_id, message_id = self._create_thread_ids(self.g1_header)

        resp = self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g2_header)
        self.assertEqual(resp.status_code, 403)

        resp = self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.mod_header)
        self.assertEqual(resp.status_code, 204)

        msg = db.session.query(DiscussionMessage).get(message_id)
        self.assertEqual(msg.deleted_by, 'moderator')

    def test_delete_is_idempotent(self):
        thread_id, message_id = self._create_thread_ids(self.g1_header)
        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)
        resp = self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 204)

        tombstones = db.session.query(DiscussionMessage).filter_by(id=message_id, is_deleted=True).all()
        self.assertEqual(len(tombstones), 1)

    # ---------- Reporting & moderation ----------

    def test_report_creates_row_and_is_idempotent_per_reporter(self):
        _, message_id = self._create_thread_ids(self.g1_header)

        resp = self.app.post(
            '/api/v1/discussion/message/{}/report'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'reason': 'spam'}),
            content_type='application/json', headers=self.g2_header)
        self.assertEqual(resp.status_code, 201)

        resp = self.app.post(
            '/api/v1/discussion/message/{}/report'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'reason': 'spam again'}),
            content_type='application/json', headers=self.g2_header)
        self.assertEqual(resp.status_code, 200)

        reports = db.session.query(DiscussionReport).filter_by(message_id=message_id).all()
        self.assertEqual(len(reports), 1)

    def test_moderator_sees_open_reports_others_dont(self):
        _, message_id = self._create_thread_ids(self.g1_header)
        self.app.post(
            '/api/v1/discussion/message/{}/report'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'reason': 'spam'}),
            content_type='application/json', headers=self.g2_header)

        resp = self.app.get(
            '/api/v1/discussion/report?event_id={}'.format(self.event_id),
            headers=self.g2_header)
        self.assertEqual(resp.status_code, 403)

        resp = self.app.get(
            '/api/v1/discussion/report?event_id={}'.format(self.event_id),
            headers=self.mod_header)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(json.loads(resp.data)), 1)

    def test_dismiss_report_sets_status_dismissed(self):
        _, message_id = self._create_thread_ids(self.g1_header)
        report_resp = self.app.post(
            '/api/v1/discussion/message/{}/report'.format(message_id),
            data=json.dumps({'event_id': self.event_id, 'reason': 'spam'}),
            content_type='application/json', headers=self.g2_header)
        report_id = json.loads(report_resp.data)['id']

        resp = self.app.post(
            '/api/v1/discussion/report/{}/dismiss'.format(report_id),
            data=json.dumps({'event_id': self.event_id}),
            content_type='application/json', headers=self.mod_header)
        self.assertEqual(resp.status_code, 200)

        report = db.session.query(DiscussionReport).get(report_id)
        self.assertEqual(report.status, 'dismissed')

    # ---------- Rate limiting ----------

    def test_rate_limit_blocks_after_threshold(self):
        with patch('app.discussion.api.RATE_LIMIT_COUNT', 2):
            self._create_thread(self.g1_header, subject='1')
            self._create_thread(self.g1_header, subject='2')
            resp = self._create_thread(self.g1_header, subject='3')
            self.assertEqual(resp.status_code, 429)

    # ---------- Spaces: access control ----------

    def test_guest_cannot_create_edit_or_delete_space(self):
        resp = self._create_space(header=self.g1_header)
        self.assertEqual(resp.status_code, 403)

        resp = self.app.put(
            '/api/v1/discussion/space/{}'.format(self.space_id),
            data=json.dumps({'event_id': self.event_id, 'name': 'Hijacked'}),
            content_type='application/json', headers=self.g1_header)
        self.assertEqual(resp.status_code, 403)

        resp = self.app.delete(
            '/api/v1/discussion/space/{}?event_id={}'.format(self.space_id, self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 403)

    def test_guest_can_list_spaces(self):
        resp = self.app.get(
            '/api/v1/discussion/space?event_id={}'.format(self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)
        ids = [s['id'] for s in json.loads(resp.data)]
        self.assertIn(self.space_id, ids)

    def test_get_space_detail(self):
        resp = self.app.get(
            '/api/v1/discussion/space/{}?event_id={}'.format(self.space_id, self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data)['id'], self.space_id)

        resp = self.app.get(
            '/api/v1/discussion/space/{}?event_id={}'.format(self.space_id, self.event_id),
            headers=self.out_header)
        self.assertEqual(resp.status_code, 403)

    def test_comms_officer_can_create_and_edit_space(self):
        resp = self._create_space(name='Introductions', description='Say hi!', subscribe_on_reply=False)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data['name'], 'Introductions')
        self.assertFalse(data['subscribe_on_reply'])

        resp = self.app.put(
            '/api/v1/discussion/space/{}'.format(data['id']),
            data=json.dumps({'event_id': self.event_id, 'name': 'Intros', 'subscribe_on_reply': True}),
            content_type='application/json', headers=self.mod_header)
        self.assertEqual(resp.status_code, 200)
        updated = json.loads(resp.data)
        self.assertEqual(updated['name'], 'Intros')
        self.assertTrue(updated['subscribe_on_reply'])

    # ---------- Spaces: posts must live in a space ----------

    def test_thread_requires_valid_space(self):
        resp = self.app.post(
            '/api/v1/discussion/thread',
            data=json.dumps({'event_id': self.event_id, 'body_markdown': 'hello'}),
            content_type='application/json', headers=self.g1_header)
        self.assertEqual(resp.status_code, 400)

        resp = self._create_thread(self.g1_header, space_id=999999)
        self.assertEqual(resp.status_code, 404)

    def test_thread_rejects_space_from_another_event(self):
        other_event = self.add_event(key='DISC2027')
        _invited_guest(other_event.id, self.g1_id)
        self.add_event_role('comms-officer', self.mod_id, other_event.id)
        other_space_id = json.loads(self.app.post(
            '/api/v1/discussion/space',
            data=json.dumps({'event_id': other_event.id, 'name': 'Other'}),
            content_type='application/json', headers=self.mod_header).data)['id']

        resp = self._create_thread(self.g1_header, space_id=other_space_id)
        self.assertEqual(resp.status_code, 404)

    def test_cannot_post_new_thread_in_archived_space(self):
        space_id = self._create_space_id(name='Retiring')
        self._create_thread(self.g1_header, space_id=space_id)  # give it a thread so delete archives it
        self.app.delete(
            '/api/v1/discussion/space/{}?event_id={}'.format(space_id, self.event_id),
            headers=self.mod_header)

        resp = self._create_thread(self.g1_header, space_id=space_id)
        self.assertEqual(resp.status_code, 404)

    # ---------- Subject required ----------

    def test_thread_requires_subject(self):
        resp = self._create_thread(self.g1_header, subject='')
        self.assertEqual(resp.status_code, 400)

        resp = self._create_thread(self.g1_header, subject='   ')
        self.assertEqual(resp.status_code, 400)

    # ---------- Emptied-out threads are hidden from the board ----------

    def _create_legacy_no_subject_thread(self, user_id, space_id=None):
        """Simulate a thread created before subjects were required."""
        thread, root = DiscussionRepository.create_thread(
            self.event_id, (space_id or self.space_id), user_id, NO_SUBJECT_PLACEHOLDER, 'hello')
        return thread.id, root.id

    def _board_ids(self, header, space_id=None):
        resp = self.app.get(
            '/api/v1/discussion/thread?event_id={}&space_id={}'.format(
                self.event_id, (space_id or self.space_id)),
            headers=header)
        return [t['id'] for t in json.loads(resp.data)]

    def test_emptied_out_thread_hidden_after_author_deletes_root(self):
        thread_id, message_id = self._create_legacy_no_subject_thread(self.g1_id)
        self.assertIn(thread_id, self._board_ids(self.g1_header))

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)

        self.assertNotIn(thread_id, self._board_ids(self.g1_header))

    def test_emptied_out_thread_hidden_after_moderator_deletes_root(self):
        thread_id, message_id = self._create_legacy_no_subject_thread(self.g1_id)

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.mod_header)

        self.assertNotIn(thread_id, self._board_ids(self.g1_header))

    def test_thread_with_subject_stays_visible_after_root_deleted(self):
        thread_id, message_id = self._create_thread_ids(self.g1_header)  # created with subject='Hi'

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)

        self.assertIn(thread_id, self._board_ids(self.g1_header))

    @patch('app.discussion.api.push_to_user')
    def test_emptied_out_thread_stays_visible_if_reply_remains(self, mock_push):
        thread_id, message_id = self._create_legacy_no_subject_thread(self.g1_id)
        self._reply(self.g2_header, thread_id)

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)

        self.assertIn(thread_id, self._board_ids(self.g1_header))

    @patch('app.discussion.api.push_to_user')
    def test_emptied_out_thread_hidden_once_last_reply_also_deleted(self, mock_push):
        thread_id, message_id = self._create_legacy_no_subject_thread(self.g1_id)
        reply_resp = self._reply(self.g2_header, thread_id)
        reply_id = json.loads(reply_resp.data)['message_id']

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(message_id, self.event_id),
            headers=self.g1_header)
        self.assertIn(thread_id, self._board_ids(self.g1_header))  # reply still present

        self.app.delete(
            '/api/v1/discussion/message/{}?event_id={}'.format(reply_id, self.event_id),
            headers=self.g2_header)
        self.assertNotIn(thread_id, self._board_ids(self.g1_header))

    # ---------- Spaces: archive vs hard-delete ----------

    def test_deleting_empty_space_hard_deletes(self):
        space_id = self._create_space_id(name='Empty space')
        resp = self.app.delete(
            '/api/v1/discussion/space/{}?event_id={}'.format(space_id, self.event_id),
            headers=self.mod_header)
        self.assertEqual(resp.status_code, 204)
        self.assertIsNone(db.session.query(DiscussionSpace).get(space_id))

    def test_deleting_nonempty_space_archives_and_keeps_threads_reachable(self):
        space_id = self._create_space_id(name='Has posts')
        thread_id, _ = self._create_thread_ids(self.g1_header, space_id=space_id)

        resp = self.app.delete(
            '/api/v1/discussion/space/{}?event_id={}'.format(space_id, self.event_id),
            headers=self.mod_header)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.data)['is_archived'])

        space = db.session.query(DiscussionSpace).get(space_id)
        self.assertIsNotNone(space)
        self.assertTrue(space.is_archived)

        # Archived space drops off the guest-facing list...
        resp = self.app.get(
            '/api/v1/discussion/space?event_id={}'.format(self.event_id),
            headers=self.g1_header)
        self.assertNotIn(space_id, [s['id'] for s in json.loads(resp.data)])

        # ...but its existing thread is still reachable.
        resp = self.app.get(
            '/api/v1/discussion/thread/{}?event_id={}'.format(thread_id, self.event_id),
            headers=self.g1_header)
        self.assertEqual(resp.status_code, 200)

    # ---------- Spaces: subscribe_on_reply default ----------

    @patch('app.discussion.api.push_to_user')
    def test_subscribe_on_reply_false_does_not_autosubscribe_on_post_or_reply(self, mock_push):
        space_id = self._create_space_id(name='Introductions', subscribe_on_reply=False)

        thread_id, _ = self._create_thread_ids(self.g1_header, space_id=space_id)
        author_sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g1_id).first()
        self.assertIsNone(author_sub)

        self._reply(self.g2_header, thread_id)
        replier_sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g2_id).first()
        self.assertIsNone(replier_sub)

        # Manual opt-in still works even though the space default is off.
        resp = self.app.post(
            '/api/v1/discussion/thread/{}/subscription'.format(thread_id),
            data=json.dumps({'event_id': self.event_id, 'subscribed': True}),
            content_type='application/json', headers=self.g2_header)
        self.assertEqual(resp.status_code, 200)
        replier_sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g2_id).first()
        self.assertTrue(replier_sub.subscribed)

    @patch('app.discussion.api.push_to_user')
    def test_subscribe_on_reply_true_autosubscribes_on_post_and_reply(self, mock_push):
        space_id = self._create_space_id(name='Ideathon', subscribe_on_reply=True)

        thread_id, _ = self._create_thread_ids(self.g1_header, space_id=space_id)
        author_sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g1_id).first()
        self.assertTrue(author_sub.subscribed)

        self._reply(self.g2_header, thread_id)
        replier_sub = db.session.query(DiscussionSubscription).filter_by(
            thread_id=thread_id, user_id=self.g2_id).first()
        self.assertTrue(replier_sub.subscribed)

    def test_space_thread_count_and_unread(self):
        space_id = self._create_space_id(name='Counted')
        self._create_thread(self.g1_header, space_id=space_id)
        self._create_thread(self.g1_header, space_id=space_id)

        resp = self.app.get(
            '/api/v1/discussion/space?event_id={}'.format(self.event_id),
            headers=self.g1_header)
        space_data = next(s for s in json.loads(resp.data) if s['id'] == space_id)
        self.assertEqual(space_data['thread_count'], 2)
        self.assertFalse(space_data['has_unread'])  # g1 authored both, so already read

        resp = self.app.get(
            '/api/v1/discussion/space?event_id={}'.format(self.event_id),
            headers=self.g2_header)
        space_data = next(s for s in json.loads(resp.data) if s['id'] == space_id)
        self.assertTrue(space_data['has_unread'])  # g2 has never viewed either thread

    # ---------- helpers ----------

    def _create_thread_ids(self, header, space_id=None):
        data = json.loads(self._create_thread(header, space_id=space_id).data)
        return data['thread_id'], data['message_id']


if __name__ == '__main__':
    unittest.main()
