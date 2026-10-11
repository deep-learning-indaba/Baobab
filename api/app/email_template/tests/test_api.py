import json
from datetime import datetime
from unittest.mock import patch

from app import db
from app.email_template.models import EmailTemplate, EmailTemplateRevision
from app.email_template.service import queue_email
from app.outbox.models import OutboxMessage, OutboxStatus
from app.utils.testing import ApiTestCase


class EmailTemplateApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.event_id = self.add_event(name={'en': 'Indaba', 'fr': 'Indaba FR'},
                                       description={'en': 'd', 'fr': 'd'}, languages=['en', 'fr']).id
        self.other_event_id = self.add_event(key='OTHER').id
        self.admin_id = self.add_user('eventadmin@example.org').id
        self.add_event_role('admin', self.admin_id, self.event_id)
        self.system_admin_id = self.add_user('sysadmin@example.org', is_admin=True).id
        self.user_id = self.add_user('someone@example.org').id
        self.admin = self.get_auth_header_for('eventadmin@example.org')

    def _url(self, path, event_id=None):
        return '/api/v1/events/{}/{}'.format(event_id or self.event_id, path)

    def _json(self, method, url, headers=None, body=None):
        response = getattr(self.app, method)(url, headers=headers or self.admin, data=json.dumps(body or {}),
                                             content_type='application/json')
        return response.status_code, json.loads(response.data)

    # ------------------------------------------------------------------ listing

    def test_lists_event_types_with_status_per_language(self):
        status, body = self._json('get', self._url('email-types'))
        self.assertEqual(status, 200)
        keys = {t['key'] for t in body}
        self.assertIn('offer', keys)
        self.assertNotIn('password-reset', keys)
        offer = next(t for t in body if t['key'] == 'offer')
        self.assertEqual(offer['languages']['en']['source'], 'default')
        self.assertEqual(set(offer['languages']), {'en', 'fr'})

    def test_type_schema_describes_fields(self):
        status, body = self._json('get', self._url('email-types/offer?ui_language=fr'))
        self.assertEqual(status, 200)
        offer = body['context']['offer']
        self.assertEqual(offer['fields']['grants']['type'], 'list')
        self.assertIn('name', offer['fields']['grants']['item']['fields'])
        self.assertEqual(offer['fields']['expiry_date']['type'], 'date')
        self.assertTrue(body['context']['recipient']['implicit'])
        self.assertIn('offre', offer['fields']['url']['description'])
        self.assertEqual(body['name'], "Offre d'une place")

    def test_requires_event_admin(self):
        other = self.get_auth_header_for('someone@example.org')
        self.assertEqual(self._json('get', self._url('email-types'), other)[0], 403)
        self.assertEqual(self._json('get', self._url('email-types', self.other_event_id))[0], 403)

    def test_event_admin_cannot_edit_organisation_types(self):
        status, _ = self._json('put', self._url('email-templates/password-reset'),
                               body={'subject': 'x', 'body': 'phish'})
        self.assertEqual(status, 404)
        status, _ = self._json('put', '/api/v1/organisation/email-templates/password-reset',
                               body={'subject': 'x', 'body': 'phish'})
        self.assertEqual(status, 403)

    # ------------------------------------------------------------------ editing

    def test_save_reset_and_revisions(self):
        status, body = self._json('put', self._url('email-templates/offer?language=en'),
                                  body={'subject': 'Offer for {{ event.name }}',
                                        'body': 'Hi {{ recipient.firstname }} {% button "Go", offer.url %}'})
        self.assertEqual(status, 200, body)
        self.assertEqual(body['override']['subject'], 'Offer for {{ event.name }}')
        self.assertEqual(body['inherited']['source'], 'default')

        self._json('put', self._url('email-templates/offer?language=en'),
                   body={'subject': 'Second', 'body': 'Body'})
        status, revisions = self._json('get', self._url('email-templates/offer/revisions?language=en'))
        self.assertEqual([r['subject'] for r in revisions], ['Second', 'Offer for {{ event.name }}'])

        status, body = self._json('delete', self._url('email-templates/offer?language=en'))
        self.assertEqual(status, 200)
        self.assertIsNone(body['override'])
        self.assertEqual(db.session.query(EmailTemplate).count(), 0)
        self.assertEqual(db.session.query(EmailTemplateRevision).count(), 2)

    def test_save_rejects_unknown_field_with_position(self):
        status, body = self._json('put', self._url('email-templates/offer?language=en'),
                                  body={'subject': 'S', 'body': 'Hi\n{{ offer.expiry_dat }}'})
        self.assertEqual(status, 400)
        self.assertEqual(body['error']['line'], 2)
        self.assertEqual(body['error']['field'], 'body')
        self.assertEqual(db.session.query(EmailTemplate).count(), 0)

    def test_save_rejects_syntax_error_and_unsafe_link(self):
        for source in ('{% if offer.payment_required %}', '{% button "x", "javascript:alert(1)" %}'):
            status, _ = self._json('put', self._url('email-templates/offer?language=en'),
                                   body={'subject': 'S', 'body': source})
            self.assertEqual(status, 400, source)

    def test_save_rejects_language_the_event_does_not_use(self):
        status, _ = self._json('put', self._url('email-templates/offer?language=pt'),
                               body={'subject': 'S', 'body': 'B'})
        self.assertEqual(status, 400)

    def test_organisation_level_override_is_inherited_by_event(self):
        sysadmin = self.get_auth_header_for('sysadmin@example.org')
        status, body = self._json('put', '/api/v1/organisation/email-templates/offer?language=en', sysadmin,
                                  {'subject': 'Org subject', 'body': 'Org body'})
        self.assertEqual(status, 200, body)
        status, body = self._json('get', self._url('email-templates/offer?language=en'))
        self.assertEqual(body['inherited']['source'], 'organisation')
        self.assertEqual(body['inherited']['subject'], 'Org subject')

    # ------------------------------------------------------------------ preview / test send

    def test_preview_with_sample_overrides(self):
        status, body = self._json('post', self._url('email-templates/offer/preview'), body={
            'language': 'en', 'subject': '{{ event.name }}',
            'body': '{% if offer.payment_required %}Pay{% else %}Free{% endif %} {% button "Go", offer.url %}',
            'sample_overrides': {'offer.payment_required': False}})
        self.assertEqual(status, 200, body)
        self.assertEqual(body['subject'], 'Indaba')
        self.assertIn('Free', body['text'])
        self.assertIn('<table role="presentation"', body['html'])
        self.assertIn('<!DOCTYPE html>', body['html'])

    def test_preview_as_real_offer(self):
        offer_id = self.add_offer(self.user_id, self.event_id, expiry_date=datetime(2026, 6, 5)).id
        status, body = self._json('post', self._url('email-templates/offer/preview'), body={
            'language': 'en', 'subject': 's', 'body': '{{ recipient.email }} {{ offer.expiry_date }}',
            'offer_id': offer_id})
        self.assertEqual(status, 200, body)
        self.assertEqual(body['text'], 'someone@example.org 5 June 2026')

    def test_preview_cannot_read_another_events_offer(self):
        offer_id = self.add_offer(self.user_id, self.other_event_id).id
        status, _ = self._json('post', self._url('email-templates/offer/preview'), body={
            'language': 'en', 'subject': 's', 'body': 'b', 'offer_id': offer_id})
        self.assertEqual(status, 404)

    def test_test_send_goes_only_to_the_admin(self):
        with patch('app.outbox.sender.SmtpConnection.send') as send:
            status, body = self._json('post', self._url('email-templates/offer/test-send'), body={
                'language': 'en', 'subject': 'Hello', 'body': 'Hi {{ recipient.firstname }}',
                'recipient': 'victim@example.org'})
        self.assertEqual(status, 201, body)
        self.assertEqual(body['sent_to'], 'eventadmin@example.org')
        self.assertEqual(send.call_args.kwargs['recipient'], 'eventadmin@example.org')
        self.assertEqual(send.call_args.kwargs['subject'], '[TEST] Hello')

    # ------------------------------------------------------------------ translation

    def test_template_reports_where_each_language_comes_from(self):
        self._json('put', self._url('email-templates/offer?language=en'), body={'subject': 'S', 'body': 'B'})
        _, body = self._json('get', self._url('email-templates/offer?language=fr'))
        self.assertEqual(body['language_sources'], {'en': 'event', 'fr': 'default'})

    def test_translate_from_another_language(self):
        self._json('put', self._url('email-templates/offer?language=en'), body={
            'subject': 'Hello {{ event.name }}', 'body': 'Dear {{ recipient.firstname }}\n{% button "Accept", offer.url %}'})
        upper = lambda texts, *a, **k: [t.replace('Hello', 'Bonjour').replace('Dear', 'Cher')
                                        .replace('Accept', 'Accepter') for t in texts]
        with patch('app.utils.translation.TranslationService.translate_many', side_effect=upper):
            status, body = self._json('post', self._url('email-templates/offer/translate?language=fr'),
                                      body={'source_language': 'en'})
        self.assertEqual(status, 200, body)
        self.assertEqual(body['subject'], 'Bonjour {{ event.name }}')
        self.assertEqual(body['body'], 'Cher {{ recipient.firstname }}\n{% button "Accepter", offer.url %}')
        self.assertEqual(body['untranslated_lines'], 0)
        # Nothing is saved: the editor shows it for review.
        self.assertEqual(db.session.query(EmailTemplate).filter_by(language='fr').count(), 0)

    def test_translate_rejects_same_or_unknown_language(self):
        for source in ('fr', 'pt'):
            status, _ = self._json('post', self._url('email-templates/offer/translate?language=fr'),
                                   body={'source_language': source})
            self.assertEqual(status, 400, source)

    def test_translate_reports_unavailable_service(self):
        with patch('app.utils.translation.TranslationService.translate_many', return_value=None):
            status, _ = self._json('post', self._url('email-templates/offer/translate?language=fr'),
                                   body={'source_language': 'en'})
        self.assertEqual(status, 503)

    # ------------------------------------------------------------------ layout

    def test_layout_save_validate_and_inherit(self):
        status, body = self._json('put', self._url('email-layout?language=en'), body={
            'brand_colour': '#123456', 'footer_markdown': '{{ event.name }} team'})
        self.assertEqual(status, 200, body)
        self.assertEqual(body['layout']['brand_colour'], '#123456')
        status, _ = self._json('put', self._url('email-layout?language=en'), body={'brand_colour': 'red'})
        self.assertEqual(status, 400)
        status, _ = self._json('put', self._url('email-layout?language=en'),
                               body={'footer_markdown': '{{ offer.url }}'})
        self.assertEqual(status, 400)
        status, _ = self._json('put', self._url('email-layout?language=en'),
                               body={'logo_url': 'javascript:alert(1)'})
        self.assertEqual(status, 400)
        status, body = self._json('post', self._url('email-layout/preview'), body={'language': 'en'})
        self.assertEqual(status, 200)
        self.assertIn('background:#123456', body['html'])
        self.assertIn('Indaba team', body['html'])


class EmailHistoryApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.event = self.add_event()
        self.event_id = self.event.id
        self.other_event = self.add_event(key='OTHER')
        self.other_event_id = self.other_event.id
        self.admin_id = self.add_user('eventadmin@example.org').id
        self.add_event_role('admin', self.admin_id, self.event_id)
        self.user = self.add_user('someone@example.org')
        self.user_id = self.user.id

        queue_email('withdrawal', self.user, event=self.event)
        queue_email('withdrawal', self.user, event=self.other_event)
        queue_email('password-reset', self.user, context={'reset': 'https://x.org/r?t=secret'})
        queue_email('new-guest', self.user, event=self.event,
                    context={'guest': 'Speaker', 'account': 'secret-code'})
        db.session.commit()
        self.headers = self.get_auth_header_for('eventadmin@example.org')

    def _get(self, path):
        response = self.app.get('/api/v1/events/{}/users/{}/emails{}'.format(self.event_id, self.user_id, path),
                                headers=self.headers)
        return response.status_code, json.loads(response.data)

    def test_lists_only_this_events_emails(self):
        status, body = self._get('')
        self.assertEqual(status, 200)
        self.assertEqual(body['total'], 2)
        self.assertEqual({m['template_key'] for m in body['messages']}, {'withdrawal', 'new-guest'})
        withdrawal = next(m for m in body['messages'] if m['template_key'] == 'withdrawal')
        self.assertEqual(withdrawal['template_name'], 'Application withdrawn')
        self.assertTrue(withdrawal['content_available'])

    def test_detail_shows_body_but_never_a_sensitive_one(self):
        _, body = self._get('')
        by_key = {m['template_key']: m['id'] for m in body['messages']}
        status, detail = self._get('/{}'.format(by_key['withdrawal']))
        self.assertEqual(status, 200)
        self.assertIn('withdrawn your application', detail['body_text'])
        status, detail = self._get('/{}'.format(by_key['new-guest']))
        self.assertEqual(status, 200)
        self.assertIsNone(detail['body_html'])
        self.assertIsNone(detail['body_text'])
        self.assertFalse(detail['content_available'])

    def test_other_events_message_is_not_found(self):
        other = db.session.query(OutboxMessage).filter_by(event_id=self.other_event_id).one()
        status, _ = self._get('/{}'.format(other.id))
        self.assertEqual(status, 404)

    def test_requires_event_admin(self):
        self.headers = self.get_auth_header_for('someone@example.org')
        self.assertEqual(self._get('')[0], 403)

    def test_resend_copies_and_refuses_sensitive(self):
        _, body = self._get('')
        by_key = {m['template_key']: m['id'] for m in body['messages']}
        url = '/api/v1/events/{}/users/{}/emails/{}/resend'.format(self.event_id, self.user_id,
                                                                    by_key['withdrawal'])
        response = self.app.post(url, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        copy = json.loads(response.data)
        self.assertEqual(copy['source_type'], 'resend')
        self.assertEqual(copy['status'], OutboxStatus.PENDING)

        url = '/api/v1/events/{}/users/{}/emails/{}/resend'.format(self.event_id, self.user_id,
                                                                    by_key['new-guest'])
        self.assertEqual(self.app.post(url, headers=self.headers).status_code, 400)

    def test_retention_task_requires_scheduler(self):
        self.assertEqual(self.app.get('/api/v1/tasks/email-retention').status_code, 403)
        response = self.app.get('/api/v1/tasks/email-retention', headers={'X-Appengine-Cron': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['purged'], 0)
