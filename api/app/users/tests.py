import json

from datetime import datetime, timedelta

from app import app, db
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country, UserComment
from app.events.models import Event, EventRole
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response
from app.organisation.models import Organisation


USER_DATA = {
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

AUTH_DATA = {
        'email': 'something@email.com',
        'password': '123456'
    }

class UserApiTest(ApiTestCase):

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

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def test_registration(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
        data = json.loads(response.data)

        assert data['id'] == 1
        assert len(data['token']) > 10

    def test_duplicate_registration(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
        assert response.status_code == 201

        response = self.app.post('/api/v1/user', data=USER_DATA)
        assert response.status_code == 409

    def test_get_user(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        response = self.app.post('/api/v1/user', data=USER_DATA)
        data = json.loads(response.data)
        assert response.status_code == 201

        headers = {'Authorization': data['token']}

        response = self.app.delete('api/v1/user', headers=headers)
        assert response.status_code == 200

        response = self.app.post('/api/v1/authenticate', data=AUTH_DATA)
        assert response.status_code == 404

    def test_authentication_unverified_email(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data=AUTH_DATA)
        assert response.status_code == 422

    def test_authentication_wrong_password(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        response = self.app.post('/api/v1/user', data=USER_DATA)
        data = json.loads(response.data)
        assert response.status_code == 201

        user = db.session.query(AppUser).filter(
            AppUser.id == data['id']).first()

        response = self.app.get(
            '/api/v1/verify-email?token='+user.verify_token)
        assert response.status_code == 201

        response = self.app.post('/api/v1/authenticate', data=AUTH_DATA)
        assert response.status_code == 200

    def test_authentication_response(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
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

        response = self.app.post('/api/v1/authenticate', data=AUTH_DATA)
        data = json.loads(response.data)

        self.assertEqual(data['firstname'], USER_DATA['firstname'])
        self.assertEqual(data['lastname'], USER_DATA['lastname'])
        self.assertEqual(data['title'], USER_DATA['user_title'])
        self.assertEqual(data['roles'], [
            {'event_id': self.event1_id, 'role': 'admin'},
            {'event_id': self.event2_id, 'role': 'reviewer'},
        ])

    def test_password_reset_user_does_not_exist(self):
        response = self.app.post('/api/v1/password-reset/request', data={
            'email': 'something@email.com'
        })
        assert response.status_code == 404

    def test_password_reset_expired(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        response = self.app.post('/api/v1/user', data=USER_DATA)
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
        self.app.post('/api/v1/user', data=USER_DATA)
        response = self.app.get(
            '/api/v1/resend-verification-email?email={}'.format(USER_DATA['email']))
        assert response.status_code == 201

    def test_resend_verification_email_no_user(self):
        self.seed_static_data()

        response = self.app.get(
            '/api/v1/resend-verification-email?email={}'.format('nonexistant@dummy.com'))
        assert response.status_code == 404

    def setup_verified_user(self):
        user = AppUser('something@email.com', 'Some', 'Thing', 'Mr',
                         1, 1, 'Male', 'University', 'Computer Science', 
                         'None', 1, datetime(1984, 12, 12),
                          'English', '123456', 1)
        user.verify_token = 'existing token'
        user.verify()
        db.session.add(user)
        db.session.commit()

    def test_email_change_gets_new_token_and_is_unverified(self):
        self.seed_static_data()
        self.setup_verified_user()
        response = self.app.post('/api/v1/authenticate', data=AUTH_DATA)
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

    def setup_responses(self):
        application_forms = [
            ApplicationForm(1, True, datetime(2019, 4, 12)),
            ApplicationForm(2, False, datetime(2019, 4, 12))
        ]
        db.session.add_all(application_forms)

        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr', 1, 1, 'M', 'UWC', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms', 1, 1, 'F', 'RU', 'Chem', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        candidate3 = AppUser('c3@c.com', 'candidate', '3', 'Mr', 1, 1, 'M', 'UFH', 'Phys', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        event_admin = AppUser('ea@ea.com', 'event_admin', '1', 'Ms', 1, 1, 'F', 'NWU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        users = [candidate1, candidate2, candidate3, event_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)

        event_role = EventRole('admin', 4, 1)
        db.session.add(event_role)

        responses = [
            Response(1, 1, True, datetime(2019, 4, 10)),
            Response(1, 2, True, datetime(2019, 4, 9), True, datetime(2019, 4, 11)),
            Response(2, 3, True)
        ]
        db.session.add_all(responses)
        db.session.commit()

    def test_user_profile_list(self):
        self.seed_static_data()
        self.setup_responses()
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/userprofilelist', headers=header, data=params)

        data = json.loads(response.data)
        data = sorted(data, key=lambda k: k['user_id'])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['user_id'], 1)
        self.assertEqual(data[0]['is_submitted'], True)
        self.assertEqual(data[0]['submitted_timestamp'], u'2019-04-10T00:00:00')
        self.assertEqual(data[0]['is_withdrawn'], False)
        self.assertEqual(data[0]['withdrawn_timestamp'], None)
        self.assertEqual(data[1]['user_id'], 2)
        self.assertEqual(data[1]['is_submitted'], True)
        self.assertEqual(data[1]['submitted_timestamp'], u'2019-04-09T00:00:00')
        self.assertEqual(data[1]['is_withdrawn'], True)
        self.assertEqual(data[1]['withdrawn_timestamp'], u'2019-04-11T00:00:00')

class UserCommentAPITest(ApiTestCase):

    def seed_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        self.event1 = Event('Indaba', 'Indaba Event',
                            datetime.now(), datetime.now())
        db.session.add(self.event1)
        db.session.commit()

        self.event1_id = self.event1.id
        
        user_data1 = USER_DATA.copy()
        response = self.app.post('/api/v1/user', data=user_data1)
        self.user1 = json.loads(response.data)

        user_data2 = USER_DATA.copy()
        user_data2['email'] = 'person2@person.com'
        user_data2['firstname'] = 'Person'
        user_data2['lastname'] = 'Two'
        response = self.app.post('/api/v1/user', data=user_data2)
        self.user2 = json.loads(response.data)

        user2 = db.session.query(AppUser).filter(AppUser.email == 'person2@person.com').first()
        user2.is_admin = True
        db.session.flush()


    def seed_comments(self):
        self.comment1 = UserComment(self.event1_id, self.user1['id'], self.user2['id'], datetime.now(), 'Comment 1')
        self.comment2 = UserComment(self.event1_id, self.user1['id'], self.user2['id'], datetime.now(), 'Comment 2')
        self.comment3 = UserComment(self.event1_id, self.user2['id'], self.user1['id'], datetime.now(), 'Comment 3')

        db.session.add_all([self.comment1, self.comment2, self.comment3])
        db.session.flush()

    def test_post_comment(self):
        with app.app_context():
            self.seed_static_data()

            params = {'event_id': self.event1_id, 'user_id': self.user2['id'], 'comment': 'Comment1'}
            print('Sending params: ', params)
            response = self.app.post('/api/v1/user-comment', headers={'Authorization': self.user1['token']}, data=json.dumps(params), content_type='application/json')
            data = json.loads(response.data)

            self.assertEqual(response.status_code, 201)

    def test_get_forbidden(self):
        with app.app_context():
            self.seed_static_data()
            self.seed_comments()

            params = {'event_id': self.event1_id, 'user_id': self.user2['id']}
            response = self.app.get('/api/v1/user-comment', headers={'Authorization': self.user1['token']}, query_string=params)

            self.assertEqual(response.status_code, 403)

    def test_get_comments(self):
        with app.app_context():
            self.seed_static_data()
            self.seed_comments()

            params = {'event_id': self.event1_id, 'user_id': self.user1['id']}
            response = self.app.get('/api/v1/user-comment', headers={'Authorization': self.user2['token']}, query_string=params)
            comment_list = json.loads(response.data)

            self.assertEqual(len(comment_list), 2)
            self.assertEqual(comment_list[0]['event_id'], self.comment1.event_id)
            self.assertEqual(comment_list[0]['user_id'], self.comment1.user_id)
            self.assertEqual(comment_list[0]['comment_by_user_firstname'], self.user2['firstname'])
            self.assertEqual(comment_list[0]['comment_by_user_lastname'], self.user2['lastname'])
            self.assertEqual(comment_list[0]['comment'], self.comment1.comment)

            self.assertEqual(comment_list[1]['event_id'], self.comment2.event_id)
            self.assertEqual(comment_list[1]['user_id'], self.comment2.user_id)
            self.assertEqual(comment_list[1]['comment_by_user_firstname'], self.user2['firstname'])
            self.assertEqual(comment_list[1]['comment_by_user_lastname'], self.user2['lastname'])
            self.assertEqual(comment_list[1]['comment'], self.comment2.comment)

class UserProfileApiTest(ApiTestCase):
    def setup_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))

        events = [
            Event('Indaba', 'Indaba Event', datetime.now(), datetime.now()),
            Event('Indaba2', 'Indaba Event 2', datetime.now(), datetime.now())
        ]
        db.session.add_all(events)

        application_forms = [
            ApplicationForm(1, True, datetime.now()),
            ApplicationForm(2, False, datetime.now())
        ]
        db.session.add_all(application_forms)

        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr', 1, 1, 'M', 'UWC', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms', 1, 1, 'F', 'RU', 'Chem', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        system_admin = AppUser('system_admin@sa.com', 'system_admin', '1', 'Mr', 1, 1, 'M', 'UFH', 'Phys', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1, True)
        event_admin = AppUser('event_admin@ea.com', 'event_admin', '1', 'Ms', 1, 1, 'F', 'NWU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        reviewer = AppUser('reviewer@r.com', 'reviewer', '1', 'Ms', 1, 1, 'F', 'NWU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        users = [candidate1, candidate2, system_admin, event_admin, reviewer]
        for user in users:
            user.verify()
        db.session.add_all(users)

        event_roles = [
            EventRole('admin', 4, 1),
            EventRole('reviwer', 5, 1)
        ]
        db.session.add_all(event_roles)
        
        responses = [
            Response(1, 1, True, datetime(2019, 4, 10)),
            Response(2, 2, True, datetime(2019, 4, 9))
        ]
        db.session.add_all(responses)
        db.session.commit()
    
    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def test_user_not_found_when_not_event_admin(self):
        self.setup_static_data()
        header = self.get_auth_header_for('reviewer@r.com')
        params = {'user_id': 1}

        response = self.app.get('/api/v1/userprofile', headers=header, data=params)

        self.assertEqual(response.status_code, 404)
    
    def test_user_not_found_when_does_not_exist(self):
        self.setup_static_data()
        header = self.get_auth_header_for('system_admin@sa.com')
        params = {'user_id': 99}

        response = self.app.get('/api/v1/userprofile', headers=header, data=params)

        self.assertEqual(response.status_code, 404)

    def test_get_user_when_system_admin(self):
        self.setup_static_data()
        header = self.get_auth_header_for('system_admin@sa.com')
        params = {'user_id': 2}

        response = self.app.get('/api/v1/userprofile', headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(data['email'], 'c2@c.com')

    def test_get_user_when_event_admin(self):
        self.setup_static_data()
        header = self.get_auth_header_for('event_admin@ea.com')
        params = {'user_id': 1}

        response = self.app.get('/api/v1/userprofile', headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(data['email'], 'c1@c.com')

class EmailerAPITest(ApiTestCase):
    def setup_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))

        self.candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr', 1, 1, 'M', 'UWC', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        self.candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms', 1, 1, 'F', 'RU', 'Chem', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        self.system_admin = AppUser('system_admin@sa.com', 'system_admin', '1', 'Mr', 1, 1, 'M', 'UFH', 'Phys', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1, True)

        users = [self.candidate1, self.candidate2, self.system_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)

        db.session.commit()
    
    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def test_forbidden_when_not_admin(self):
        with app.app_context():
            self.setup_static_data()
            header = self.get_auth_header_for('c1@c.com')
            params = {
                'user_id': self.candidate2.id,
                'email_subject': 'This is a test email',
                'email_body': 'Hello world, this is a test email.'
            }

            response = self.app.post('/api/v1/admin/emailer', headers=header, data=params)

            self.assertEqual(response.status_code, 403)
    
    def test_email(self):
        with app.app_context():
            self.setup_static_data()
            header = self.get_auth_header_for('system_admin@sa.com')
            params = {
                'user_id': self.candidate2.id,
                'email_subject': 'This is a test email',
                'email_body': 'Hello world, this is a test email.'
            }

            response = self.app.post('/api/v1/admin/emailer', headers=header, data=params)
            self.assertEqual(response.status_code, 200)

class OrganisationUserTest(ApiTestCase):
    """Test that users are correctly linked to organisations"""
    def seed_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.add(Organisation('Indaba', 'System X', 'logo.png', 'large_logo.png', 'indaba', 'indaba.com'))

        self.user1_org1 = AppUser('first_user@c.com', 'candidate', '1', 'Mr', 1, 1, 'M', 'UWC', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1)
        self.user1_org2 = AppUser('first_user@c.com', 'candidate', '2', 'Ms', 1, 1, 'F', 'RU', 'Chem', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 2)
        self.user2_org1 = AppUser('second_user@c.com', 'system_admin', '1', 'Mr', 1, 1, 'M', 'UFH', 'Phys', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc', 1, True)

        users = [self.user1_org1, self.user1_org2, self.user2_org1]
        for user in users:
            user.verify()
        db.session.add_all(users)

        db.session.commit()

    def get_auth_header_for(self, email, domain):
        body = {
            'email': email,
            'password': 'abc'
        }

        response = self.app.post('api/v1/authenticate', data=body, headers={'Origin': domain})
        data = json.loads(response.data)
        header = {
            'Authorization': data['token'],
            'Origin': domain
        }
        return header

    def test_auth_org(self):
        """Test that authentication is linked to organisation."""
        with app.app_context():
            self.seed_static_data()
            headers = self.get_auth_header_for('first_user@c.com', 'www.indaba.net/blah')
            response = self.app.get('/api/v1/user', headers=headers)
            data = json.loads(response.data)
            self.assertEqual(data['firstname'], 'candidate')
            self.assertEqual(data['lastname'], '2')

            headers = self.get_auth_header_for('first_user@c.com', 'www.org.net/blah')
            response = self.app.get('/api/v1/user', headers=headers)
            data = json.loads(response.data)
            self.assertEqual(data['firstname'], 'candidate')
            self.assertEqual(data['lastname'], '1')

    def test_cant_auth_outside_org(self):
        with app.app_context():
            self.seed_static_data()
            body = {
                'email': 'second_user@c.com',
                'password': 'abc'
            }

            response = self.app.post('api/v1/authenticate', data=body, headers={'Origin': 'www.indaba.net/blah'})
            self.assertEqual(response.status_code, 401)

    def allow_same_email_different_org(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.add(Organisation('Indaba', 'System X', 'logo.png', 'large_logo.png', 'indaba', 'indaba.com'))
        db.session.commit()

        response = self.app.post('/api/v1/user', data=USER_DATA, headers={'Origin': 'www.myorg.net'})
        self.assertEqual(response.status_code, 201)

        response = self.app.post('/api/v1/user', data=USER_DATA, headers={'Origin': 'www.indaba.net'})
        self.assertEqual(response.status_code, 201)

        response = self.app.post('/api/v1/user', data=USER_DATA, headers={'Origin': 'www.indaba.net'})
        self.assertEqual(response.status_code, 409)


        