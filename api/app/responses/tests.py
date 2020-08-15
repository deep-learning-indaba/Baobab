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
        'policy_agreed': True,
        'language': 'en'
    }

    def _seed_data(self):
        """Create dummy data for testing"""
        organisation = self.add_organisation(name='Deep Learning Indaba')
        test_country = self.add_country()
        test_category = self.add_category()

        email_templates = [
            EmailTemplate('withdrawal', None, 'Withdrawal', '', 'en'),
            EmailTemplate('confirmation-response', None, 'Confirmation', '{question_answer_summary}', 'en')
        ]
        db.session.add_all(email_templates)
        db.session.commit()

        self.add_email_template('verify-email')

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.user_data = json.loads(response.data)

        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.other_user_data = json.loads(response.data)

        self.add_n_users(10)

        self.event = self.add_event({'en': 'Event Without Nomination'}, key='indaba-2025')
        self.form = self.create_application_form(self.event.id, True, False)
        self.section = self.add_section(self.form.id)
        self.question = self.add_question(self.form.id, self.section.id, order=1)
        self.question2 = self.add_question(self.form.id, self.section.id, order=2)
        self.response = self.add_response(self.form.id, self.other_user_data['id'], False, False)
        self.answer1 = self.add_answer(self.response.id, self.question.id, 'My Answer')

        self.event_with_nomination = self.add_event({'en': 'Event With Nomination'}, key='eeml-2025')
        self.form_with_nomination = self.create_application_form(self.event_with_nomination.id, True, True)
        self.section_with_nomination = self.add_section(self.event_with_nomination.id)
        self.question1_with_nomination = self.add_question(self.form_with_nomination.id, self.section_with_nomination.id, order=1)
        self.question2_with_nomination = self.add_question(self.form_with_nomination.id, self.section_with_nomination.id, order=2)
        self.response1_with_nomination = self.add_response(self.form_with_nomination.id, self.other_user_data['id'], True, False)
        self.answer2_with_nomination = self.add_answer(self.response1_with_nomination.id, self.question2_with_nomination.id, 'Second nomination answer')
        self.answer1_with_nomination = self.add_answer(self.response1_with_nomination.id, self.question1_with_nomination.id, 'Another answer')
        self.response2_with_nomination = self.add_response(self.form_with_nomination.id, self.other_user_data['id'], False, True)
        self.answer4_with_nomination = self.add_answer(self.response2_with_nomination.id, self.question2_with_nomination.id, 'Second answer for second nomination')
        self.answer3_with_nomination = self.add_answer(self.response2_with_nomination.id, self.question1_with_nomination.id, 'First answer for second nomination')

        db.session.flush()

    def test_get_response_without_nomination(self):
        """Test a GET flow when the applications do not allow nominations"""
        
        self._seed_data()

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.other_user_data['token']},
                                query_string={'event_id': self.event.id})
        data = json.loads(response.data)

        self.assertEqual(len(data), 1)
        data = data[0]
        self.assertEqual(data['application_form_id'], self.form.id)
        self.assertEqual(data['user_id'], self.other_user_data['id'])
        self.assertFalse(data['is_submitted'])
        self.assertIsNone(data['submitted_timestamp'])
        self.assertFalse(data['is_withdrawn'])
        self.assertIsNone(data['withdrawn_timestamp'])
        self.assertIsNotNone(data['started_timestamp'])
        self.assertTrue(data['answers'])
        self.assertEqual(data['language'], 'en')

        self.assertEqual(len(data['answers']), 1)
        answer = data['answers'][0]
        self.assertEqual(answer['id'], self.answer1.id)
        self.assertEqual(answer['value'], self.answer1.value)
        self.assertEqual(answer['question_id'], 1)

    def test_get_response_with_nomination(self):
        """Test a GET flow when the applications do allow nominations"""

        self._seed_data()
        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.event_with_nomination.id}
        )
        data = json.loads(response.data)

        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['application_form_id'], self.form_with_nomination.id)
        self.assertEqual(data[0]['user_id'], self.other_user_data['id'])
        self.assertIsNotNone(data[0]['submitted_timestamp'])
        self.assertTrue(data[0]['is_submitted'])
        self.assertIsNone(data[0]['withdrawn_timestamp'])
        self.assertFalse(data[0]['is_withdrawn'])
        self.assertIsNotNone(data[0]['started_timestamp'])
        self.assertEqual(len(data[0]['answers']), 2)
        answer1 = data[0]['answers'][0]
        self.assertEqual(answer1['id'], self.answer1_with_nomination.id)
        self.assertEqual(answer1['value'], self.answer1_with_nomination.value)
        self.assertEqual(answer1['question_id'], self.answer1_with_nomination.question_id)
        answer2 = data[0]['answers'][1]
        self.assertEqual(answer2['id'], self.answer2_with_nomination.id)
        self.assertEqual(answer2['value'], self.answer2_with_nomination.value)
        self.assertEqual(answer2['question_id'], self.answer2_with_nomination.question_id)

        self.assertEqual(data[1]['application_form_id'], self.form_with_nomination.id)
        self.assertEqual(data[1]['user_id'], self.other_user_data['id'])
        self.assertIsNone(data[1]['submitted_timestamp'])
        self.assertFalse(data[1]['is_submitted'])
        self.assertIsNotNone(data[1]['withdrawn_timestamp'])
        self.assertTrue(data[1]['is_withdrawn'])
        self.assertIsNotNone(data[1]['started_timestamp'])
        self.assertEqual(len(data[1]['answers']), 2)
        answer3 = data[1]['answers'][0]
        self.assertEqual(answer3['id'], self.answer3_with_nomination.id)
        self.assertEqual(answer3['value'], self.answer3_with_nomination.value)
        self.assertEqual(answer3['question_id'], self.answer3_with_nomination.question_id)
        answer4 = data[1]['answers'][1]
        self.assertEqual(answer4['id'], self.answer4_with_nomination.id)
        self.assertEqual(answer4['value'], self.answer4_with_nomination.value)
        self.assertEqual(answer4['question_id'], self.answer4_with_nomination.question_id)

    def test_get_event(self):
        """Test that we get an error if we try to get a response for an event that doesn't exist."""

        self._seed_data()

        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.event.id + 100}
        )

        self.assertEqual(response.status_code, 404)

    def test_get_missing_form(self):
        """Test that we get a 404 error if we try to get a response for an event with no application form."""
        
        self._seed_data()
        test_event2 = self.add_event({'en': 'Test Event 2'}, key='HOLLA')

        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': test_event2.id}
        )

        self.assertEqual(response.status_code, 404)

    def test_get_missing_response(self):
        """Test that we get an empty list if there is no response for the event and user combination."""
        
        self._seed_data()

        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.user_data['token']},
            query_string={'event_id': self.event.id}
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data)  # Check for empty list

    def test_post_without_nomination(self):
        """Test a typical POST flow."""

        self._seed_data()
        response_data = {
            'application_form_id': self.form.id,
            'is_submitted': True,
            'answers': [
                {
                    'question_id': self.question.id,
                    'value': 'Answer 1'
                },
                {
                    'question_id': self.question2.id,
                    'value': 'Hello world, this is the 2nd answer.'
                }
            ]
        }

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']},
            query_string={'language': 'en'})
        
        self.assertEqual(response.status_code, 201)

        data = json.loads(response.data)

        self.assertEqual(data['application_form_id'], self.form.id)
        self.assertEqual(data['user_id'], self.user_data['id'])
        self.assertIsNotNone(data['submitted_timestamp'])
        self.assertTrue(data['is_submitted'])
        self.assertFalse(data['is_withdrawn'])
        self.assertIsNone(data['withdrawn_timestamp'])
        self.assertEqual(len(data['answers']), 2)
        self.assertEqual(data['language'], 'en')

        answer = data['answers'][0]
        self.assertEqual(answer['value'], 'Answer 1')
        self.assertEqual(answer['question_id'], self.question.id)

        answer = data['answers'][1]
        self.assertEqual(
            answer['value'], 'Hello world, this is the 2nd answer.')
        self.assertEqual(answer['question_id'], self.question2.id)

    def test_second_response_rejected_without_nomination(self):
        self._seed_data()
        response_data = {
            'application_form_id': self.form.id,
            'is_submitted': True,
            'answers': [
                {
                    'question_id': self.question.id,
                    'value': 'Answer 1'
                }
            ]
        }

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']},
            query_string={'language': 'en'})
        
        self.assertEqual(response.status_code, 201)

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']})
        
        self.assertEqual(response.status_code, 400)

    def test_second_response_accepted_with_nomination(self):
        self._seed_data()
        response_data = {
            'application_form_id': self.form_with_nomination.id,
            'is_submitted': True,
            'answers': [
                {
                    'question_id': self.question1_with_nomination.id,
                    'value': 'Answer 1'
                }
            ]
        }

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']},
            query_string={'language': 'en'})
        
        self.assertEqual(response.status_code, 201)

        response = self.app.post(
            '/api/v1/response',
            data=json.dumps(response_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']},
            query_string={'language': 'en'})
        
        self.assertEqual(response.status_code, 201)

    def test_update(self):
        """Test a typical PUT flow."""

        self._seed_data()
        update_data = {
            'id': self.response.id,
            'application_form_id': self.form.id,
            'is_submitted': True,  # Set submitted
            'answers': [
                {
                    'question_id': self.question.id,
                    'value': 'Answer 1 UPDATED'  # Update an existing answer
                },
                {
                    'question_id': self.question2.id,  # Add a new answer
                    'value': 'This is the 2nd answer.'
                }
            ]
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'language': 'fr'})  # Updating the language from English to French

        self.assertEqual(response.status_code, 200)

        # Retrieve the response and check that the fields are as expected
        response = self.app.get(
            'api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.event.id})

        data = json.loads(response.data)[0]

        self.assertEqual(data['application_form_id'], self.form.id)
        self.assertEqual(data['user_id'], self.other_user_data['id'])

        parsed_submitted = dateutil.parser.parse(
            data['submitted_timestamp'])
        self.assertLess(
            abs((datetime.now() - parsed_submitted).total_seconds()), 5*60)

        self.assertTrue(data['is_submitted'])
        self.assertFalse(data['is_withdrawn'])
        self.assertEqual(data['language'], 'fr')
        self.assertTrue(data['answers'])

        answer = data['answers'][0]
        self.assertEqual(answer['value'], 'Answer 1 UPDATED')
        self.assertEqual(answer['question_id'], self.question.id)

        answer = data['answers'][1]
        self.assertEqual(answer['value'], 'This is the 2nd answer.')
        self.assertEqual(answer['question_id'], self.question2.id)

    def test_update_missing(self):
        """Test that 404 is returned if we try to update a response that doesn't exist."""
        
        self._seed_data()
        update_data = {
            'id': self.response.id + 100,
            'application_form_id': self.form.id,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'language': 'en'})

        self.assertEqual(response.status_code, 404)

    def test_update_permission(self):
        """Test that a user can't update another user's response."""
        
        self._seed_data()
        update_data = {
            'id': self.response.id,
            'application_form_id': self.form.id,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.user_data['token']},
            query_string={'language': 'en'})

        self.assertEqual(response.status_code, 401)

    def test_update_conflict(self):
        """Test that we can't update the application form id for a response."""
        
        self._seed_data()
        update_data = {
            'id': self.response.id,
            'application_form_id': self.form.id + 100,
            'is_submitted': True,  # Set submitted
            'answers': []
        }

        response = self.app.put(
            '/api/v1/response',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'language': 'en'})

        self.assertEqual(response.status_code, 409)

    def test_delete(self):
        """Test a typical DELETE flow."""
        
        self._seed_data()
        response = self.app.delete(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'id': self.response.id})

        self.assertEqual(response.status_code, 204)

        # We should still be able to get the response, but it is marked unsubmitted and withdrawn
        response = self.app.get(
            '/api/v1/response',
            headers={'Authorization': self.other_user_data['token']},
            query_string={'event_id': self.event.id})
        data = json.loads(response.data)[0]
        self.assertFalse(data['is_submitted'])
        self.assertTrue(data['is_withdrawn'])

    def test_delete_missing(self):
        """Test that we can't delete a response that doesn't exist."""
        
        self._seed_data()
        response = self.app.delete(
                '/api/v1/response',
                headers={'Authorization': self.other_user_data['token']},
                query_string={'id': self.response.id + 1000})
        self.assertEqual(response.status_code, 404)  # Not found

    def test_delete_permission(self):
        """Test that we can't delete another user's response."""
        
        self._seed_data()

        # test_response belongs to "other_user", check that "user" can't delete it
        response = self.app.delete(
            '/api/v1/response',
            headers={'Authorization': self.user_data['token']},
            query_string={'id': self.response.id})

        self.assertEqual(response.status_code, 401)  # Unauthorized
