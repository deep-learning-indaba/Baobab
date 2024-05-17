import json
import warnings

from datetime import datetime, date, timedelta
from app import app, db, LOGGER
from app.events.models import Event, EventFee
from app.utils.testing import ApiTestCase
from app.responses.models import Response, Answer
from app.email_template.models import EmailTemplate
from app.events.models import Event, EventRole
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question
from app.utils.errors import FORBIDDEN, EVENT_NOT_FOUND, EVENT_FEE_NOT_FOUND
from app.organisation.models import Organisation
from app.events.models import EventType
from app.outcome.models import Outcome
from app.outcome.models import Status as OutcomeStatus
from app.invitedGuest.models import InvitedGuest, GuestRegistration
import app.events.status as event_status
from app.registration.models import Registration
from app.offer.models import Offer

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

        test_event = self.add_event({'en': 'Test Event'}, {'en': 'Event Description'},
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                           'SPEEDNET', 1, 'abx@indaba.deeplearning')
        db.session.add(test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

    def test_get_events_applied(self):
        self.seed_static_data()

        self.add_response(self.test_form.id, self.test_user.id, is_submitted=True)

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events',
            headers={'Authorization': data["token"]},
            query_string={'language': 'en'}
        )
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["description"], 'Event Description')
        self.assertEqual(data[0]["status"]['application_status'], 'Submitted')

    def test_get_events_withdrawn(self):
        self.seed_static_data()

        self.add_response(self.test_form.id, self.test_user.id, is_withdrawn=True)

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events',
            headers={'Authorization': data["token"]},
            query_string={'language': 'en'}
        )
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["description"], 'Event Description')
        self.assertEqual(data[0]["status"]['application_status'], 'Withdrawn')

    def test_unsubmitted_response(self):
        self.seed_static_data()
        self.add_response(self.test_form.id, self.test_user.id)

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': 'abc'
        })

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events',
            headers={'Authorization': data["token"]},
            query_string={'language': 'en'})
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["description"], 'Event Description')
        self.assertEqual(data[0]["status"]['application_status'], 'Not Submitted')

    def test_get_event_type(self):
        self.seed_static_data()
        db.session.delete(self.test_form)
        db.session.commit()

        response = self.app.get('/api/v1/events')
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_past_event_offer_accepted(self):
        """API should return past events that user had an accepted offer for."""
        self.seed_static_data()

        past_event = self.add_event(start_date=datetime.now() - timedelta(days=30), 
                       end_date=datetime.now() - timedelta(days=30),
                       key='PAST12')
        self.add_offer(self.test_user.id, past_event.id, candidate_response=True)
        
        response = self.app.get(
            '/api/v1/events',
            headers=self.get_auth_header_for('something@email.com'),
            query_string={'language': 'en'})
        data = json.loads(response.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["event_type"], 'EVENT')
        self.assertTrue(data[1]["status"]['is_event_attendee'])
        
    def test_past_event_offer_rejected(self):
        """API should not return past events where the user rejected an offer."""
        self.seed_static_data()

        past_event = self.add_event(start_date=datetime.now() - timedelta(days=30), 
                       end_date=datetime.now() - timedelta(days=30),
                       key='PAST12')
        self.add_offer(self.test_user.id, past_event.id, candidate_response=False)
        
        response = self.app.get(
            '/api/v1/events',
            headers=self.get_auth_header_for('something@email.com'),
            query_string={'language': 'en'})
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["event_type"], 'EVENT')

    def test_past_event_guest(self):
        """API should return past events where user was an invited guest."""
        self.seed_static_data()

        past_event = self.add_event(start_date=datetime.now() - timedelta(days=30), 
                       end_date=datetime.now() - timedelta(days=30),
                       key='PAST12')
        self.add_invited_guest(self.test_user.id, past_event.id)
        
        response = self.app.get(
            '/api/v1/events',
            headers=self.get_auth_header_for('something@email.com'),
            query_string={'language': 'en'})
        data = json.loads(response.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["event_type"], 'EVENT')
        self.assertTrue(data[1]["status"]['is_event_attendee'])

    def test_past_event_non_attendee(self):
        """API should not return past events where the user was not an attendee."""
        self.seed_static_data()

        past_event1 = self.add_event(start_date=datetime.now() - timedelta(days=30), 
                       end_date=datetime.now() - timedelta(days=30),
                       key='PAST1')

        past_event2 = self.add_event(start_date=datetime.now() - timedelta(days=30), 
                       end_date=datetime.now() - timedelta(days=30),
                       key='PAST2')

        # Add a different user who attended these events
        other_user = self.add_user(email='other@user.com')
        self.add_invited_guest(other_user.id, event_id=past_event1.id)
        self.add_offer(other_user.id, event_id=past_event2.id, candidate_response=True)
        
        response = self.app.get(
            '/api/v1/events',
            headers=self.get_auth_header_for('something@email.com'),
            query_string={'language': 'en'})
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["event_type"], 'EVENT')


