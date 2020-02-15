import json

from datetime import datetime, timedelta
from app import app, db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.responses.models import Response, Answer
from app.email_template.models import EmailTemplate
from app.events.models import Event, EventRole
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question
from app.utils.errors import FORBIDDEN
from app.organisation.models import Organisation


class EventsAPITest(ApiTestCase):

    def seed_static_data(self):
        self.test_user = self.add_user('something@email.com')
        self.add_organisation('Deep Learning Indaba',
                              'blah.png', 'blah_big.png', 'deeplearningindaba')
        test_country = Country('Indaba Land')
        db.session.add(test_country)
        db.session.commit()

        test_category = UserCategory('Category1')
        db.session.add(test_category)
        db.session.commit()

        self.test_user.verified_email = True
        db.session.add(self.test_user)
        db.session.commit()

        test_event = Event('Test Event', 'Event Description',
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                           'SPEEDNET', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning',
                           datetime.now(), datetime.now() + timedelta(days=30), datetime.now(), datetime.now(),
                           datetime.now(), datetime.now(), datetime.now(), datetime.now(),
                           datetime.now(), datetime.now())
        db.session.add(test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

        db.session.flush()

    def test_get_events_unauthed(self):
        self.seed_static_data()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Apply now'

    def test_get_events_applied(self):
        self.seed_static_data()

        test_response = Response(
            self.test_form.id, self.test_user.id, is_submitted=True)
        db.session.add(test_response)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Applied'

    def test_get_events_withdrawn(self):
        self.seed_static_data()

        test_response = Response(
            self.test_form.id, self.test_user.id, is_submitted=True, is_withdrawn=True)
        db.session.add(test_response)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application withdrawn'

    def test_get_events_closed(self):
        self.seed_static_data()

        self.test_form.event.application_close = datetime.now()
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application closed'

    def test_get_events_unauthed_closed(self):
        self.seed_static_data()

        self.test_form.event.application_close = datetime.now()
        db.session.commit()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application closed'

    def test_get_events_not_available(self):
        self.seed_static_data()

        db.session.delete(self.test_form)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application not available'

    def test_unsubmitted_response(self):
        self.seed_static_data()
        test_response = Response(
            self.test_form.id, self.test_user.id, is_submitted=False, is_withdrawn=False)
        db.session.add(test_response)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Continue application'

    def test_get_events_unauthed_not_available(self):
        self.seed_static_data()

        db.session.delete(self.test_form)
        db.session.commit()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application not available'


class EventsStatsAPITest(ApiTestCase):

    user_data_dict = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title': 'Mr',
        'nationality_country_id': 1,
        'residence_country_id': 1,
        'user_ethnicity': 'None',
        'user_gender': 'Male',
        'affiliation': 'University',
        'department': 'Computer Science',
        'user_disability': 'None',
        'user_category_id': 1,
        'user_primaryLanguage': 'Zulu',
        'user_dateOfBirth':  datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'password': 'abc'
    }

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba',
                              'blah.png', 'blah_big.png', 'deeplearningindaba')

        test_country = Country('Indaba Land')
        db.session.add(test_country)
        db.session.commit()

        test_category = UserCategory('Category1')
        db.session.add(test_category)
        db.session.commit()

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.test_user1 = json.loads(response.data)

        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.test_user2 = json.loads(response.data)

        self.test_event = Event('Test Event', 'Event Description',
                                datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                                'KONNET', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning',
                                datetime.now(), datetime.now() + timedelta(days=30), datetime.now(), datetime.now(),
                                datetime.now(), datetime.now(), datetime.now(), datetime.now(),
                                datetime.now(), datetime.now())
        db.session.add(self.test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            self.test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

        self.test_response = Response(
            self.test_form.id, self.test_user1['id'])
        db.session.add(self.test_response)
        db.session.commit()

        self.test_response2 = Response(
            self.test_form.id, self.test_user2['id'])
        self.test_response2.submit_response()
        db.session.add(self.test_response2)
        db.session.commit()

        self.user_role1 = EventRole(
            'admin', self.test_user1['id'], self.test_event.id)
        db.session.add(self.user_role1)
        db.session.commit()

        db.session.flush()

    def test_get_stats_forbidden(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/eventstats',
                                    headers={
                                        'Authorization': self.test_user2['token']},
                                    query_string={'event_id': self.test_event.id})
            self.assertEqual(response.status_code, 403)

    def test_event_id_required(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/eventstats',
                                    headers={
                                        'Authorization': self.test_user2['token']},
                                    query_string={'someparam': self.test_event.id})
            self.assertEqual(response.status_code, 400)

    def test_event_id_missing(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/eventstats',
                                    headers={
                                        'Authorization': self.test_user2['token']},
                                    query_string={'event_id': self.test_event.id + 100})
            self.assertEqual(response.status_code, 404)

    def test_event_stats_accurate(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/eventstats',
                                    headers={
                                        'Authorization': self.test_user1['token']},
                                    query_string={'event_id': self.test_event.id})
            data = json.loads(response.data)
            self.assertEqual(data['num_users'], 2)
            self.assertEqual(data['num_responses'], 2)
            self.assertEqual(data['num_submitted_responses'], 1)


class RemindersAPITest(ApiTestCase):
    def seed_static_data(self):
        inactive_user = self.add_user(
            'inactive@mail.co.za', 'inactive', post_create_fn=lambda u: u.deactivate())
        deleted_user = self.add_user(
            'deleted@mail.co.za', 'deleted', post_create_fn=lambda u: u.delete())

        event_admin = self.add_user('event@admin.co.za', 'event', 'admin')
        self.add_user('applicant@mail.co.za', 'applicant')
        self.add_user('notstarted@mail.co.za', 'notstarted')
        self.add_user('applicant2@mail.co.za', 'applicant')

        db.session.commit()
        self.add_organisation('Deep Learning Indaba',
                              'blah.png', 'blah_big.png', 'deeplearningindaba')
        country = Country('South Africa')
        db.session.add(country)

        user_category = UserCategory('Post Doc')
        db.session.add(user_category)

        event = Event('Indaba 2019', 'Deep Learning Indaba', datetime(2019, 8, 25), datetime(2019, 8, 31),
                      'COOLER', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning', datetime.now(), datetime.now(),
                      datetime.now(), datetime.now(), datetime.now(
        ), datetime.now(), datetime.now(), datetime.now(),
            datetime.now(), datetime.now())
        db.session.add(event)
        db.session.commit()

        email_templates = [
            EmailTemplate('application-not-submitted', None, ''),
            EmailTemplate('application-not-started', None, '')]
        db.session.add_all(email_templates)
        db.session.commit()

        event_role = EventRole('admin', event_admin.id, event.id)
        db.session.add(event_role)

        application_form = self.create_application_form(1, True, False)
        db.session.add(application_form)
        db.session.commit()

        responses = [
            Response(application_form.id, self.test_users[0].id, True),
            Response(application_form.id, self.test_users[1].id, False),
            Response(application_form.id, self.test_users[3].id, True, datetime.now(
            ), True, datetime.now()),
            Response(application_form.id, self.test_users[4].id, False),
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

    def test_not_submitted_reminder(self):
        self.seed_static_data()
        header = self.get_auth_header_for('event@admin.co.za')
        params = {'event_id': 1}

        response = self.app.post(
            '/api/v1/reminder-unsubmitted', headers=header, data=params)
        data = json.loads(response.data)
        LOGGER.warning(data)
        self.assertEqual(data['unsubmitted_responses'], 1)

    def test_not_started_reminder(self):
        self.seed_static_data()
        header = self.get_auth_header_for('event@admin.co.za')
        params = {'event_id': 1}

        response = self.app.post(
            '/api/v1/reminder-not-started', headers=header, data=params)
        data = json.loads(response.data)
        LOGGER.warning(data)
        self.assertEqual(data['not_started_responses'], 2)

    def test_non_event_admin_blocked_from_sending_reminders(self):
        self.seed_static_data()
        header = self.get_auth_header_for('applicant@mail.co.za')
        params = {'event_id': 1}

        response_unsubmitted = self.app.post(
            '/api/v1/reminder-unsubmitted', headers=header, data=params)
        response_not_started = self.app.post(
            '/api/v1/reminder-not-started', headers=header, data=params)

        self.assertEqual(response_unsubmitted.status_code, FORBIDDEN[1])
        self.assertEqual(response_not_started.status_code, FORBIDDEN[1])


class EventAPITest(ApiTestCase):

    test_event_data_dict = {
        'name': 'Test Event',
        'description': 'Test Event Description',
        'start_date': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'end_date': datetime(2020, 6, 6).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'key': 'testevent',
        'organisation_id': 1,
        'email_from': 'test@testindaba.com',
        'url': 'testindaba.com',
        'application_open': datetime(2020, 1, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'application_close': datetime(2020, 2, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'review_open': datetime(2020, 2, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'review_close': datetime(2020, 3, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'selection_open': datetime(2020, 3, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'selection_close': datetime(2020, 5, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'offer_open': datetime(2020, 5, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'offer_close': datetime(2020, 5, 30).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'registration_open': datetime(2020, 5, 30).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'registration_close': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    }

    def seed_static_data(self):
        self.add_organisation('Test Indaba', 'blah.png',
                              'blah_big.png', 'testindaba')

        test_country = Country('Test Land')
        db.session.add(test_country)
        db.session.commit()

        test_category = UserCategory('TestYear')
        db.session.add(test_category)
        db.session.commit()

        self.test_admin_user = AppUser(email='someoneadmin@email.com', firstname='Some',
                                       lastname='One', user_title='Mr', password='abc', organisation_id=1, is_admin=True)
        self.test_admin_user.verify()
        db.session.add(self.test_admin_user)
        db.session.commit()
        self.test_user = AppUser(email='someone@email.com', firstname='Some',
                                 lastname='One', user_title='Mr', password='abc', organisation_id=1)
        self.test_user.verify()
        db.session.add(self.test_user)
        db.session.commit()

        event = Event('Indaba 2019', 'Deep Learning Indaba', datetime(2019, 8, 25), datetime(2019, 8, 31),
                      'COOLER', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning', datetime.now(), datetime.now(),
                      datetime.now(), datetime.now(), datetime.now(
        ), datetime.now(), datetime.now(), datetime.now(),
            datetime.now(), datetime.now())
        db.session.add(event)
        db.session.commit()

        db.session.flush()

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        LOGGER.debug('here')
        return header

    def test_post_event_unauthed(self):
        self.seed_static_data()
        response = self.app.post(
            'api/v1/event', data=self.test_event_data_dict)
        assert response.status_code == 401

    def test_put_event_unauthed(self):
        self.seed_static_data()
        response = self.app.put('api/v1/event', data=self.test_event_data_dict)
        assert response.status_code == 401

    def test_post_event_not_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        assert response.status_code == 403

    def test_post_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        assert response.status_code == 201

    def test_post_event_eventrole_added(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        event_response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        event_data = json.loads(event_response.data)
        assert event_response.status_code == 201

        body = {
            'email': self.test_admin_user.email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        assert len(data['roles']) == 1
        for event_role in data['roles']:
            if event_role['event_id'] == event_data['id']:
                assert data['roles'][0]['role'] == 'admin'

    def test_put_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        # update(put) event
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = 'Test Event Updated'
        response = self.app.put(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['name'] == 'Test Event Updated'

    def test_put_event_not_admin(self):
        self.seed_static_data()

        # update(put) event by non-admin user
        # get auth header for non admin user
        header = self.get_auth_header_for(self.test_user.email)

        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = 'Test Event Updated'

        response = self.app.put(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        assert response.status_code == 403
