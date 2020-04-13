import json
from datetime import date, datetime

import dateutil.parser
from flask import g

from app import app, db
from app.applicationModel.models import ApplicationForm, Question, Section
from app.email_template.models import EmailTemplate
from app.events.models import Event
from app.organisation.models import Organisation
from app.responses.models import Answer, Response
from app.responses.repository import ResponseRepository as response_repository
from app.users.models import AppUser, Country, UserCategory
from app.utils.testing import ApiTestCase


class ResponseApiTest(ApiTestCase):
    user_data_dict = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title': 'Mr',
        'password': '123456',
        'policy_agreed': True
    }

    def _seed_data(self):
        """Create dummy data for testing"""
        organisation = self.add_organisation(name='Deep Learning Indaba')
        test_country = self.add_country()
        test_category = self.add_category()

        email_templates = [
            EmailTemplate('withdrawal', None, ''),
            EmailTemplate('confirmation-response', None, '{question_answer_summary}')
        ]
        db.session.add_all(email_templates)
        db.session.commit()

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.user_data = json.loads(response.data)

        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.other_user_data = json.loads(response.data)

        self.add_n_users(10)

        self.test_event = self.add_event('Event Without Nomination')
        self.test_form = self.create_application_form(self.test_event.id, True)
        self.test_section = self.add_section(self.test_form.id)
        self.test_question = self.add_question(self.test_form.id, self.test_section.id, order=1)
        self.test_question2 = self.add_question(self.test_form.id, self.test_section.id, order=2)

        self.test_response = Response(self.test_form.id, self.other_user_data['id'])
        self.add_to_db(self.test_response)

        self.test_answer1 = Answer(
                self.test_response.id, self.test_question.id, 'My Answer')
        self.add_to_db(self.test_answer1)

        db.session.flush()

    def test_get_response_without_nomination(self):
        """Test a GET flow when the applications do not allow nominations"""
        
        self._seed_data()

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.other_user_data['token']},
                                query_string={'event_id': self.test_event.id})
        data = json.loads(response.data)

        self.assertEqual(data['application_form_id'], self.test_form.id)
        self.assertEqual(data['user_id'], self.other_user_data['id'])
        self.assertIsNone(data['submitted_timestamp'])
        self.assertFalse(data['is_withdrawn'])
        self.assertTrue(data['answers'])

        self.assertEqual(len(data['answers']), 1)
        answer = data['answers'][0]
        self.assertEqual(answer['id'], self.test_answer1.id)
        self.assertEqual(answer['value'], self.test_answer1.value)
        self.assertEqual(answer['question_id'], 1)

    def test_get_event(self):
        """Test that we get an error if we try to get a response for an event that doesn't exist."""

        self._seed_data()

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.other_user_data['token']
                                    },
                                query_string={'event_id': self.test_event.id + 100})

        self.assertEqual(response.status_code, 404)

    def test_get_missing_form(self):
        """Test that we get a 404 error if we try to get a response for an event with no application form."""
        
        self._seed_data()
        test_event2 = self.add_event('Test Event 2', 'Event Description', date(2019, 2, 24), 
                        date(2019, 3, 24), 'HOLLA', 2, 'mover@indaba.com', 'idb.com')

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.other_user_data['token']},
                                query_string={'event_id': test_event2.id})

        self.assertEqual(response.status_code, 404)

    def test_get_missing_response(self):
        """Test that we get a 404 error if there is no response for the event and user combination."""
        
        self._seed_data()

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.user_data['token']},
                                query_string={'event_id': self.test_event.id})

        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test a typical POST flow."""

        self._seed_data()
        response_data = {
            'application_form_id': self.test_form.id,
            'is_submitted': True,
            'answers': [
                {
                    'question_id': self.test_question.id,
                    'value': 'Answer 1'
                },
                {
                    'question_id': self.test_question2.id,
                    'value': 'Hello world, this is the 2nd answer.'
                }
            ]
        }

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']})

        self.assertEqual(response.status_code, 201)

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.user_data['token']},
                                query_string={'event_id': self.test_event.id})
        data = json.loads(response.data)

        self.assertEqual(data['application_form_id'], self.test_form.id)
        self.assertEqual(data['user_id'], self.user_data['id'])
        self.assertIsNotNone(data['submitted_timestamp'])
        self.assertFalse(data['is_withdrawn'])
        self.assertTrue(data['answers'])

        answer = data['answers'][0]
        self.assertEqual(answer['value'], 'Answer 1')
        self.assertEqual(answer['question_id'], self.test_question.id)

        answer = data['answers'][1]
        self.assertEqual(
            answer['value'], 'Hello world, this is the 2nd answer.')
        self.assertEqual(answer['question_id'], self.test_question2.id)

    def test_update(self):
        """Test a typical PUT flow."""

        self._seed_data()
        update_data = {
            'id': self.test_response.id,
            'application_form_id': self.test_form.id,
            'is_submitted': True,  # Set submitted
            'answers': [
                {
                    'question_id': self.test_question.id,
                    'value': 'Answer 1 UPDATED'  # Update an existing answer
                },
                {
                    'question_id': self.test_question2.id,  # Add a new answer
                    'value': 'This is the 2nd answer.'
                }
            ]
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']})

        self.assertEqual(response.status_code, 200)

        # Retrieve the response and check that the fields are as expected
        response = self.app.get(
            'api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.test_event.id})

        data = json.loads(response.data)

        self.assertEqual(data['application_form_id'], self.test_form.id)
        self.assertEqual(data['user_id'], self.other_user_data['id'])

        parsed_submitted = dateutil.parser.parse(
            data['submitted_timestamp'])
        self.assertLess(
            abs((datetime.now() - parsed_submitted).total_seconds()), 5*60)

        self.assertTrue(data['is_submitted'])
        self.assertFalse(data['is_withdrawn'])
        self.assertTrue(data['answers'])

        answer = data['answers'][0]
        self.assertEqual(answer['value'], 'Answer 1 UPDATED')
        self.assertEqual(answer['question_id'], self.test_question.id)

        answer = data['answers'][1]
        self.assertEqual(answer['value'], 'This is the 2nd answer.')
        self.assertEqual(answer['question_id'], self.test_question2.id)

    def test_update_missing(self):
        """Test that 404 is returned if we try to update a response that doesn't exist."""
        
        self._seed_data()
        update_data = {
            'id': self.test_response.id + 100,
            'application_form_id': self.test_form.id,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']})

        self.assertEqual(response.status_code, 404)

    def test_update_permission(self):
        """Test that a user can't update another user's response."""
        
        self._seed_data()
        update_data = {
            'id': self.test_response.id,
            'application_form_id': self.test_form.id,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']})

        self.assertEqual(response.status_code, 401)

    def test_update_conflict(self):
        """Test that we can't update the application form id for a response."""
        
        self._seed_data()
        update_data = {
            'id': self.test_response.id,
            'application_form_id': self.test_form.id + 100,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']})

        self.assertEqual(response.status_code, 409)

    def test_delete(self):
        """Test a typical DELETE flow."""
        
        self._seed_data()
        response = self.app.delete(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'id': self.test_response.id})

        self.assertEqual(response.status_code, 204)

        # We should still be able to get the response, but it is marked unsubmitted and withdrawn
        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.test_event.id})
        data = json.loads(response.data)
        self.assertFalse(data['is_submitted'])
        self.assertTrue(data['is_withdrawn'])

    def test_delete_missing(self):
        """Test that we can't delete a response that doesn't exist."""
        
        self._seed_data()
        response = self.app.delete(
                '/api/v1/response',
                headers={'Authorization': self.other_user_data['token']},
                query_string={'id': self.test_response.id + 1000})
        self.assertEqual(response.status_code, 404)  # Not found

    def test_delete_permission(self):
        """Test that we can't delete another user's response."""
        
        self._seed_data()

        # test_response belongs to "other_user", check that "user" can't delete it
        response = self.app.delete(
            '/api/v1/response',
            headers={'Authorization': self.user_data['token']},
            query_string={'id': self.test_response.id})

        self.assertEqual(response.status_code, 401)  # Unauthorized
