import json
from unittest import mock
from app.organisation.models import Organisation
from app.organisation.resolver import OrganisationResolver, ORGANISATION_CACHE_TTL_SECONDS
from app.utils.errors import FORBIDDEN
from app.utils.testing import ApiTestCase
from app import app, db


class OrganisationApiTest(ApiTestCase):
    def seed_static_data(self):
        self.add_organisation(
            name='Deep Learning Indaba', 
            system_name='Baobab', 
            small_logo='blah.png', 
            large_logo='blah_big.png', 
            domain='deeplearningindaba',
            languages=[{"code": "en", "description": "English"}])
        db.session.flush()

    def setUp(self):
        super(OrganisationApiTest, self).setUp()
        self.seed_static_data()

    def test_organisation_from_origin(self):
        with app.app_context():
            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': 'https://baobab.deeplearningindaba.com/apply'})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['name'], 'Deep Learning Indaba')
            self.assertEqual(data['small_logo'], 'blah.png')
            self.assertEqual(data['large_logo'], 'blah_big.png')
            self.assertEqual(data['domain'], 'deeplearningindaba')
            self.assertEqual(data['languages'][0]['code'], 'en')
            self.assertEqual(data['languages'][0]['description'], 'English')
            for key in ('primary_colour', 'secondary_colour', 'favicon'):
                self.assertIn(key, data)
                self.assertIsNone(data[key])

    def test_organisation_returns_branding_fields(self):
        org = Organisation.query.filter_by(domain='deeplearningindaba').one()
        org.primary_colour = '#112233'
        org.secondary_colour = '#445566'
        org.favicon = 'favicon.ico'
        db.session.commit()
        OrganisationResolver.bust_cache()

        response = self.app.get(
            '/api/v1/organisation',
            headers={'Origin': 'https://baobab.deeplearningindaba.com/apply'})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['primary_colour'], '#112233')
        self.assertEqual(data['secondary_colour'], '#445566')
        self.assertEqual(data['favicon'], 'favicon.ico')

    def test_organisation_from_referer(self):
        with app.app_context():
            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': '', 'referer': 'https://baobab.deeplearningindaba.com/apply'})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['name'], 'Deep Learning Indaba')
            self.assertEqual(data['small_logo'], 'blah.png')
            self.assertEqual(data['large_logo'], 'blah_big.png')
            self.assertEqual(data['domain'], 'deeplearningindaba')
            self.assertEqual(data['languages'][0]['code'], 'en')
            self.assertEqual(data['languages'][0]['description'], 'English')

    def test_organisation_error(self):
        with app.app_context():
            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': '', 'referer': ''})
            self.assertEqual(response.status_code, 400)

class OrganisationResolverCacheTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.add_organisation(name='Old Name', domain='ttl-org', webhook_secret_key='ttl-secret')
        OrganisationResolver.reset_cache()

    def tearDown(self):
        OrganisationResolver.reset_cache()
        super().tearDown()

    def test_cache_refreshes_only_after_ttl(self):
        with app.app_context():
            self.assertEqual(OrganisationResolver.resolve_from_domain('ttl-org').name, 'Old Name')

            org = Organisation.query.filter_by(domain='ttl-org').one()
            org.name = 'New Name'
            db.session.commit()

            self.assertEqual(OrganisationResolver.resolve_from_domain('ttl-org').name, 'Old Name')

            expired = OrganisationResolver._loaded_at + ORGANISATION_CACHE_TTL_SECONDS + 1
            with mock.patch('app.organisation.resolver.time.monotonic', return_value=expired):
                self.assertEqual(OrganisationResolver.resolve_from_domain('ttl-org').name, 'New Name')

    def test_stripe_signature_resolution_refreshes_after_ttl(self):
        with app.app_context():
            OrganisationResolver.resolve_from_domain('ttl-org')

            org = Organisation.query.filter_by(domain='ttl-org').one()
            org.name = 'New Name'
            db.session.commit()

            with mock.patch('app.organisation.resolver.verify_payload',
                            side_effect=lambda payload, secret, sig: secret == 'ttl-secret'):
                self.assertEqual(
                    OrganisationResolver.resolve_from_stripe_signature('payload', 'sig').name, 'Old Name')

                expired = OrganisationResolver._loaded_at + ORGANISATION_CACHE_TTL_SECONDS + 1
                with mock.patch('app.organisation.resolver.time.monotonic', return_value=expired):
                    self.assertEqual(
                        OrganisationResolver.resolve_from_stripe_signature('payload', 'sig').name, 'New Name')

    def test_reset_cache_clears_loaded_at(self):
        with app.app_context():
            OrganisationResolver.resolve_from_domain('ttl-org')
            self.assertIsNotNone(OrganisationResolver._loaded_at)
            OrganisationResolver.reset_cache()
            self.assertIsNone(OrganisationResolver._loaded_at)


