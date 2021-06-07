import json
from os import write
import zipfile
import tempfile
from datetime import date, datetime
import collections

import dateutil.parser
from flask import g

from app import app, db
from app.files.api import FileUploadAPI as file_upload
from app.applicationModel.models import ApplicationForm, Question, Section
from app.email_template.models import EmailTemplate
from app.events.models import Event
from app.organisation.models import Organisation
from app.responses.models import Answer, Response
from app.responses.repository import ResponseRepository as response_repository
from app.users.models import AppUser, Country, UserCategory
from app.utils.testing import ApiTestCase
from app.utils.strings import build_response_html_answers


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
        self.section_translation = self.add_section_translation(self.section.id, 'en')
        self.question = self.add_question(self.form.id, self.section.id, order=1)
        self.question_translation = self.add_question_translation(self.question.id, 'en', 'Question 1')
        self.question2 = self.add_question(self.form.id, self.section.id, order=2)
        self.question_translation2 = self.add_question_translation(self.question2.id, 'en', 'Question 2')
        self.response = self.add_response(self.form.id, self.other_user_data['id'], False, False)
        self.answer1 = self.add_answer(self.response.id, self.question.id, 'My Answer')

        self.event_with_nomination = self.add_event({'en': 'Event With Nomination'}, key='eeml-2025')
        self.form_with_nomination = self.create_application_form(self.event_with_nomination.id, True, True)
        self.section_with_nomination = self.add_section(self.event_with_nomination.id)
        self.section_translation_with_nomination = self.add_section_translation(self.section_with_nomination.id, 'en')
        self.question1_with_nomination = self.add_question(self.form_with_nomination.id, self.section_with_nomination.id, order=1)
        self.question_translation1_with_nomination = self.add_question_translation(self.question1_with_nomination.id, 'en', 'Question 1 with nomination')
        self.question2_with_nomination = self.add_question(self.form_with_nomination.id, self.section_with_nomination.id, order=2)
        self.question_translation2_with_nomination = self.add_question_translation(self.question2_with_nomination.id, 'en', 'Question 1 with nomination')
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


