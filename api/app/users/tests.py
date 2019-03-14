import json

from datetime import datetime, timedelta

from app import db
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country


class UserApiTest(ApiTestCase):

    user_data = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title': 'Mr',
        'nationality_country_id': 1,
        'residence_country_id': 1,
        'user_gender': 'Male',
        'affiliation': 'University',
        'department': 'Computer Science',
        'user_disability': 'None',
        'user_category_id': 1,
        'user_primaryLanguage': 'Zulu',
        'user_dateOfBirth': '1984-12-12',
        'password': '123456'
    }

    auth_data = {
        'email': 'something@email.com',
        'password': '123456'
    }

    def seed_static_data(self):
        db.session.add(UserCategory('Postdoc'))
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
        assert data['firstname'] == 'Some'
        assert data['lastname'] == 'Thing'
        assert data['user_title'] == 'Mr'
        assert data['nationality_country'] == 'South Africa'
        assert data['residence_country'] == 'South Africa'
        assert data['user_gender'] == 'Male'
        assert data['affiliation'] == 'University'
        assert data['department'] == 'Computer Science'
        assert data['user_disability'] == 'None'
        assert data['user_category'] == 'Postdoc'
        assert data['user_primaryLanguage'] == 'Zulu'
        assert data['user_dateOfBirth'] == '1984-12-12'

    def test_update_user(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        headers = {'Authorization': data['token']}

        response = self.app.put('/api/v1/user', headers=headers, data={
            'email': 'something@email.com',
            'firstname': 'Updated',
            'lastname': 'Updated',
            'user_title': 'Mrs',
            'nationality_country_id': 1,
            'residence_country_id': 1,
            'user_gender': 'Female',
            'affiliation': 'Company',
            'department': 'AI',
            'user_disability': 'None',
            'user_category_id': 1,
            'user_primaryLanguage': 'Zulu',
            'user_dateOfBirth': '1984-12-12',
            'password': ''
        })
        assert response.status_code == 200

        response = self.app.get('/api/v1/user', headers=headers)
        data = json.loads(response.data)
        assert data['email'] == 'something@email.com'
        assert data['firstname'] == 'Updated'
        assert data['lastname'] == 'Updated'
        assert data['user_title'] == 'Mrs'
        assert data['nationality_country'] == 'South Africa'
        assert data['residence_country'] == 'South Africa'
        assert data['user_gender'] == 'Female'
        assert data['affiliation'] == 'Company'
        assert data['department'] == 'AI'
        assert data['user_disability'] == 'None'
        assert data['user_category'] == 'Postdoc'
        assert data['user_primaryLanguage'] == 'Zulu'
        assert data['user_dateOfBirth'] == '1984-12-12'

    def test_authentication_deleted(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        headers = {'Authorization': data['token']}

        response = self.app.delete('api/v1/user', headers=headers)
        assert response.status_code == 200

        response = self.app.post('/api/v1/authenticate', data=self.auth_data)
        assert response.status_code == 404

    def test_authentication_unverified_email(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data=self.auth_data)
        assert response.status_code == 422

    def test_authentication_wrong_password(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'wrong'
        })
        assert response.status_code == 401

    def test_authentication(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data=self.auth_data)
        assert response.status_code == 200

    def test_password_reset_user_does_not_exist(self):
        response = self.app.post('/api/v1/password-reset/request', data={
            'email': 'something@email.com'
        })
        assert response.status_code == 409

    def test_password_reset_expired(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)
        assert response.status_code == 201

        response = self.app.post('/api/v1/password-reset/request', data={
            'email': 'something@email.com'
        })
        assert response.status_code == 201

        pw_reset = db.session.query(PasswordReset).first()
        pw_reset.date = datetime.now() - timedelta(days=2)
        db.session.commit()

        response = self.app.post('/api/v1/password-reset/confirm', data={
            'code': pw_reset.code,
            'password': 'abc123'
        })
        assert response.status_code == 400

    def test_password_reset(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)
        assert response.status_code == 201

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)
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
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc123'
        })

        assert response.status_code == 200

    def test_deletion(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)

        user_id = data['id']
        headers = {'Authorization': data['token']}
        response = self.app.delete('/api/v1/user', headers=headers)
        assert response.status_code == 200

        user = db.session.query(AppUser).filter(AppUser.id == user_id).first()
        assert user.email == 'something@email.com'
        assert user.is_deleted == True

    def test_resend_verification_email(self):
        self.seed_static_data()
        self.app.post('/api/v1/user', data=self.user_data)
        response = self.app.get(
            '/api/v1/resend-verification-email?email={}'.format(self.user_data['email']))
        assert response.status_code == 201

    def test_resend_verification_email_no_user(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/resend-verification-email?email={}'.format('nonexistant@dummy.com'))
        assert response.status_code == 409
