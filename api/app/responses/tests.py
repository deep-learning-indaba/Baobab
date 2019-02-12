import json
from app import app, db
from flask import g
from datetime import date
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
        print(self.other_user_data)

        response = self.app.post('/api/v1/user', data=self.user_data_dict)
        self.user_data = json.loads(response.data)
        print(self.user_data)

        # Add application form data
        self.test_event = Event('Test Event', 'Event Description', date(2019, 2, 24), date(2019, 3, 24))
        _add_object_to_db(self.test_event)
        self.test_form = ApplicationForm(self.test_event.id, True, date(2019, 3, 24))
        _add_object_to_db(self.test_form)
        test_section = Section(self.test_form.id, 'Test Section', 'Test Description', 1)
        _add_object_to_db(test_section)
        self.test_question = Question(self.test_form.id, test_section.id, 'Test Question Description', 1, 'Test Type')
        _add_object_to_db(self.test_question)
        self.test_question2 = Question(self.test_form.id, test_section.id, 'Test Question 2', 2, 'short-text')
        _add_object_to_db(self.test_question2)

        test_response = Response(self.test_form.id, self.other_user_data['id'])
        _add_object_to_db(test_response)

        self.test_answer1 = Answer(test_response.id, self.test_question.id, 'My Answer')
        _add_object_to_db(self.test_answer1)
        self.test_answer2 = Answer(test_response.id, self.test_question2.id, 'Choose me! Choose me!')
        _add_object_to_db(self.test_answer2)
        
        db.session.flush()

    def test_get_response(self):
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

            answer = data['answers'][1]
            self.assertEqual(answer['id'], self.test_answer2.id)
            self.assertEqual(answer['value'], self.test_answer2.value)
            self.assertEqual(answer['question_id'], self.test_question2.id)

    def test_post(self):
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
            self.assertTrue(True)
                
    # TODO:
    # Test error conditions in GET
    # Complete test_post
    # Complete PUT for update
    # Test PUT
    # Complete DELETE
    # Test DELETE
