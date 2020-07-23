import json
from app.utils.testing import ApiTestCase
from app import app, db, LOGGER
from app.organisation.models import Organisation


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
