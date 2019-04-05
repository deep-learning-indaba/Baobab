import json

from datetime import datetime, timedelta

from app import db
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country
from app.events.models import Event, EventRole


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
        'user_dateOfBirth':  datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'password': '123456'
    }

    auth_data = {
        'email': 'something@email.com',
        'password': '123456'
    }

    def seed_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        self.event1 = Event('Indaba', 'Indaba Event',
                            datetime.now(), datetime.now())
        self.event2 = Event('IndabaX', 'IndabaX Sudan',
                            datetime.now(), datetime.now())
        db.session.add(self.event1)
        db.session.add(self.event2)
        db.session.commit()

        self.event1_id = self.event1.id
        self.event2_id = self.event2.id

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
        assert data['user_dateOfBirth'] == datetime(
            1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S')

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
            'user_dateOfBirth':  datetime(1984, 12, 12, 0, 0, 0).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
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
        assert data['user_dateOfBirth'] == datetime(
            1984, 12, 12, 0, 0, 0, 0).strftime('%Y-%m-%dT%H:%M:%S')

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

    def test_authentication_response(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=self.user_data)
        data = json.loads(response.data)

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)

        role1 = EventRole('admin', data['id'], self.event1_id)
        role2 = EventRole('reviewer', data['id'], self.event2_id)

        db.session.add(role1)
        db.session.add(role2)
        db.session.commit()
        db.session.flush()

        response = self.app.post('/api/v1/authenticate', data=self.auth_data)
        data = json.loads(response.data)

        self.assertEqual(data['firstname'], self.user_data['firstname'])
        self.assertEqual(data['lastname'], self.user_data['lastname'])
        self.assertEqual(data['title'], self.user_data['user_title'])
        self.assertEqual(data['roles'], [
            {'event_id': self.event1_id, 'role': 'admin'},
            {'event_id': self.event2_id, 'role': 'reviewer'},
        ])

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
        assert response.status_code == 418

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

    def setup_verified_user(self):
        user = AppUser('something@email.com', 'Some', 'Thing', 'Mr',
                         1, 1, 'Male', 'University', 'Computer Science', 
                         'None', 1, datetime(1984, 12, 12),
                          'English', '123456')
        user.verify_token = 'existing token'
        user.verify()
        db.session.add(user)
        db.session.commit()

    def test_email_change_gets_new_token_and_is_unverified(self):
        self.seed_static_data()
        self.setup_verified_user()
        response = self.app.post('/api/v1/authenticate', data=self.auth_data)
        data = json.loads(response.data)
        headers = {'Authorization': data['token']}

        response = self.app.put('/api/v1/user', headers=headers, data={
            'email': 'somethingnew@email.com',
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
            'user_dateOfBirth':  datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'password':''
            })

        self.assertEqual(response.status_code,  200)

        user = db.session.query(AppUser).get(1)

        self.assertEqual(user.email, 'somethingnew@email.com')
        self.assertEqual(user.firstname, 'Some')
        self.assertEqual(user.lastname, 'Thing')
        self.assertEqual(user.user_title, 'Mr')
        self.assertEqual(user.nationality_country_id, 1)
        self.assertEqual(user.residence_country_id, 1)
        self.assertEqual(user.user_gender, 'Male')
        self.assertEqual(user.affiliation, 'University')
        self.assertEqual(user.department, 'Computer Science')
        self.assertEqual(user.user_disability, 'None')
        self.assertEqual(user.user_category_id, 1)
        self.assertEqual(user.user_primaryLanguage, 'Zulu')
        self.assertEqual(user.user_dateOfBirth, datetime(1984, 12, 12))
        self.assertEqual(user.verified_email, False)
        self.assertNotEqual(user.verify_token, 'existing token')
   