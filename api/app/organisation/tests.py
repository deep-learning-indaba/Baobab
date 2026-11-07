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