class ResponseListAPITest(ApiTestCase):
    def _seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        self.event2 = self.add_event(key='event2')

        self.users = self.add_n_users(4)
        UserName = collections.namedtuple('UserName', ['user_title', 'firstname', 'lastname'])
        self.user_names = [UserName(u.user_title, u.firstname, u.lastname) for u in self.users]

        self.event1admin = self.add_user('event1admin@mail.com')
        self.event2admin = self.add_user('event2admin@mail.com')
        
        self.event1.add_event_role('admin', self.event1admin.id)
        self.event2.add_event_role('admin', self.event2admin.id)
        db.session.commit()

        self.form1 = self.create_application_form(self.event1.id)
        self.form1_section1 = self.add_section(self.form1.id)
        self.form1_question1 = self.add_question(self.form1.id, self.form1_section1.id)  # ID 1
        self.add_question_translation(self.form1_question1.id, 'en', 'English Headline 1')
        self.add_question_translation(self.form1_question1.id, 'fr', 'French Headline 1')
        self.form1_question2 = self.add_question(self.form1.id, self.form1_section1.id)  # ID 2
        self.add_question_translation(self.form1_question2.id, 'en', 'English Headline 2')
        self.add_question_translation(self.form1_question2.id, 'fr', 'French Headline 2')
        self.form1_question3 = self.add_question(self.form1.id, self.form1_section1.id)  # ID 3
        self.add_question_translation(self.form1_question3.id, 'en', 'English Headline 3')
        self.add_question_translation(self.form1_question3.id, 'fr', 'French Headline 3')

        self.form2 = self.create_application_form(self.event2.id)
        self.form2_section1 = self.add_section(self.form2.id)
        self.form2_question1 = self.add_question(self.form2.id, self.form2_section1.id)  # ID 4
        self.add_question_translation(self.form2_question1.id, 'en', 'English Headline 3')
        self.add_question_translation(self.form2_question1.id, 'fr', 'French Headline 3')

        # Create responses, 3 for event 1 (2 submitted, 1 unsubmitted), 1 for event 2
        self.response1 = self.add_response(self.form1.id, self.users[0].id, is_submitted=True)
        self.response1_started = self.response1.started_timestamp
        self.response1_submitted = self.response1.submitted_timestamp
        self.add_answer(self.response1.id, self.form1_question1.id, 'First answer')
        self.add_answer(self.response1.id, self.form1_question2.id, 'Second answer')
        self.add_answer(self.response1.id, self.form1_question3.id, 'Third answer')

        self.response2 = self.add_response(self.form1.id, self.users[1].id, is_submitted=True, language='fr')
        self.response2_started = self.response2.started_timestamp
        self.response2_submitted = self.response2.submitted_timestamp
        self.add_answer(self.response2.id, self.form1_question1.id, 'Forth answer')
        self.add_answer(self.response2.id, self.form1_question2.id, 'Fifth answer')
        self.add_answer(self.response2.id, self.form1_question3.id, 'Sixth answer')

        self.response3 = self.add_response(self.form1.id, self.users[2].id, is_submitted=False)
        self.response3_started = self.response3.started_timestamp
        self.add_answer(self.response3.id, self.form1_question1.id, 'Seventh answer')
        self.add_answer(self.response3.id, self.form1_question2.id, 'Eigth answer')
        self.add_answer(self.response3.id, self.form1_question3.id, 'Ninth answer')

        self.response4 = self.add_response(self.form2.id, self.users[3].id, is_submitted=False)
        self.add_answer(self.response4.id, self.form2_question1.id, 'Tenth answer')

        self.review_form1 = self.add_review_form(self.form1.id)
        self.review_config1 = self.add_review_config(self.review_form1.id)

        self.add_response_reviewer(self.response1.id, self.users[1].id)
        self.add_response_reviewer(self.response1.id, self.users[2].id)
        self.add_response_reviewer(self.response2.id, self.users[0].id)

        review_response = self.add_review_response(self.users[1].id, self.response1.id, self.review_form1.id)
        self.review_response_id = review_response.id

        tag1 = self.add_tag()
        tag2 = self.add_tag(names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'})
        self.tag_response(self.response1.id, tag1.id)
        self.tag_response(self.response3.id, tag1.id)
        self.tag_response(self.response3.id, tag2.id)

    def test_no_questions_submitted(self):
        """Test response list with no questions requested."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': False
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            data=params)

        data = json.loads(response.data)

        self.assertEqual(len(data), 2)

        response1 = data[0]
        self.assertEqual(response1['response_id'], 1)
        self.assertEqual(response1['user_title'], self.user_names[0].user_title)
        self.assertEqual(response1['firstname'], self.user_names[0].firstname)
        self.assertEqual(response1['lastname'], self.user_names[0].lastname)
        self.assertEqual(response1['start_date'], self.response1_started.isoformat())
        self.assertEqual(response1['is_submitted'], True)
        self.assertEqual(response1['is_withdrawn'], False)
        self.assertEqual(response1['submitted_date'], self.response1_submitted.isoformat())
        self.assertEqual(response1['language'], 'en')
        self.assertEqual(len(response1['answers']), 0)
        self.assertEqual(len(response1['reviewers']), 2)
        self.assertEqual(response1['reviewers'][0]['reviewer_id'], 2)
        self.assertEqual(response1['reviewers'][0]['reviewer_name'], '{} {} {}'.format(*self.user_names[1]))
        self.assertEqual(response1['reviewers'][0]['review_response_id'], self.review_response_id)
        self.assertEqual(response1['reviewers'][1]['reviewer_id'], 3)
        self.assertEqual(response1['reviewers'][1]['reviewer_name'], '{} {} {}'.format(*self.user_names[2]))
        self.assertEqual(response1['reviewers'][1]['review_response_id'], None)
        self.assertEqual(len(response1['tags']), 1)
        self.assertEqual(response1['tags'][0]['id'], 1)
        self.assertEqual(response1['tags'][0]['name'], 'Tag 1 en')

        response2 = data[1]
        self.assertEqual(response2['response_id'], 2)
        self.assertEqual(response2['user_title'], self.user_names[1].user_title)
        self.assertEqual(response2['firstname'], self.user_names[1].firstname)
        self.assertEqual(response2['lastname'], self.user_names[1].lastname)
        self.assertEqual(response2['start_date'], self.response2_started.isoformat())
        self.assertEqual(response2['is_submitted'], True)
        self.assertEqual(response2['is_withdrawn'], False)
        self.assertEqual(response2['submitted_date'], self.response2_submitted.isoformat())
        self.assertEqual(response2['language'], 'fr')
        self.assertEqual(len(response2['answers']), 0)
        self.assertEqual(len(response2['reviewers']), 2)
        self.assertEqual(response2['reviewers'][0]['reviewer_id'], 1)
        self.assertEqual(response2['reviewers'][0]['reviewer_name'], '{} {} {}'.format(*self.user_names[0]))
        self.assertEqual(response2['reviewers'][0]['review_response_id'], None)
        self.assertEqual(response2['reviewers'][1], None)
        self.assertEqual(len(response2['tags']), 0)

    def test_questions_unsubmitted(self):
        """Test response list with questions requested and unsubmitted included."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': True,
            'question_ids[]': [1, 3]
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            data=params)

        data = json.loads(response.data)
        self.assertEqual(len(data), 3)

        self.assertEqual(len(data[0]['answers']), 2)

        self.assertEqual(data[0]['answers'][0]['question_id'], 1)
        self.assertEqual(data[0]['answers'][0]['value'], 'First answer')
        self.assertEqual(data[0]['answers'][0]['type'], 'short-text')
        self.assertEqual(data[0]['answers'][0]['options'], None)
        self.assertEqual(data[0]['answers'][0]['headline'], 'English Headline 1')
        self.assertEqual(data[0]['answers'][1]['question_id'], 3)
        self.assertEqual(data[0]['answers'][1]['value'], 'Third answer')
        self.assertEqual(data[0]['answers'][1]['type'], 'short-text')
        self.assertEqual(data[0]['answers'][1]['options'], None)
        self.assertEqual(data[0]['answers'][1]['headline'], 'English Headline 3')

        response3 = data[2]
        self.assertEqual(response3['response_id'], 3)
        self.assertEqual(response3['user_title'], self.user_names[2].user_title)
        self.assertEqual(response3['firstname'], self.user_names[2].firstname)
        self.assertEqual(response3['lastname'], self.user_names[2].lastname)
        self.assertEqual(response3['start_date'], self.response3_started.isoformat())
        self.assertEqual(response3['is_submitted'], False)
        self.assertEqual(response3['is_withdrawn'], False)
        self.assertEqual(response3['submitted_date'], None)
        self.assertEqual(response3['language'], 'en')
        self.assertEqual(len(response3['answers']), 2)
        self.assertEqual(len(response3['reviewers']), 2)
        self.assertEqual(response3['reviewers'][0], None)
        self.assertEqual(response3['reviewers'][1], None)
        self.assertEqual(len(response3['tags']), 2)
        self.assertEqual(response3['tags'][0]['id'], 1)
        self.assertEqual(response3['tags'][0]['name'], 'Tag 1 en')
        self.assertEqual(response3['tags'][1]['id'], 2)
        self.assertEqual(response3['tags'][1]['name'], 'Tag 2 en')


