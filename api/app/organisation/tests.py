import json
from app.organisation.resolver import OrganisationResolver
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

class StripeSettingsApiTest(ApiTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/stripe-settings"

    def setUp(self):
        super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_prevent_non_admin_on_get_stripe_settings(self):
        print(OrganisationResolver._secrets_cache)
        self.add_user()

        header = self.get_auth_header_for('user@user.com')
        response = self.app.get(self.url, headers=header)

        print(OrganisationResolver._secrets_cache)
        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_get_stripe_settings(self):
        print(OrganisationResolver._secrets_cache)
        self.add_user(is_admin=True)

        header = self.get_auth_header_for('user@user.com')
        response = self.app.get(self.url, headers=header)
        print(OrganisationResolver._secrets_cache)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['iso_currency_code'], 'usd')
        self.assertEqual(data['stripe_api_publishable_key'], 'not_secret')
        self.assertEqual(data['stripe_api_secret_key'], 'secret_key')
        self.assertEqual(data['stripe_webhook_secret_key'], 'webhook_secret_key')

    def test_prevent_non_admin_on_post_stripe_settings(self):
        print(OrganisationResolver._secrets_cache)
        self.add_user()

        header = self.get_auth_header_for('user@user.com')
        response = self.app.post(self.url, headers=header)
        print(OrganisationResolver._secrets_cache)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_setting_of_stripe_currency_and_keys(self):
        print(OrganisationResolver._secrets_cache)

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

        print(OrganisationResolver._secrets_cache)