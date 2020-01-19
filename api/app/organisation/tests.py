import json
from app.utils.testing import ApiTestCase
from app import app, db, LOGGER
from app.organisation.models import Organisation


class GuestRegistrationApiTest(ApiTestCase):
    def seed_static_data(self):
        organisation1 = Organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba', False)
        organisation2 = Organisation('My Org', 'org.png', 'org_big.png', 'org', True)
        db.session.add(organisation1)
        db.session.add(organisation2)
        db.session.commit()
        db.session.flush()

    def test_organisation_from_origin(self):
        with app.app_context():
            self.seed_static_data()

            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': 'https://baobab.deeplearningindaba.com/apply'})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['name'], 'Deep Learning Indaba')
            self.assertEqual(data['small_logo'], 'blah.png')
            self.assertEqual(data['large_logo'], 'blah_big.png')
            self.assertEqual(data['domain'], 'deeplearningindaba')
            self.assertEqual(data['is_default'], False)

    def test_organisation_from_referer(self):
        with app.app_context():
            self.seed_static_data()

            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': '', 'referer': 'https://baobab.deeplearningindaba.com/apply'})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['name'], 'Deep Learning Indaba')
            self.assertEqual(data['small_logo'], 'blah.png')
            self.assertEqual(data['large_logo'], 'blah_big.png')
            self.assertEqual(data['domain'], 'deeplearningindaba')
            self.assertEqual(data['is_default'], False)

    def test_organisation_default(self):
        with app.app_context():
            self.seed_static_data()

            response = self.app.get(
                '/api/v1/organisation',
                headers={'Origin': '', 'referer': ''})
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['name'], 'My Org')
            self.assertEqual(data['small_logo'], 'org.png')
            self.assertEqual(data['large_logo'], 'org_big.png')
            self.assertEqual(data['domain'], 'org')
            self.assertEqual(data['is_default'], True)