class StripeSettingsApiTest(ApiTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/stripe-settings"

    def setUp(self):
        super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_prevent_non_admin_on_get_stripe_settings(self):
        self.add_user()

        header = self.get_auth_header_for('user@user.com')
        response = self.app.get(self.url, headers=header)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_get_stripe_settings(self):
        self.add_user(is_admin=True)

        header = self.get_auth_header_for('user@user.com')
        response = self.app.get(self.url, headers=header)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['iso_currency_code'], 'usd')
        self.assertEqual(data['stripe_api_publishable_key'], 'not_secret')
        self.assertEqual(data['stripe_api_secret_key'], 'secret_key')
        self.assertEqual(data['stripe_webhook_secret_key'], 'webhook_secret_key')

    def test_prevent_non_admin_on_post_stripe_settings(self):
        self.add_user()

        header = self.get_auth_header_for('user@user.com')
        response = self.app.post(self.url, headers=header)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_setting_of_stripe_currency_and_keys(self):

        self.add_user(is_admin=True)

        header = self.get_auth_header_for('user@user.com')
        params = {
            'iso_currency_code': 'zar',
            'publishable_key': 'very_public',
            'secret_key': '42',
            'webhook_secret_key': '616'
        }
        response = self.app.post(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['iso_currency_code'], 'zar')
        self.assertEqual(data['stripe_api_publishable_key'], 'very_public')
        self.assertEqual(data['stripe_api_secret_key'], '42')
        self.assertEqual(data['stripe_webhook_secret_key'], '616')


