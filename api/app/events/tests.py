import json

from datetime import datetime, date, timedelta
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
from app.events.models import EventType
from app.outcome.models import Outcome
from app.outcome.models import Status as OutcomeStatus
from app.invitedGuest.models import InvitedGuest, GuestRegistration
import app.events.status as event_status
from app.registration.models import RegistrationForm, Offer, Registration

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

        test_event = self.add_event('Test Event', 'Event Description',
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                           'SPEEDNET', 1, 'abx@indaba.deeplearning')
        db.session.add(test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

        db.session.flush()

    def test_get_events_applied(self):
        self.seed_static_data()

        test_response = Response(self.test_form.id, self.test_user.id)
        test_response.submit()
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

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["description"], 'Event Description')
        self.assertEqual(data[0]["status"]['application_status'], 'Submitted')

    def test_get_events_withdrawn(self):
        self.seed_static_data()

        test_response = Response(self.test_form.id, self.test_user.id)
        test_response.withdraw()
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

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["description"], 'Event Description')
        self.assertEqual(data[0]["status"]['application_status'], 'Withdrawn')

    def test_unsubmitted_response(self):
        self.seed_static_data()
        test_response = Response(self.test_form.id, self.test_user.id)
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

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.test_user1 = json.loads(response.data)

        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.test_user2 = json.loads(response.data)

        self.test_event = self.add_event('Test Event', 'Event Description',
                                datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60),
                                'KONNET', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning',
                                datetime.now(), datetime.now() + timedelta(days=30))
        db.session.add(self.test_event)
        db.session.commit()

        self.test_form = self.create_application_form(
            self.test_event.id, True, False)
        db.session.add(self.test_form)
        db.session.commit()

        self.test_response = Response(self.test_form.id, self.test_user1['id'])
        db.session.add(self.test_response)
        db.session.commit()

        self.test_response2 = Response(self.test_form.id, self.test_user2['id'])
        self.test_response2.submit()
        db.session.add(self.test_response2)
        db.session.commit()

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

        event = self.add_event('Indaba 2019', 'Deep Learning Indaba', datetime(2019, 8, 25), datetime(2019, 8, 31),
                      'COOLER', 1, 'abx@indaba.deeplearning', 'indaba.deeplearning')
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

        submitted_response = Response(application_form.id, self.test_users[0].id)
        submitted_response.submit()
        withdrawn_response = Response(application_form.id, self.test_users[3].id)
        withdrawn_response.withdraw()
        responses = [
            submitted_response,
            Response(application_form.id, self.test_users[1].id),
            withdrawn_response,
            Response(application_form.id, self.test_users[4].id),
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
        'registration_close': datetime(2020, 6, 1).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'event_type':'EVENT'
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

        event = self.add_event('Indaba 2019', 'Deep Learning Indaba', datetime(2019, 8, 25), datetime(2019, 8, 31), 'COOLER')
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
        self.assertEqual(response.status_code, 401)

    def test_put_event_unauthed(self):
        self.seed_static_data()
        response = self.app.put('api/v1/event', data=self.test_event_data_dict)
        self.assertEqual(response.status_code, 401)

    def test_post_event_not_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        self.assertEqual(response.status_code, 403)

    def test_post_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        self.assertEqual(response.status_code, 201)

    def test_post_event_eventrole_added(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        event_response = self.app.post(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
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

    def test_put_event_is_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for(self.test_admin_user.email)
        # update(put) event
        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = 'Test Event Updated'
        response = self.app.put(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['name'], 'Test Event Updated')

    def test_put_event_not_admin(self):
        self.seed_static_data()

        # update(put) event by non-admin user
        # get auth header for non admin user
        header = self.get_auth_header_for(self.test_user.email)

        self.test_event_data_dict['id'] = 1
        self.test_event_data_dict['name'] = 'Test Event Updated'

        response = self.app.put(
            'api/v1/event', headers=header, data=self.test_event_data_dict)
        self.assertEqual(response.status_code, 403)


class EventStatusTest(ApiTestCase):
    def seed_static_data(self):
        self.event_admin = self.add_user('event@admin.co.za', 'event', 'admin')
        self.user1 = self.add_user('applicant@mail.co.za', 'applicant')
        self.user2 = self.add_user('applicant2@mail.co.za', 'applicant2')
        self.event = self.add_event()
        self.event2 = self.add_event('Second event', key='second_event')

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

        response = Response(self.application_form.id, self.user1.id)
        db.session.add(response)
        db.session.commit()

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
        response = Response(
            self.application_form.id, 
            self.user1.id)
        db.session.add(response)
        db.session.commit()

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
        response = Response(
            self.application_form.id, 
            self.user1.id)
        response.submit()
        db.session.add(response)
        db.session.commit()

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

        response = Response(
            self.application_form.id, 
            self.user1.id)
        response.submit()
        db.session.add(response)

        # Test pending offer
        offer = Offer(
            user_id=self.user1.id, 
            event_id=self.event.id, 
            offer_date=date.today(), 
            expiry_date=date.today() + timedelta(days=1),
            payment_required=False,
            travel_award=False,
            accommodation_award=False)
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

        response = Response(
            self.application_form.id, 
            self.user1.id)
        response.submit()
        db.session.add(response)

        offer = Offer(
            user_id=self.user1.id, 
            event_id=self.event.id, 
            offer_date=date.today(), 
            expiry_date=date.today() + timedelta(days=1),
            payment_required=False,
            travel_award=False,
            accommodation_award=False,
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