class ResponseTagAPITest(ApiTestCase):
    def _seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        self.event1admin = self.add_user('event1admin@mail.com')
        self.event1reviewer1 = self.add_user('event1reviewer1@mail.com')
        self.event1reviewer2 = self.add_user('event1reviewer2@mail.com')
        self.user1 = self.add_user('user1@mail.com')
        self.user2 = self.add_user('user2@mail.com')

        self.event1.add_event_role('admin', self.event1admin.id)
        self.event1.add_event_role('reviewer', self.event1reviewer1.id)
        self.event1.add_event_role('reviewer', self.event1reviewer2.id)

        application_form = self.create_application_form(self.event1.id)
        self.response1 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.add_response_reviewer(self.response1.id, self.event1reviewer1.id)
        self.response2 = self.add_response(application_form.id, self.user2.id, is_submitted=True)
        self.add_response_reviewer(self.response2.id, self.event1reviewer2.id)

        self.tag1 = self.add_tag()
        self.tag2 = self.add_tag(names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'})

        self.tag_response(self.response2.id, self.tag2.id)

    def test_tag_admin(self):
        """Test that an event admin can add a tag to a response."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.post(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 201)

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': False
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data[0]['tags']), 1)
        self.assertEqual(data[0]['tags'][0]['id'], 1)

    def test_tag_reviewer(self):
        """Test that a reviewer can add a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.post(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1reviewer1@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 201)

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': False
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data[0]['tags']), 1)
        self.assertEqual(data[0]['tags'][0]['id'], 1)

    def test_remove_tag_admin(self):
        """Test that an event admin can remove a tag from a response."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag2.id,
            'response_id': self.response2.id
        }

        response = self.app.delete(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 200)

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': False
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data[1]['tags']), 0)

    def test_remove_tag_reviewer(self):
        """Test that a reviewer can remove a tag from a response."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag2.id,
            'response_id': self.response2.id
        }

        response = self.app.delete(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1reviewer2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 200)

        params = {
            'event_id': self.event1.id,
            'language': 'en',
            'include_unsubmitted': False
        }

        response = self.app.get(
            '/api/v1/responses',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data[1]['tags']), 0)

    def test_tag_different_reviewer(self):
        """Test that a reviewer of a different response can't add a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.post(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1reviewer2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

    def test_remove_tag_different_reviewer(self):
        """Test that a reviewer of a different response can't remove a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.delete(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('event1reviewer2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

    def test_tag_non_admin_non_reviewer(self):
        """Test that a non admin and non reviewer can't add a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.post(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('user2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

    def test_remove_tag_non_admin_non_reviewer(self):
        """Test that a non admin and non reviewer can't remove a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'response_id': self.response1.id
        }

        response = self.app.delete(
            '/api/v1/responsetag',
            headers=self.get_auth_header_for('user2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

class ResponseDetailAPITest(ApiTestCase):
    def _seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        self.event1admin = self.add_user('event1admin@mail.com')
        self.user1 = self.add_user('user1@mail.com', user_title='Ms', firstname='Danai', lastname='Gurira')

        self.reviewer1 = self.add_user('reviewer1@mail.com', user_title='Mx', firstname='Skittles', lastname='Cat')
        self.reviewer2 = self.add_user('reviewer2@mail.com', user_title='Mr', firstname='Finn', lastname='Dog')
        self.reviewer3 = self.add_user('reviewer3@mail.com', user_title='Mx', firstname='Bailey', lastname='Dog')

        self.event1.add_event_role('admin', self.event1admin.id)
        self.event1.add_event_role('reviewer', self.reviewer1.id)
        self.event1.add_event_role('reviewer', self.reviewer2.id)

        application_form = self.create_application_form(self.event1.id)
        section = self.add_section(application_form.id)
        question1 = self.add_question(application_form.id, section.id)
        self.add_question_translation(question1.id, 'en')
        question2 = self.add_question(application_form.id, section.id)
        self.add_question_translation(question2.id, 'en')

        self.response1 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response1_submitted = self.response1.submitted_timestamp
        self.response1_started = self.response1.started_timestamp
        self.add_answer(self.response1.id, question1.id, 'Answer 1')
        self.add_answer(self.response1.id, question2.id, 'Answer 2')

        tag1 = self.add_tag()
        tag2 = self.add_tag(names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'})

        self.tag_response(self.response1.id, tag1.id)
        self.tag_response(self.response1.id, tag2.id)

        review_form = self.add_review_form(application_form.id)
        config = self.add_review_config(review_form.id, 2, 1)

        self.add_response_reviewer(self.response1.id, self.reviewer1.id)
        self.add_response_reviewer(self.response1.id, self.reviewer2.id)
        self.add_response_reviewer(self.response1.id, self.reviewer3.id)

        self.add_review_response(self.reviewer1.id, self.response1.id, review_form.id)
        self.add_review_response(self.reviewer2.id, self.response1.id, review_form.id, is_submitted=True)

    def test_response_detail(self):
        """Test typical get request."""
        self._seed_static_data()
        params = {
            'event_id': self.event1.id,
            'response_id': self.response1.id,
            'language': 'en'
        }

        response = self.app.get(
            '/api/v1/responsedetail',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['id'], 1)
        self.assertEqual(data['application_form_id'], 1)
        self.assertEqual(data['user_id'], 2)
        self.assertEqual(data['is_submitted'], True)
        self.assertEqual(data['submitted_timestamp'], self.response1_submitted.isoformat())
        self.assertEqual(data['is_withdrawn'], False)
        self.assertEqual(data['withdrawn_timestamp'], None)
        self.assertEqual(data['started_timestamp'], self.response1_started.isoformat())
        self.assertEqual(len(data['answers']), 2)
        self.assertEqual(data['answers'][0]['value'], 'Answer 1')
        self.assertEqual(data['answers'][1]['value'], 'Answer 2')
        self.assertEqual(data['language'], 'en')
        self.assertEqual(data['user_title'], 'Ms')
        self.assertEqual(data['firstname'], 'Danai')
        self.assertEqual(data['lastname'], 'Gurira')
        self.assertEqual(len(data['tags']), 2)
        self.assertEqual(data['tags'][0]['name'], 'Tag 1 en')
        self.assertEqual(data['tags'][1]['name'], 'Tag 2 en')
        self.assertEqual(len(data['reviewers']), 3)
        self.assertEqual(data['reviewers'][0]['user_title'], 'Mx')
        self.assertEqual(data['reviewers'][0]['firstname'], 'Skittles')
        self.assertEqual(data['reviewers'][0]['lastname'], 'Cat')
        self.assertEqual(data['reviewers'][0]['status'], 'started')
        self.assertEqual(data['reviewers'][1]['user_title'], 'Mr')
        self.assertEqual(data['reviewers'][1]['firstname'], 'Finn')
        self.assertEqual(data['reviewers'][1]['lastname'], 'Dog')
        self.assertEqual(data['reviewers'][1]['status'], 'completed')
        self.assertEqual(data['reviewers'][2]['user_title'], 'Mx')
        self.assertEqual(data['reviewers'][2]['firstname'], 'Bailey')
        self.assertEqual(data['reviewers'][2]['lastname'], 'Dog')
        self.assertEqual(data['reviewers'][2]['status'], 'not_started')


    def test_response_detail_admin_only(self):
        """Test that a non admin can't access reponse detail."""
        self._seed_static_data()
        params = {
            'event_id': self.event1.id,
            'response_id': self.response1.id,
            'language': 'en'
        }

        response = self.app.get(
            '/api/v1/responsedetail',
            headers=self.get_auth_header_for('user1@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

class ResponseExportAPITest(ApiTestCase):
    def _data_seed_static(self):
    
        self.event1 = self.add_event(key='event1')
        self.event1admin = self.add_user('event1admin@mail.com', is_admin=True)
        self.user1 = self.add_user('user1@mail.com', user_title='Ms', firstname='Danai', lastname='Gurira')

        application_form = self.create_application_form(self.event1.id)
        # Section 1, two questions
        section1 = self.add_section(application_form.id)
        self.add_section_translation(section1.id, 'en', name='Section1')
        question1 = self.add_question(application_form.id, section1.id)
        self.add_question_translation(question1.id, 'en', headline='Question 1, S1')
        question2 = self.add_question(application_form.id, section1.id)
        self.add_question_translation(question2.id, 'en', headline='Question 2, S1')

        # Section 2, 3 questions
        section2 = self.add_section(application_form.id)
        self.add_section_translation(section2.id, 'en', name='Section2')
        question2_1 = self.add_question(application_form.id, section2.id)
        self.add_question_translation(question2_1.id, 'en', headline='Question 1, S2')
        question2_2 = self.add_question(application_form.id, section2.id)
        self.add_question_translation(question2_2.id, 'en', headline='Question 2, S2')
        question2_3 = self.add_question(application_form.id, section2.id)
        self.add_question_translation(question2_3.id, 'en', headline='Question 3, S2')

        # Section 3, 1 question
        section3 = self.add_section(application_form.id)
        self.add_section_translation(section3.id, 'en', name='Section3')
        question3_1 = self.add_question(application_form.id, section3.id)
        self.add_question_translation(question3_1.id, 'en', headline='Queston 1, S3')

        # Two supplementary files included in application upload (e.g. CV) - Section 1
        question_supp1 = self.add_question(application_form.id, section1.id, question_type = 'file')
        # ref_supp1, status_code = file_upload.post(self)

        question_supp2 = self.add_question(application_form.id, section1.id, question_type = 'file')
        # ref_supp2, status_code = file_upload.post(self)

        # Create response
        self.response1 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response1_submitted = self.response1.submitted_timestamp
        self.response1_started = self.response1.started_timestamp
        self.add_answer(self.response1.id, question1.id, 'Section 1 Answer 1')
        self.add_answer(self.response1.id, question2.id, 'Section 1 Answer 2')

        self.add_answer(self.response1.id, question2_1.id, 'Section 2 Answer 1')
        self.add_answer(self.response1.id, question2_2.id, 'Section 2 Answer 2')
        self.add_answer(self.response1.id, question2_3.id, 'Section 2 Answer 3')

        self.add_answer(self.response1.id, question3_1.id, 'Section 3 Answer 1')

        # Add file type answer
        with tempfile.NamedTemporaryFile(mode='wb') as temp:

                temp.write(b'This is my CV')

                temp.flush()
            
                response_reference = self.app.post(
                    '/api/v1/file',
                    data=temp.name,
                    content_type='text/plain',
                    headers=self.get_auth_header_for('user1@mail.com')
                    )
                print(response_reference)
        # self.add_answer(self.response1.id, question_supp1.id, {"filename": ref_supp1, "rename": "supplementarrypdfONE.pdf" })
        # self.add_answer(self.response1.id, question_supp2.id, {"filename": ref_supp2, "rename": "supplementarrypdfTWO.pdf" })


    # TODO clean these up and test them out.   

    def test_zipped_file_uncorrupted(self):
        """
        Tests that the zipped files' CRCs are okay. 
        """

        self._data_seed_static()

        params = {
            'response_id': self.response1.id,
            'language': 'en'
        }
        
        response = self.app.get(
            '/api/v1/response-export',
            headers=self.get_auth_header_for('event1admin@mail.com'), 
            json=params)
            
        assert response.mimetype == 'application/zip'
        assert response.headers.get('Content-Disposition') == 'attachment; filename=response_1.zip'

        with tempfile.NamedTemporaryFile(mode='wb') as temp:

            temp.write(response.data)

            temp.flush()

            with zipfile.ZipFile(temp.name) as zip:
                assert zip.testzip() is None
    

    def test_number_files_returned_zipped_folder(self):
            """
            Tests that the correct number of files are returned in the zip folder
            """

            self._data_seed_static()

            params = {
                'response_id': self.response1.id,
                'language': 'en'
            }
            
            with tempfile.NamedTemporaryFile(mode='wb') as temp:

                temp.write(b'This is my CV')

                temp.flush()
            
                response = self.app.post(
                    '/api/v1/file',
                    data=temp.name,
                    content_type='text/plain',
                    headers=self.get_auth_header_for('user1@mail.com')
                    )
            
            response = self.app.get(
                '/api/v1/response-export',
                headers=self.get_auth_header_for('event1admin@mail.com'), 
                json=params)

            assert response.mimetype == 'application/zip'
            assert response.headers.get('Content-Disposition') == 'attachment; filename=response_1.zip'

            with tempfile.NamedTemporaryFile(mode='wb') as temp_zip:

                temp_zip.write(response.data)

                temp_zip.flush()

                with zipfile.ZipFile(temp_zip.name) as zip:
                    assert zip.testzip() is None
                    print(zip.namelist())
                    assert len(zip.namelist()) == 2

        
    def test_filename_renamed_correctly_in_zip_folder(self):
        "Tests that the files are correctly renamed in the downloaded zip folder"

        self._data_seed_static()

        params = {
            'response_id': self.response1.id,
            'language': 'en'
        }
        
        response = self.app.get(
            '/api/v1/response-export',
            headers=self.get_auth_header_for('event1admin@mail.com'), 
            json=params)
            

        with tempfile.NamedTemporaryFile(mode='wb') as temp:

            temp.write(response.data)

            temp.flush()

            with zipfile.ZipFile(temp.name) as zip:
                assert zip.namelist() == [f"{self.response1.id}.pdf"]
    