class EventsStatsAPITest(ApiTestCase):

    user_data_dict = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title': 'Mr',
        'password': 'abc',
        'policy_agreed': True,
        'language': 'en'
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

        self.add_email_template('verify-email')

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.test_user1 = json.loads(response.data)

        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.test_user2 = json.loads(response.data)

        self.test_event = self.add_event({'en': 'Test Event'}, {'en': 'Event Description'},
                                datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                                'KONNET', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning',
                                datetime.now(), datetime.now() + timedelta(days=30))
        db.session.add(self.test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            self.test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

        self.test_response = self.add_response(self.test_form.id, self.test_user1['id'])
        self.test_response2 = self.add_response(self.test_form.id, self.test_user2['id'], is_submitted=True)

        self.user_role1 = EventRole(
            'admin', self.test_user1['id'], self.test_event.id)
        db.session.add(self.user_role1)
        db.session.commit()

        db.session.flush()

    def test_get_stats_forbidden(self):
        self.seed_static_data()
        response = self.app.get('/api/v1/eventstats',
                                headers={
                                    'Authorization': self.test_user2['token']},
                                query_string={'event_id': self.test_event.id})
        self.assertEqual(response.status_code, 403)

    def test_event_id_required(self):
        self.seed_static_data()
        response = self.app.get('/api/v1/eventstats',
                                headers={
                                    'Authorization': self.test_user2['token']},
                                query_string={'someparam': self.test_event.id})
        self.assertEqual(response.status_code, 400)


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

        event = self.add_event(
            {'en': 'Indaba 2019'}, {'en': 'Deep Learning Indaba'}, 
            datetime(2019, 8, 25), datetime(2019, 8, 31),
            'COOLER', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning'
        )
        db.session.add(event)
        db.session.commit()

        email_templates = [
            EmailTemplate('application-not-submitted', None, 'Application Not Submitted', '', 'en'),
            EmailTemplate('application-not-started', None, 'Application Not Started', '', 'en')]
        db.session.add_all(email_templates)
        db.session.commit()

        event_role = EventRole('admin', event_admin.id, event.id)
        db.session.add(event_role)

        application_form = self.create_application_form(1, True, False)
        db.session.add(application_form)
        db.session.commit()

        submitted_response = self.add_response(application_form.id, self.test_users[0].id, is_submitted=True)
        withdrawn_response = self.add_response(application_form.id, self.test_users[3].id, is_withdrawn=True)
        self.add_response(application_form.id, self.test_users[1].id)
        self.add_response(application_form.id, self.test_users[4].id)

        self.add_email_template('application-not-submitted')
        self.add_email_template('application-not-started')

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
        'name': {
            'en': 'Test Event',
            'fr': 'evenement de test'
        },
        'description': {
            'en': 'Test Event Description',
            'fr': "Description de l'evenement de test"
        },
        'start_date': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end_date': datetime(2020, 6, 6).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'key': 'testevent',
        'organisation_id': 1,
        'email_from': 'test@testindaba.com',
        'url': 'testindaba.com',
        'application_open': datetime(2020, 1, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'application_close': datetime(2020, 2, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'review_open': datetime(2020, 2, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'review_close': datetime(2020, 3, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'selection_open': datetime(2020, 3, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'selection_close': datetime(2020, 5, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'offer_open': datetime(2020, 5, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'offer_close': datetime(2020, 5, 30).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'registration_open': datetime(2020, 5, 30).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'registration_close': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'event_type':'EVENT',
        'travel_grant': False
    }
    
    test_journal_data_dict = {
        'name': {
            'en': 'Test Journal',
            'fr': 'evenement de test'
        },
        'description': {
            'en': 'Test Journal Description',
            'fr': "Description de l'evenement de test"
        },
        'start_date': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end_date': None,
        'key': 'testjournalevent',
        'organisation_id': 1,
        'email_from': 'test@testindaba.com',
        'url': 'testindaba.com',
        'application_open': None,
        'application_close': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'review_open': None,
        'review_close': None,
        'selection_open': None,
        'selection_close': None,
        'offer_open': None,
        'offer_close': None,
        'registration_open': None,
        'registration_close': None,
        'event_type':'JOURNAL',
        'travel_grant': False
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

        event = self.add_event({'en': 'Indaba 2019'}, {'en': 'Deep Learning Indaba'}, datetime(2019, 8, 25), datetime(2019, 8, 31), 'COOLER')
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
        return header

    def test_post_event_unauthed(self):
        self.seed_static_data()
        response = self.app.post(
            'api/v1/event',
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_put_event_unauthed(self):
        self.seed_static_data()
        response = self.app.put(
            'api/v1/event',
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_post_event_not_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.post(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_post_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        response = self.app.post(
            'api/v1/event',
            headers=header, 
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data['name']), 2)
        self.assertEqual(len(data['description']), 2)
        self.assertEqual(data['name']['en'], 'Test Event')
        self.assertEqual(data['name']['fr'], 'evenement de test')
        self.assertEqual(data['description']['en'], 'Test Event Description')
        self.assertEqual(data['description']['fr'], "Description de l'evenement de test")


    def test_post_event_eventrole_added(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        event_response = self.app.post(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        event_data = json.loads(event_response.data)
        self.assertEqual(event_response.status_code, 201)

        body = {
            'email': self.test_admin_user.email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        self.assertEqual(len(data['roles']), 1)
        for event_role in data['roles']:
            if event_role['event_id'] == event_data['id']:
                self.assertEqual(data['roles'][0]['role'], 'admin')
                
    def test_post_event_missing_date(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        current_end = self.test_event_data_dict['end_date']
        self.test_event_data_dict['end_date'] = None
        response = self.app.post(
            'api/v1/event',
            headers=header, 
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.test_event_data_dict['end_date'] = current_end
        self.assertEqual(response.status_code, 400)
        
    def test_post_event_journal(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        response = self.app.post(
            'api/v1/event',
            headers=header, 
            data=json.dumps(self.test_journal_data_dict),
            content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['end_date'], None)
        self.assertEqual(data['application_open'], None)
        self.assertEqual(data['application_close'], None)
        self.assertEqual(data['review_open'], None)
        self.assertEqual(data['review_close'], None)
        self.assertEqual(data['selection_open'], None)
        self.assertEqual(data['selection_close'], None)
        self.assertEqual(data['offer_open'], None)
        self.assertEqual(data['offer_close'], None)
        self.assertEqual(data['registration_open'], None)
        self.assertEqual(data['registration_close'], None)

    def test_put_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        # update(put) event
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = {'en': 'Test Event Name Updated'}
        self.test_event_data_dict['description'] = {'en': 'Test Event Description Updated'}
        response = self.app.put(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['name']), 1)
        self.assertEqual(len(data['description']), 1)
        self.assertEqual(data['name']['en'], 'Test Event Name Updated')
        self.assertEqual(data['description']['en'], 'Test Event Description Updated')

    def test_put_event_not_admin(self):
        self.seed_static_data()

        # update(put) event by non-admin user
        # get auth header for non admin user
        header = self.get_auth_header_for(self.test_user.email)

        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = {'en': 'Test Event Updated'}
        self.test_event_data_dict['description'] = {'en': 'Test Event Description Updated'}

        response = self.app.put(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.assertEqual(response.status_code, 403)
    
    def test_post_event_must_contain_translation(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        self.test_event_data_dict['name'] = {}
        self.test_event_data_dict['description'] = {}

        response = self.app.post(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_event_translation_mismatch(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        self.test_event_data_dict['name'] = {'en': 'English Translation'}
        self.test_event_data_dict['description'] = {'fr': 'French Translation'}

        response = self.app.post(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_put_event_must_contain_translation(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = {}
        self.test_event_data_dict['description'] = {}

        response = self.app.put(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_put_event_must_contain_translation(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = {'en': 'English Translation'}
        self.test_event_data_dict['description'] = {'fr': 'French Translation'}

        response = self.app.put(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        
    def test_put_event_journal(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        # update(put) event
        self.test_journal_data_dict['id'] = 2
        self.test_journal_data_dict['name'] = {'en': 'Test Journal'}
        self.test_journal_data_dict['description'] = {'en': 'Test Journal Description'}
        self.test_journal_data_dict['end_date'] = datetime(2020, 1, 1).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        response = self.app.post(
            'api/v1/event',
            headers=header, 
            data=json.dumps(self.test_journal_data_dict),
            content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        
        response = self.app.put(
            'api/v1/event',
            headers=header,
            data=json.dumps(self.test_journal_data_dict),
            content_type='application/json')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['end_date'], None)
        self.assertEqual(data['application_open'], None)
        self.assertEqual(data['application_close'], None)
        self.assertEqual(data['review_open'], None)
        self.assertEqual(data['review_close'], None)
        self.assertEqual(data['selection_open'], None)
        self.assertEqual(data['selection_close'], None)
        self.assertEqual(data['offer_open'], None)
        self.assertEqual(data['offer_close'], None)
        self.assertEqual(data['registration_open'], None)
        self.assertEqual(data['registration_close'], None)
        
    def test_put_event_missing_date(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = {'en': 'Update Test Continuous Journal'}
        self.test_event_data_dict['description'] = {'en': 'Update Test Continuous Journal Description'}
        self.test_event_data_dict['end_date'] = None
        response = self.app.post(
            'api/v1/event',
            headers=header, 
            data=json.dumps(self.test_event_data_dict),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)


class EventStatusTest(ApiTestCase):
    def seed_static_data(self):
        self.event_admin = self.add_user('event@admin.co.za', 'event', 'admin')
        self.user1 = self.add_user('applicant@mail.co.za', 'applicant')
        self.user2 = self.add_user('applicant2@mail.co.za', 'applicant2')
        self.event = self.add_event()
        self.event2 = self.add_event({'en': 'Second event'}, key='second_event')

        self.application_form = self.create_application_form()

        self.registration_form = self.create_registration_form(self.event.id) 
        db.session.add(self.registration_form)
        db.session.commit()


    def test_invited_guest_unregistered(self):
        """Check that un-registred invited guest statuses are correct."""
        self.seed_static_data()
        invited = InvitedGuest(event_id=self.event.id, user_id=self.user1.id, role='Mentor')
        db.session.add(invited)
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.invited_guest, 'Mentor')
        self.assertIsNone(status.registration_status)
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        # Check no interference with other user and other event
        status = event_status.get_event_status(self.event.id, self.user2.id)
        self.assertIsNone(status.invited_guest)

        status = event_status.get_event_status(self.event2.id, self.user1.id)
        self.assertIsNone(status.invited_guest)

    def test_registered_invited_guest(self):
        """Check that statuses are correct for a registered invited guest."""
        self.seed_static_data()
        invited = InvitedGuest(event_id=self.event.id, user_id=self.user1.id, role='Mentor')
        db.session.add(invited)

        # Check un-confirmed guest registration
        guest_registration = GuestRegistration(
            user_id=self.user1.id, 
            registration_form_id=self.registration_form.id,
            confirmed=False)

        db.session.add(guest_registration)
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.invited_guest, 'Mentor')
        self.assertEqual(status.registration_status, 'Not Confirmed')
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        # Check confirmed guest registration
        guest_registration.confirm(datetime.now())
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.invited_guest, 'Mentor')
        self.assertEqual(status.registration_status, 'Confirmed')
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

    def test_invited_guest_and_applied(self):
        """Check invited guest status when the user also applied."""
        self.seed_static_data()
        invited = InvitedGuest(event_id=self.event.id, user_id=self.user1.id, role='Mentor')
        db.session.add(invited)

        self.add_response(self.application_form.id, self.user1.id)

        status = event_status.get_event_status(self.event.id, self.user1.id)

        self.assertEqual(status.invited_guest, 'Mentor')
        self.assertIsNone(status.registration_status)
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

    def test_applied(self):
        """Test statuses when the user has applied."""
        self.seed_static_data()
        # Candidate has not submitted or withdrawn
        response = self.add_response(self.application_form.id, self.user1.id)

        status = event_status.get_event_status(self.event.id, self.user1.id)

        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Not Submitted')
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        # Submitted
        response.submit()
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)

        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Submitted')
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        # Withdrawn
        response.withdraw()
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)

        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Withdrawn')
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        status = event_status.get_event_status(self.event.id, self.user2.id)
        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

        status = event_status.get_event_status(self.event2.id, self.user1.id)
        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertIsNone(status.application_status)
        self.assertIsNone(status.outcome_status)
        self.assertIsNone(status.offer_status)

    def test_outcome(self):
        """Check statuses when the user has an outcome."""
        self.seed_static_data()

        # Check that status is invalid if there is an outcome with not application (response)
        outcome = Outcome(self.event.id, self.user1.id, OutcomeStatus.ACCEPTED, self.user2.id)
        db.session.add(outcome)

        with self.assertRaises(ValueError):
            event_status.get_event_status(self.event.id, self.user1.id)
        
        # Check status when user has applied and has an outcome
        self.add_response(self.application_form.id, self.user1.id, is_submitted=True)

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Submitted')
        self.assertEqual(status.outcome_status, outcome.status.name)
        self.assertIsNone(status.offer_status)

    def test_offer(self):
        """Test statuses when offer."""
        self.seed_static_data()

        outcome = Outcome(self.event.id, self.user1.id, OutcomeStatus.ACCEPTED, self.user2.id)
        db.session.add(outcome)

        self.add_response(self.application_form.id, self.user1.id, is_submitted=True)

        # Test pending offer
        offer = Offer(
            user_id=self.user1.id, 
            event_id=self.event.id, 
            offer_date=date.today(), 
            expiry_date=date.today() + timedelta(days=1),
            payment_required=False)
        db.session.add(offer)
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Submitted')
        self.assertEqual(status.outcome_status, outcome.status.name)
        self.assertEqual(status.offer_status, 'Pending')

        # Test accepted offer
        offer.candidate_response = True
        db.session.commit()
        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertIsNone(status.invited_guest)
        self.assertIsNone(status.registration_status)
        self.assertEqual(status.application_status, 'Submitted')
        self.assertEqual(status.outcome_status, outcome.status.name)
        self.assertEqual(status.offer_status, 'Accepted')

        # Should still be accepted when past the expiry date
        offer.expiry_date = date.today() - timedelta(days=2)
        db.session.commit()
        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.offer_status, 'Accepted')

        # Test expired offer
        offer.candidate_response = None
        db.session.commit()
        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.offer_status, 'Expired')

        # Test rejected offer
        offer.candidate_response = False
        db.session.commit()
        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.offer_status, 'Rejected')

    def test_registered(self):
        """Test statusess for registered attendees."""
        self.seed_static_data()

        outcome = Outcome(self.event.id, self.user1.id, OutcomeStatus.ACCEPTED, self.user2.id)
        db.session.add(outcome)

        self.add_response(self.application_form.id, self.user1.id, is_submitted=True)

        offer = Offer(
            user_id=self.user1.id, 
            event_id=self.event.id, 
            offer_date=date.today(), 
            expiry_date=date.today() + timedelta(days=1),
            payment_required=False,
            candidate_response=True)
        db.session.add(offer)
        db.session.commit()

        registration = Registration(offer.id, self.registration_form.id)
        db.session.add(registration)
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertIsNone(status.invited_guest)
        self.assertEqual(status.registration_status, 'Not Confirmed')
        self.assertEqual(status.application_status, 'Submitted')
        self.assertEqual(status.outcome_status, outcome.status.name)
        self.assertEqual(status.offer_status, 'Accepted')

        registration.confirm()
        db.session.commit()

        status = event_status.get_event_status(self.event.id, self.user1.id)
        self.assertEqual(status.registration_status, 'Confirmed')

class EventFeeAPITest(ApiTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "/api/v1/eventfee"
        
        # we don't mind this since this warning is specific to sqlite
        warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively")

    def seed_static_data(self):
        self.event = self.add_event()

        self.treasurer_email = "treasurer@user.com"
        self.treasurer = self.add_user(self.treasurer_email)
        self.add_event_role("treasurer", self.treasurer.id, self.event.id)
     
    def test_get_event_fee_not_found(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.treasurer.email)

        params = {'event_id': 2}
        response = self.app.get(self.url, headers=header, data=params)
        
        self.assertEqual(response.status_code, EVENT_NOT_FOUND[1])

    def test_get_event_fee_without_being_treasurer(self):
        self.seed_static_data()
        applicant = self.add_user("applicant@user.com")
        header = self.get_auth_header_for(applicant.email)

        params = {'event_id': 1}
        response = self.app.get(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_get_event_fee_success(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.treasurer_email)
        self.add_event_fee(1, 1, "Registration", amount=250.00, description="Fee to attend")
        self.add_event_fee(1, 1, "Accommodation", amount=100.00, description="Fee for 1 bed")
        self.add_event(key="EEML")
        self.add_event_fee(2, 1, "Flights")

        params = {'event_id': 1}
        response = self.app.get(self.url, headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        
        self.assertEqual(data[0]['name'], "Registration")
        self.assertEqual(data[0]['description'], "Fee to attend")
        self.assertEqual(data[0]['iso_currency_code'], 'usd')
        self.assertEqual(data[0]['amount'], 250.00)
        self.assertEqual(data[0]['is_active'], True)
        self.assertEqual(data[0]['created_by_user_id'], 1)
        self.assertEqual(data[0]['created_by'], 'User Lastname')
        self.assertIsNotNone(data[0]['created_at'])
        self.assertIsNone(data[0]['updated_by_user_id'])
        self.assertIsNone(data[0]['updated_by'])
        self.assertIsNone(data[0]['updated_at'])

        self.assertEqual(data[1]['name'], "Accommodation")
        self.assertEqual(data[1]['description'], "Fee for 1 bed")
        self.assertEqual(data[1]['iso_currency_code'], 'usd')
        self.assertEqual(data[1]['amount'], 100.00)
        self.assertEqual(data[1]['is_active'], True)
        self.assertEqual(data[1]['created_by_user_id'], 1)
        self.assertEqual(data[1]['created_by'], 'User Lastname')
        self.assertIsNotNone(data[1]['created_at'])
        self.assertIsNone(data[1]['updated_by_user_id'])
        self.assertIsNone(data[1]['updated_by'])
        self.assertIsNone(data[1]['updated_at'])

    def test_post_event_fee_not_found(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.treasurer.email)

        params = {
            'event_id': 42,
            'name': 'Registration',
            'amount': 199.99,
            'description': 'Fee to attend'
        }
        response = self.app.post(self.url, headers=header, data=params)
        
        self.assertEqual(response.status_code, EVENT_NOT_FOUND[1])

    def test_post_event_fee_without_being_treasurer(self):
        self.seed_static_data()
        applicant = self.add_user("applicant@user.com")
        header = self.get_auth_header_for(applicant.email)

        params = {
            'event_id': 1,
            'name': 'Registration',
            'amount': 199.99,
            'description': 'Fee to attend'
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_post_event_fee_without_stripe_setup(self):
        self.seed_static_data()
        organisaton = db.session.query(Organisation).get(self.dummy_org_id)
        organisaton.iso_currency_code = None
        db.session.merge(organisaton)
        db.session.commit()
        header = self.get_auth_header_for(self.treasurer_email)

        params = {
            'event_id': 1,
            'name': 'Registration',
            'amount': 199.99,
            'description': 'Fee to attend'
        }
        response = self.app.post(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, 400)

    def test_post_event_fee_success(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.treasurer_email)

        params = {
            'event_id': 1,
            'name': 'Registration',
            'amount': 199.99,
            'description': 'Fee to attend'
        }
        response = self.app.post(self.url, headers=header, data=params)
        
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['name'], "Registration")
        self.assertEqual(data['description'], "Fee to attend")
        self.assertEqual(data['iso_currency_code'], 'usd')
        self.assertEqual(data['amount'], 199.99)
        self.assertEqual(data['is_active'], True)
        self.assertEqual(data['created_by_user_id'], 1)
        self.assertEqual(data['created_by'], 'User Lastname')
        self.assertIsNotNone(data['created_at'])
        self.assertIsNone(data['updated_by_user_id'])
        self.assertIsNone(data['updated_by'])
        self.assertIsNone(data['updated_at'])

    def test_delete_event_fee_not_found(self):
        self.seed_static_data()
        self.add_event_fee(1, 1)
        self.add_event(key="EEML")
        self.add_event_fee(2, 1)
        header = self.get_auth_header_for(self.treasurer_email)

        params={'event_id': 1, 'event_fee_id': 2}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, EVENT_FEE_NOT_FOUND[1])

    def test_delete_event_fee_without_being_treasurer(self):
        self.seed_static_data()
        applicant = self.add_user("applicant@user.com")
        self.add_event_fee(1, 1)
        header = self.get_auth_header_for(applicant.email)

        params = {'event_id': 1, 'event_fee_id': 1}
        response = self.app.delete(self.url, headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_delete_fee_success(self):
        self.seed_static_data()
        self.add_event_fee(1, 1)
        header = self.get_auth_header_for(self.treasurer_email)

        params = {'event_id': 1, 'event_fee_id': 1}
        response = self.app.delete(self.url, headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(data['is_active'], False)
        self.assertEqual(data['updated_by_user_id'], 1)
        self.assertEqual(data['updated_by'], 'User Lastname')
        self.assertIsNotNone(data['updated_at'])