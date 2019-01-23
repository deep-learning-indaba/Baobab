import json

from app import db
from app.utils.testing import ApiTestCase
from app.users.models import PasswordReset, UserTitle, UserCategory, UserDisability, UserEthnicity, UserGender, Country


class UserApiTest(ApiTestCase):

    user_data = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title_id': 1,
        'nationality_country_id': 1,
        'residence_country_id': 1,
        'user_ethnicity_id': 1,
        'user_gender_id': 1,
        'affiliation': 'University',
        'department': 'Computer Science',
        'user_disability_id': 1,
        'user_category_id': 1,
        'password': '123456'
    }

    def seed_static_data(self):
        db.session.add(UserTitle('Mr'))
        db.session.add(UserCategory('Postdoc'))
        db.session.add(UserDisability('None'))
        db.session.add(UserEthnicity('None'))
        db.session.add(UserGender('Male'))
        db.session.add(Country('South Africa'))
        db.session.flush()

    def test_registration(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)

        assert data['id'] == 1
        assert len(data['token']) > 10

    def test_duplicate_registration(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        assert response.status_code == 201

        response = self.app.post('/api/v1/user', data=self.user_data)
        assert response.status_code == 409

    def test_get_user(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)

        headers = {'Authorization': data['token']}

        response = self.app.get('/api/v1/user', headers=headers)
        data = json.loads(response.data)
        assert data['email'] == 'something@email.com'

    def test_password_reset(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        assert response.status_code == 201

        response = self.app.post('/api/v1/password-reset/request', data={
            'email': 'something@email.com'
        })
        assert response.status_code == 201

        pw_reset = db.session.query(PasswordReset).first()

        response = self.app.post('/api/v1/password-reset/confirm', data={
            'code': "bad code",
            'password': 'abc123'
        })
        assert response.status_code == 401

        response = self.app.post('/api/v1/password-reset/confirm', data={
            'code': pw_reset.code,
            'password': 'abc123'
        })
        assert response.status_code == 200

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc123'
        })

        assert response.status_code == 200