class OrganisationSettingsApiTest(ApiTestCase):
    url = '/api/v1/organisation/settings'

    def setUp(self):
        super().setUp()
        self.org_id = Organisation.query.filter_by(domain='org').one().id
        self.other_org = self.add_organisation(domain='otherorg', name='Other Org')
        self.other_org_id = self.other_org.id
        self.add_user(email='admin@user.com', is_admin=True)
        self.add_user(email='user@user.com')
        self.add_user(email='other@admin.com', is_admin=True, organisation_id=self.other_org_id)
        self.admin_header = self.get_auth_header_for('admin@user.com')
        self.user_header = self.get_auth_header_for('user@user.com')
        response = self.app.post('api/v1/authenticate', data={'email': 'other@admin.com', 'password': 'abc'},
                                 headers={'Origin': 'https://baobab.otherorg.com'})
        self.other_admin_header = {'Authorization': json.loads(response.data)['token']}

    def tearDown(self):
        OrganisationResolver.reset_cache()
        super().tearDown()

    def put(self, body, header=None):
        return self.app.put(self.url, headers=header or self.admin_header,
                            data=json.dumps(body), content_type='application/json')

    def stored(self):
        db.session.expire_all()
        return Organisation.query.get(self.org_id)

    def test_get_returns_settings_without_secrets(self):
        response = self.app.get(self.url, headers=self.admin_header)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['domain'], 'org')
        self.assertEqual(data['name'], 'My Org')
        self.assertEqual(data['stripe_api_publishable_key'], 'not_secret')
        self.assertTrue(data['stripe_secret_key_set'])
        self.assertTrue(data['stripe_webhook_secret_key_set'])
        self.assertNotIn('stripe_api_secret_key', data)
        self.assertNotIn('stripe_webhook_secret_key', data)
        self.assertNotIn('"secret_key"', response.data.decode())
        self.assertNotIn('"webhook_secret_key"', response.data.decode())

    def test_get_secret_flags_false_when_cleared(self):
        self.put({'stripe_api_secret_key': None, 'stripe_webhook_secret_key': ''})
        data = json.loads(self.app.get(self.url, headers=self.admin_header).data)
        self.assertFalse(data['stripe_secret_key_set'])
        self.assertFalse(data['stripe_webhook_secret_key_set'])

    def test_put_changes_only_given_field(self):
        before = self.get_settings_snapshot()
        response = self.put({'primary_colour': '#123456'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['primary_colour'], '#123456')

        after = self.get_settings_snapshot()
        before['primary_colour'] = '#123456'
        self.assertEqual(before, after)

        public = self.app.get('/api/v1/organisation')
        self.assertEqual(json.loads(public.data)['primary_colour'], '#123456')

    def get_settings_snapshot(self):
        org = self.stored()
        return {c.name: getattr(org, c.name) for c in Organisation.__table__.columns}

    def test_put_omitting_secrets_keeps_them(self):
        response = self.put({'name': 'Renamed'})
        self.assertEqual(response.status_code, 200)
        org = self.stored()
        self.assertEqual(org.stripe_api_secret_key, 'secret_key')
        self.assertEqual(org.stripe_webhook_secret_key, 'webhook_secret_key')

    def test_put_null_clears_secrets(self):
        response = self.put({'stripe_api_secret_key': None, 'stripe_webhook_secret_key': None})
        self.assertEqual(response.status_code, 200)
        org = self.stored()
        self.assertIsNone(org.stripe_api_secret_key)
        self.assertIsNone(org.stripe_webhook_secret_key)

    def test_put_string_replaces_secret(self):
        response = self.put({'stripe_api_secret_key': 'sk_new'})
        self.assertEqual(response.status_code, 200)
        org = self.stored()
        self.assertEqual(org.stripe_api_secret_key, 'sk_new')
        self.assertEqual(org.stripe_webhook_secret_key, 'webhook_secret_key')
        self.assertNotIn('sk_new', response.data.decode())

    def test_put_full_round_trip(self):
        body = {
            'name': '  New Name  ',
            'system_name': 'NewSys',
            'url': 'https://new.example.org',
            'system_url': 'http://baobab.example.org',
            'email_from': 'hi@example.org',
            'languages': [{'code': 'fr', 'description': 'Francais'}, {'code': 'en', 'description': 'English'}],
            'favicon': 'fav.ico',
            'secondary_colour': '#abcdef',
            'iso_currency_code': 'ZAR',
            'stripe_api_publishable_key': 'pk_new',
        }
        response = self.put(body)
        self.assertEqual(response.status_code, 200)
        get = json.loads(self.app.get(self.url, headers=self.admin_header).data)
        self.assertEqual(json.loads(response.data), get)
        self.assertEqual(get['name'], 'New Name')
        self.assertEqual(get['system_name'], 'NewSys')
        self.assertEqual(get['url'], 'https://new.example.org')
        self.assertEqual(get['email_from'], 'hi@example.org')
        self.assertEqual(get['languages'][0]['code'], 'fr')
        self.assertEqual(get['favicon'], 'fav.ico')
        self.assertEqual(get['secondary_colour'], '#abcdef')
        self.assertEqual(get['iso_currency_code'], 'ZAR')
        self.assertEqual(get['stripe_api_publishable_key'], 'pk_new')

    def test_put_null_or_empty_clears_nullable_fields(self):
        self.put({'favicon': 'fav.ico', 'primary_colour': '#123456'})
        response = self.put({'favicon': None, 'primary_colour': '', 'email_from': '  '})
        self.assertEqual(response.status_code, 200)
        org = self.stored()
        self.assertIsNone(org.favicon)
        self.assertIsNone(org.primary_colour)
        self.assertIsNone(org.email_from)

    def assert_invalid(self, body, field):
        before = self.get_settings_snapshot()
        response = self.put(body)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data)['field'], field)
        self.assertEqual(before, self.get_settings_snapshot())

    def test_put_rejects_domain_and_id(self):
        self.assert_invalid({'domain': 'evil'}, 'domain')
        self.assert_invalid({'id': 99}, 'id')

    def test_put_rejects_unknown_key(self):
        self.assert_invalid({'primry_colour': '#123456'}, 'primry_colour')

    def test_put_rejects_bad_colour(self):
        self.assert_invalid({'primary_colour': 'red'}, 'primary_colour')
        self.assert_invalid({'secondary_colour': '#12345'}, 'secondary_colour')

    def test_put_rejects_empty_or_null_required_fields(self):
        self.assert_invalid({'name': ''}, 'name')
        self.assert_invalid({'name': '   '}, 'name')
        self.assert_invalid({'system_name': None}, 'system_name')
        self.assert_invalid({'small_logo': ''}, 'small_logo')

    def test_put_rejects_invalid_values_without_partial_save(self):
        self.assert_invalid({'name': 'Changed', 'primary_colour': 'nope'}, 'primary_colour')

    def test_put_rejects_bad_lengths_and_formats(self):
        self.assert_invalid({'name': 'x' * 51}, 'name')
        self.assert_invalid({'url': 'ftp://x.org'}, 'url')
        self.assert_invalid({'email_from': 'nope'}, 'email_from')
        self.assert_invalid({'favicon': 'x' * 256}, 'favicon')
        self.assert_invalid({'iso_currency_code': 'usd'}, 'iso_currency_code')
        self.assert_invalid({'stripe_api_secret_key': 'x' * 201}, 'stripe_api_secret_key')

    def test_put_rejects_bad_languages(self):
        self.assert_invalid({'languages': [{'code': 'de', 'description': 'Deutsch'}]}, 'languages')
        self.assert_invalid({'languages': [{'code': 'en', 'description': 'A'},
                                           {'code': 'en', 'description': 'B'}]}, 'languages')
        self.assert_invalid({'languages': []}, 'languages')
        self.assert_invalid({'languages': None}, 'languages')
        self.assert_invalid({'languages': [{'code': 'en', 'description': ''}]}, 'languages')
        self.assert_invalid({'languages': ['en']}, 'languages')

    def test_non_admin_forbidden(self):
        self.assertEqual(self.app.get(self.url, headers=self.user_header).status_code, 403)
        self.assertEqual(self.put({'name': 'X'}, header=self.user_header).status_code, 403)
        self.assertEqual(self.stored().name, 'My Org')

    def test_admin_of_other_organisation_forbidden(self):
        origin = {'Origin': 'https://baobab.otherorg.com'}
        headers = dict(self.admin_header, **origin)
        response = self.app.get(self.url, headers=headers)
        self.assertEqual(response.status_code, 403)
        response = self.app.put(self.url, headers=headers, data=json.dumps({'name': 'X'}),
                                content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Organisation.query.get(self.other_org_id).name, 'Other Org')

        # The other organisation's own admin is allowed
        headers = dict(self.other_admin_header, **origin)
        self.assertEqual(self.app.get(self.url, headers=headers).status_code, 200)

    def test_no_token_unauthorized(self):
        self.assertEqual(self.app.get(self.url).status_code, 401)
        response = self.app.put(self.url, data=json.dumps({'name': 'X'}), content_type='application/json')
        self.assertEqual(response.status_code, 401)
