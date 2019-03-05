import json
import dateutil.parser

from app import app, db
from flask import g
from datetime import date, datetime
from app.utils.testing import ApiTestCase
from app.responses.models import Response, Answer
from app.events.models import Event
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question


def _add_object_to_db(obj):
    db.session.add(obj)
    db.session.commit()

class ResponseApiTest(ApiTestCase):
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
        'password': '123456'
    }

    def _seed_data(self):
        # Add a user
        test_country = Country('Indaba Land')
        _add_object_to_db(test_country)

        test_category = UserCategory('Category1')
        _add_object_to_db(test_category)
        
        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = 'other@user.com'
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.other_user_data = json.loads(response.data)

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.user_data = json.loads(response.data)

        # Add application form data
        self.test_event = Event('Test Event', 'Event Description', date(2019, 2, 24), date(2019, 3, 24))
        _add_object_to_db(self.test_event)
        self.test_form = ApplicationForm(self.test_event.id, True, date(2019, 3, 24))
        _add_object_to_db(self.test_form)
        test_section = Section(self.test_form.id, 'Test Section', 'Test Description', 1)
        _add_object_to_db(test_section)
        self.test_question = Question(self.test_form.id, test_section.id, 'Test Question Description', 'Test question placeholder', 1, 'Test Type', None)
        _add_object_to_db(self.test_question)
        self.test_question2 = Question(self.test_form.id, test_section.id, 'Test Question 2', 'Enter something', 2, 'short-text', None)
        _add_object_to_db(self.test_question2)

        self.test_response = Response(self.test_form.id, self.other_user_data['id'])
        _add_object_to_db(self.test_response)

        self.test_answer1 = Answer(self.test_response.id, self.test_question.id, 'My Answer')
        _add_object_to_db(self.test_answer1)
        
        db.session.flush()

    def test_get_response(self):
        """Test a typical GET flow."""
        with app.app_context():
            self._seed_data()

            response = self.app.get('/api/v1/response', 
                                    headers={'Authorization': self.other_user_data['token']}, 
                                    query_string={'event_id': self.test_event.id})
            data = json.loads(response.data)
            
            self.assertEqual(data['application_form_id'], self.test_form.id)
            self.assertEqual(data['user_id'], self.other_user_data['id'])
            self.assertIsNone(data['submitted_timestamp'])
            self.assertFalse(data['is_withdrawn'])
            self.assertTrue(data['answers'])

            answer = data['answers'][0]
            self.assertEqual(answer['id'], self.test_answer1.id)
            self.assertEqual(answer['value'], self.test_answer1.value)
            self.assertEqual(answer['question_id'], self.test_question.id)

    def test_get_event(self):
        """Test that we get an error if we try to get a response for an event that doesn't exist."""
        with app.app_context():
            self._seed_data()

            response = self.app.get('/api/v1/response', 
                                    headers={'Authorization': self.other_user_data['token']}, 
                                    query_string={'event_id': self.test_event.id + 100})

            self.assertEqual(response.status_code, 404)
    
    def test_get_missing_form(self):
        """Test that we get a 404 error if we try to get a response for an event with no application form."""
        with app.app_context():
            self._seed_data()
            test_event2 = Event('Test Event 2', 'Event Description', date(2019, 2, 24), date(2019, 3, 24))
            _add_object_to_db(test_event2)

            response = self.app.get('/api/v1/response', 
                                    headers={'Authorization': self.other_user_data['token']}, 
                                    query_string={'event_id': test_event2.id})

            self.assertEqual(response.status_code, 404)

    def test_get_missing_response(self):
        """Test that we get a 404 error if there is no response for the event and user combination."""
        with app.app_context():
            self._seed_data()

            response = self.app.get('/api/v1/response', 
                                    headers={'Authorization': self.user_data['token']}, 
                                    query_string={'event_id': self.test_event.id})

            self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test a typical POST flow."""

        with app.app_context():
            self._seed_data()
            response_data = {
                'application_form_id': self.test_form.id,
                'is_submitted': False,
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
                                    headers={'Authorization': self.user_data['token']}, 
                                    query_string={'event_id': self.test_event.id})
            data = json.loads(response.data)

            self.assertEqual(data['application_form_id'], self.test_form.id)
            self.assertEqual(data['user_id'], self.user_data['id'])
            self.assertIsNone(data['submitted_timestamp'])
            self.assertFalse(data['is_withdrawn'])
            self.assertTrue(data['answers'])

            answer = data['answers'][0]
            self.assertEqual(answer['value'], 'Answer 1')
            self.assertEqual(answer['question_id'], self.test_question.id)

            answer = data['answers'][1]
            self.assertEqual(answer['value'], 'Hello world, this is the 2nd answer.')
            self.assertEqual(answer['question_id'], self.test_question2.id)

    def test_update(self):
        """Test a typical PUT flow."""

        with app.app_context():
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

            parsed_submitted = dateutil.parser.parse(data['submitted_timestamp'])
            self.assertLess(abs((datetime.now() - parsed_submitted).total_seconds()), 5*60)
            
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
        with app.app_context():
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
        with app.app_context():
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
        with app.app_context():
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
        with app.app_context():
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
        with app.app_context():
            self._seed_data()
            response = self.app.delete(
                    '/api/v1/response', 
                    headers={'Authorization': self.other_user_data['token']},
                    query_string={'id': self.test_response.id + 10})
            self.assertEqual(response.status_code, 404)  # Not found

    def test_delete_permission(self):
        """Test that we can't delete another user's response."""
        with app.app_context():
            self._seed_data()

            # test_response belongs to "other_user", check that "user" can't delete it
            response = self.app.delete(
                    '/api/v1/response', 
                    headers={'Authorization': self.user_data['token']},
                    query_string={'id': self.test_response.id})
            
            self.assertEqual(response.status_code, 401)  # Unauthorized