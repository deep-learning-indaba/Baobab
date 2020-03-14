import json
import dateutil.parser

from app import app, db
from flask import g
from datetime import date, datetime
from app.utils.testing import ApiTestCase
from app.email_template.models import EmailTemplate
from app.responses.models import Response, Answer
from app.events.models import Event
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question
from app.organisation.models import Organisation
from app.responses.repository import ResponseRepository as response_repository


class ResponseApiTest(ApiTestCase):
    user_data_dict = {
        'email': 'something@email.com',
        'firstname': 'Some',
        'lastname': 'Thing',
        'user_title': 'Mr',
        'password': '123456',
        'policy_agreed': True
    }

    nominated_data_dict = {
        'email':     'awesome@email.com',
        'firstname': 'Awesome',
        'lastname':  'McAwesomeFace',
        'title':     'Mx',
        }

    other_user_email = 'other@user.com'
    num_dummy_users = 10

    def _seed_data(self):
        """Create dummy data for testing"""
        organisation = self.add_organisation(
            'Deep Learning Indaba',
            'Baobab',
            'blah.png',
            'blah_big.png',
            'deeplearningindba',
            'https://www.deeplearningindaba.com',
            'from@deeplearningindaba.com')

        email_templates = [
            EmailTemplate('withdrawal', None, ''),
            EmailTemplate('confirmation-response', None, '{question_answer_summary}')
        ]
        db.session.add_all(email_templates)
        db.session.commit()

        # Add country
        test_country = Country('Indaba Land')
        self.add_to_db(test_country)

        # Add category
        test_category = UserCategory('Category1')
        self.add_to_db(test_category)

        # Add users to database
        other_user_data = self.user_data_dict.copy()
        other_user_data['email'] = self.other_user_email
        response = self.app.post('/api/v1/user', data=other_user_data)
        self.other_user_data = json.loads(response.data)

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.user_data = json.loads(response.data)

        self.add_n_users(self.num_dummy_users)

        # Add application form data
        self.test_event = self.add_event('Test Event', 'Event Description', date(2019, 2, 24), date(2019, 3, 24),
                                         'NAGSOLVER')
        self.test_form = self.create_application_form(
                self.test_event.id, True)
        self.test_section = Section(
                self.test_form.id, 'Test Section', 'Test Description', 1)
        self.add_to_db(self.test_section)
        self.test_question = Question(self.test_form.id, self.test_section.id,
                                      'Test Question Description', 'Test question placeholder', 1, 'Test Type', None)
        self.add_to_db(self.test_question)
        self.test_question2 = Question(
                self.test_form.id, self.test_section.id, 'Test Question 2', 'Enter something', 2, 'short-text', None)
        self.add_to_db(self.test_question2)

        # responses
        self.test_response = Response(
                self.test_form.id, self.other_user_data['id'])
        self.add_to_db(self.test_response)

        self.test_answer1 = Answer(
                self.test_response.id, self.test_question.id, 'My Answer')
        self.add_to_db(self.test_answer1)

        self.responses = []
        for user in self.test_users:
            response = Response(self.test_form.id, user.id)
            self.add_to_db(response)
            answer1 = Answer(response.id, self.test_question.id, "{}'s Answer for question 1".format(user.firstname))
            answer2 = Answer(response.id, self.test_question2.id, "{}'s Answer for question 2".format(user.firstname))
            self.add_to_db(answer1)
            self.add_to_db(answer2)
            self.responses.append(response)

        # add nomination application form
        self.test_nomination_form = self.create_application_form(
                self.test_event.id, True, True)
        self.test_nomination_response = Response(
                self.test_nomination_form.id, self.other_user_data['id'])
        self.add_to_db(self.test_nomination_response)

        db.session.flush()

    def test_get_response(self):
        """Test a typical GET flow."""
        
        self._seed_data()

        response = self.app.get('/api/v1/response',
                                headers={
                                    'Authorization': self.other_user_data['token']},
                                query_string={'event_id': self.test_event.id})
        data = json.loads(response.data)

        self.assertEqual(data[0]['application_form_id'], self.test_form.id)
        self.assertEqual(data[0]['user_id'], self.other_user_data['id'])
        self.assertIsNone(data[0]['submitted_timestamp'])
        self.assertFalse(data[0]['is_withdrawn'])
        self.assertTrue(data[0]['answers'])

        answer = data[0]['answers'][0]
        self.assertEqual(answer['id'], self.test_answer1.id)
        self.assertEqual(answer['value'], self.test_answer1.value)
        self.assertEqual(answer['question_id'], 1)

    def test_repo_get_response(self):
        """Test for when retrieving a response from the repository and not via the api directly"""
        self._seed_data()

        response = response_repository.get_by_id_and_user_id(
                self.test_response.id, self.other_user_data['id'])
        self.assertEqual(response.application_form_id, self.test_form.id)
        self.assertEqual(response.user_id, self.other_user_data['id'])
        self.assertIsNone(response.submitted_timestamp)
        self.assertFalse(response.is_withdrawn)
        self.assertTrue(response.answers)

        same_response = response_repository.get_by_id(self.test_response.id)
        self.assertEqual(response, same_response)

        all_user_responses = response_repository.get_by_user_id(self.other_user_data['id'])
        self.assertEqual(len(all_user_responses), 2)
        self.assertEqual(response, all_user_responses[0])

    def test_repo_get_answers(self):
        self._seed_data()

        # retrieve using response_id
        #   first answer should have correct response_id and question_id
        answers_by_response = response_repository.get_answers_by_response_id(self.test_response.id)
        self.assertEqual(answers_by_response[0].response_id, self.test_response.id)
        self.assertEqual(answers_by_response[0].question_id, self.test_question.id)

        # retrieve using question_id
        #   test the first answer here is the same as first answer above
        #   test_question completed by dummy users and other_user
        answers_by_question = response_repository.get_answers_by_question_id(self.test_question.id)
        self.assertEqual(answers_by_question[0], answers_by_response[0])
        self.assertEqual(len(self.test_users) + 1, len(answers_by_question))  # including other_user response

        # retrieve using response_id and question_id
        #   use same question_id and response_id as previous test --> can test object is the same
        answer_by_qid_rid = response_repository.get_answer_by_question_id_and_response_id(
                self.test_question.id, self.test_response.id)
        self.assertEqual(answer_by_qid_rid, answers_by_response[0])
        #   use different ids. Check expected ids are in the returned answer
        answer_by_qid_rid_q2 = response_repository.get_answer_by_question_id_and_response_id(
                self.test_question2.id, self.responses[0].id)
        self.assertEqual(answer_by_qid_rid_q2.response_id, self.responses[0].id)
        self.assertEqual(answer_by_qid_rid_q2.question_id, self.test_question2.id)

        # retrieve all (Question, Answer) tuples using section_id and response_id
        qa_by_sid_rid = response_repository.get_question_answers_by_section_id_and_response_id(
                self.test_section.id, self.test_response.id)
        self.assertTupleEqual(qa_by_sid_rid[0], (self.test_question, self.test_answer1))
        other_response = self.responses[0]
        qa_by_sid_rid_dummy = response_repository.get_question_answers_by_section_id_and_response_id(
                self.test_section.id, other_response.id)
        answer1 = response_repository.get_answer_by_question_id_and_response_id(
                self.test_question.id, other_response.id)
        answer2 = response_repository.get_answer_by_question_id_and_response_id(
                self.test_question2.id, other_response.id)
        self.assertEqual(len(qa_by_sid_rid_dummy), 2)  # answered 2 questions
        self.assertTupleEqual(qa_by_sid_rid_dummy[0], (self.test_question, answer1))
        self.assertTupleEqual(qa_by_sid_rid_dummy[1], (self.test_question2, answer2))

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
        data = json.loads(response.data)[0]

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

        data = json.loads(response.data)[0]

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
        data = json.loads(response.data)[0]
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
