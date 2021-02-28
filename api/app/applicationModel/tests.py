# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta

from app import LOGGER, db
from app.applicationModel.models import ApplicationForm, Question, Section
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository
from app.events.models import Event, EventType
from app.organisation.models import Organisation
from app.utils.testing import ApiTestCase


class ApplicationFormApiTest(ApiTestCase):

    def setUp(self):
        super(ApplicationFormApiTest, self).setUp()
        self._seed_data()

    def _seed_data(self):
        self.test_user = self.add_user('something@email.com')

        self.add_organisation('IndabaX')
        start_time = datetime.now() + timedelta(days=30)
        end_time = datetime.now() + timedelta(days=60)

        self.event = self.add_event({'en': 'Test Event'}, {'en': 'Event Description'}, start_time, end_time)
        self.form = self.create_application_form(self.event.id, True, False)

        self.section = self.add_section(self.form.id, 1)
        self.section_translation_en = self.add_section_translation(self.section.id, 'en', 'Test Section', 'Test Description', ['no'])
        self.section_translation_fr = self.add_section_translation(self.section.id, 'fr', 'Section francaise', 'Description du test', ['non'])
        self.question = self.add_question(self.form.id, self.section.id, question_type='multi-choice')
        self.question_translation_en = self.add_question_translation(
            question_id=self.question.id,
            language='en',
            headline='English Headline',
            description='English Question Description',
            placeholder='English Placeholder',
            validation_regex='^\\W*(\\w+(\\W+|$)){0,150}$',
            validation_text='Enter a maximum of 150 words',
            options=[{'label': 'Yes', 'value': 'yes'}, {'label': 'No', 'value': 'no'}],
            show_for_values=['yes']
        )
        self.question_translation_fr = self.add_question_translation(
            question_id=self.question.id,
            language='fr',
            headline='Titre francais',
            description='Description de la question en Francais',
            placeholder='Espace reserve Francais',
            validation_regex='^\\W*(\\w+(\\W+|$)){0,200}$',
            validation_text='Entrez un maximum de 200 mots',
            options=[{'label': 'Oui', 'value': 'oui'}, {'label': 'Non', 'value': 'non'}],
            show_for_values=['oui']
        )

        self.section2 = self.add_section(self.form.id, 2)
        self.section_translation2_en = self.add_section_translation(self.section2.id, 'en', 'Test Section 2', 'Test Description 2')
        self.section_translation2_fr = self.add_section_translation(self.section2.id, 'fr', 'Section francaise 2', 'Description du test 2')
        self.question2 = self.add_question(self.form.id, self.section2.id, question_type='text')
        self.question_translation2_en = self.add_question_translation(self.question2.id, 'en', 'English Headline 2')
        self.question_translation2_fr = self.add_question_translation(self.question2.id, 'fr', 'Titre francais 2')

    def test_get_form_in_english(self):
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.get(
            '/api/v1/application-form',
            headers=header,
            query_string={'event_id': 1, 'language': 'en'}
        )
        data = json.loads(response.data)

        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['nominations'], False)

        self.assertEqual(len(data['sections']), 2)
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['depends_on_question_id'], None)

        self.assertEqual(data['sections'][0]['name'], 'Test Section')
        self.assertEqual(data['sections'][0]['description'], 'Test Description')
        self.assertEqual(data['sections'][0]['show_for_values'], ['no'])

        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['is_required'], True)
        self.assertEqual(data['sections'][0]['questions'][0]['depends_on_question_id'], None)
        self.assertEqual(data['sections'][0]['questions'][0]['key'], None)

        self.assertEqual(data['sections'][0]['questions'][0]['description'], 'English Question Description')
        self.assertEqual(data['sections'][0]['questions'][0]['headline'], 'English Headline')
        self.assertEqual(data['sections'][0]['questions'][0]['options'], [{'label': 'Yes', 'value': 'yes'}, {'label': 'No', 'value': 'no'}])
        self.assertEqual(data['sections'][0]['questions'][0]['placeholder'], 'English Placeholder')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_regex'], '^\\W*(\\w+(\\W+|$)){0,150}$')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_text'], 'Enter a maximum of 150 words')
        self.assertEqual(data['sections'][0]['questions'][0]['show_for_values'], ['yes'])
        
    
    def test_get_form_in_french(self):
        header = self.get_auth_header_for(self.test_user.email)
        response = self.app.get(
            '/api/v1/application-form',
            headers=header,
            query_string={'event_id': 1, 'language': 'fr'}
        )
        data = json.loads(response.data)

        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['nominations'], False)

        self.assertEqual(len(data['sections']), 2)
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['depends_on_question_id'], None)

        self.assertEqual(data['sections'][0]['name'], 'Section francaise')
        self.assertEqual(data['sections'][0]['description'], 'Description du test')
        self.assertEqual(data['sections'][0]['show_for_values'], ['non'])

        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['is_required'], True)
        self.assertEqual(data['sections'][0]['questions'][0]['depends_on_question_id'], None)
        self.assertEqual(data['sections'][0]['questions'][0]['key'], None)

        self.assertEqual(data['sections'][0]['questions'][0]['description'], 'Description de la question en Francais')
        self.assertEqual(data['sections'][0]['questions'][0]['headline'], 'Titre francais')
        self.assertEqual(data['sections'][0]['questions'][0]['options'], [{'label': 'Oui', 'value': 'oui'}, {'label': 'Non', 'value': 'non'}])
        self.assertEqual(data['sections'][0]['questions'][0]['placeholder'], 'Espace reserve Francais')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_regex'], '^\\W*(\\w+(\\W+|$)){0,200}$')
        self.assertEqual(data['sections'][0]['questions'][0]['validation_text'], 'Entrez un maximum de 200 mots')
        self.assertEqual(data['sections'][0]['questions'][0]['show_for_values'], ['oui'])

    def test_repo_get_by_event(self):
        app = application_form_repository.get_by_event_id(self.test_event.id)
        self.assertEqual(app, self.test_form)

    def test_repo_get_sections(self):
        sections_by_app_id = application_form_repository.get_sections_by_app_id(self.test_form.id)
        self.assertEqual(sections_by_app_id[0], self.test_section)
        self.assertEqual(sections_by_app_id[1], self.test_section2)
        sections_by_app_id_and_section_name = application_form_repository. \
            get_section_by_app_id_and_section_name(self.test_form.id, self.test_section.name)
        self.assertEqual(sections_by_app_id_and_section_name, self.test_section)
        sections_by_app_id_and_section_name = application_form_repository. \
            get_section_by_app_id_and_section_name(self.test_form.id, self.test_section2.name)
        self.assertEqual(sections_by_app_id_and_section_name, self.test_section2)

        section = application_form_repository.get_section_by_id(self.test_section.id)
        self.assertEqual(section, self.test_section)

    def test_repo_get_question(self):
        question1 = application_form_repository.get_question_by_id(self.test_question.id)
        self.assertEqual(question1, self.test_question)

        question2 = application_form_repository.get_question_by_id(self.test_question2.id)
        self.assertEqual(question2, self.test_question2)


APPLICATION_FORM_POST_DATA = {
  "event_id": 1, 
  "is_open": True, 
  "nominations": False, 
  "sections": [
    {
      "name": {
         "en": "Section 1",
         "fr": "Section 1"
      },
      "description": {
         "en": "Description of the section",
         "fr": "Description de la section"
      },
      "order": 1,
      "depends_on_question_id": None,
      "show_for_values": {
          "en": None,
          "fr": None
      },
      "key": "candidate_information",
      "questions": [
        {
          "id": 1,    
          "validation_regex": {
             "en": None, 
             "fr": None
          },
          "options": {
              "en": [
                  {"value": "undergrad", "label": "An undergraduate student"}, 
                  {"value": "masters", "label": "A masters student"}, 
                ],
              "fr": [
                  {"value": "undergrad", "label": "un étudiant de premier cycle"}, 
                  {"value": "masters", "label": "un étudiant en maîtrise"}, 
                ],
          },
          "description": {
              "en": "Question 1 en", 
              "fr": "Question 1 fr"
          },
          "headline": {
              "en": "Question 1 en", 
              "fr": "Question 1 fr"
          },
          "placeholder": {
              "en": "Select an Option...",
              "fr": "Sélectionnez une option"
          },
          "is_required": True, 
          "type": "multi-choice", 
          "validation_text": {
              "en": None,
              "fr": None
          },
          "order": 1,
          "depends_on_question_id": 3,
          "key": None,
          "show_for_values": {
              "en": ["the-matrix", "terminator"],
              "fr": ["the-matrix", "terminator"]
          }
        },
        {
          "id": 2,    
          "validation_regex": {
             "en": "^Moo$", 
             "fr": "^moo$"
          },
          "options": {
              "en": None,
              "fr": None,
          },
          "description": {
              "en": "Question 2 en", 
              "fr": "Question 2 fr"
          },
          "headline": {
              "en": "Question 2 en", 
              "fr": "Question 2 fr"
          },
          "placeholder": {
              "en": "Enter some text...",
              "fr": "Entrez du texte ..."
          },
          "is_required": False, 
          "type": "short-text", 
          "validation_text": {
              "en": "You must enter the word Moo",
              "fr": "Vous devez entrer le mot Moo"
          },
          "order": 2,
          "depends_on_question_id": None,
          "key": None,
          "show_for_values": {
              "en": None,
              "fr": None
          }
        }
      ], 
    },  # End section 1
    {
      "name": {
         "en": "Section 2",
         "fr": "Section 2 fr"
      },
      "description": {
         "en": "Description of the section 2",
         "fr": "Description de la section 2"
      },
      "order": 2,
      "depends_on_question_id": 1,
      "show_for_values": {
          "en": ["masters"],
          "fr": ["masters"],
      },
      "key": None,
      "questions": [
        {
          "id": 3,    
          "validation_regex": {
             "en": None, 
             "fr": None
          },
          "options": {
              "en": [
                  {"value": "the-matrix", "label": "The Matrix"}, 
                  {"value": "terminator", "label": "Terminator"}, 
                ],
              "fr": [
                  {"value": "the-matrix", "label": "La matrice"}, 
                  {"value": "terminator", "label": "Terminator"}, 
                ],
          },
          "description": {
              "en": "Question 3 en", 
              "fr": "Question 3 fr"
          },
          "headline": {
              "en": "Question 3 en", 
              "fr": "Question 3 fr"
          },
          "placeholder": {
              "en": "Select an Option...",
              "fr": "Sélectionnez une option"
          },
          "is_required": True, 
          "type": "multi-choice", 
          "validation_text": {
              "en": None,
              "fr": None
          },
          "order": 1,
          "depends_on_question_id": None,
          "key": "review-identifier",
          "show_for_values": {
              "en": None,
              "fr": None
          }
        },
      ], 
    },  # End section 2
  ]
}

class ApplicationFormCreateTest(ApiTestCase):
    """
    Test the Application Form Detail API's POST method
    """

    def _seed_data_create(self):
        self.event = self.add_event()
        self.system_admin = self.add_user(is_admin=True)
        self.event_admin = self.add_user(email='user2@user.com')
        self.normal_user = self.add_user(email='user3@user.com')
        self.event.add_event_role('admin', self.event_admin.id)
        db.session.commit()

    def test_event_admin_permission(self):
        """
        Tests that the application form can be created by an event admin
        """
        self._seed_data_create()

        response = self.app.post(
            '/api/v1/application-form-detail',
            data=json.dumps(APPLICATION_FORM_POST_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.event_admin.email)
        )

        self.assertEqual(response.status_code, 201)

    def test_non_event_admin_permission(self):
        """
        Test that the application form can't be created by a non event-admin
        """
        self._seed_data_create()

        response = self.app.post(
            '/api/v1/application-form-detail',
            data=json.dumps(APPLICATION_FORM_PUT_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.normal_user.email)
        )

        self.assertEqual(response.status_code, 403)

    def test_app_form_is_created(self):
        """
        Tests that the application form is created and an ID is returned
        """
        self._seed_data_create()

        response = self.app.post(
            '/api/v1/application-form-detail',
            data=json.dumps(APPLICATION_FORM_POST_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.system_admin.email)
        )
        response_data = json.loads(response.data)
        print('Response Data:', response_data)
        # Check that the ID is populated
        self.assertIsNotNone(response_data['id'])

        # Check that the fields are populated correctly in the response
        self.assertEqual(response_data['event_id'], APPLICATION_FORM_POST_DATA['event_id'])
        self.assertEqual(response_data['is_open'], APPLICATION_FORM_POST_DATA['is_open'])
        self.assertEqual(response_data['nominations'], APPLICATION_FORM_POST_DATA['nominations'])

        self.assertEqual(len(response_data['sections']), len(APPLICATION_FORM_POST_DATA['sections']))

        # Check a few fields in the sections themselves
        section0 = response_data['sections'][0]
        self.assertIsNotNone(section0['id'])
        self.assertDictEqual(section0['name'], APPLICATION_FORM_POST_DATA['sections'][0]['name'])
        self.assertEqual(len(section0['questions']), len(APPLICATION_FORM_POST_DATA['sections'][0]['questions']))

        section0_question0 = section0['questions'][0]
        self.assertIsNotNone(section0_question0['id'])
        self.assertDictEqual(section0_question0['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][0]['questions'][0]['headline'])

        section0_question1 = section0['questions'][1]
        self.assertIsNotNone(section0_question1['id'])
        self.assertDictEqual(section0_question1['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][0]['questions'][1]['headline'])

        section1 = response_data['sections'][1]
        self.assertIsNotNone(section1['id'])
        self.assertDictEqual(section1['name'], APPLICATION_FORM_POST_DATA['sections'][1]['name'])
        self.assertEqual(len(section1['questions']), len(APPLICATION_FORM_POST_DATA['sections'][1]['questions']))

        section1_question0 = section1['questions'][0]
        self.assertIsNotNone(section1_question0['id'])
        self.assertDictEqual(section1_question0['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][1]['questions'][0]['headline'])


APPLICATION_FORM_PUT_DATA = {
    "id": 1,
    "event_id": 1,
    "is_open": False,
    "nominations": False,
    "sections": [
        {  
            "id": 1,   # Existing section, just updates
            "description": "Updated description of the section",
            "order": 1,
            # "depends_on_question_id": 1,
            "show_for_values": None,
            "key": None,
            "questions": [
                {
                    "id": 1,
                    "validation_regex": None,  # Updated
                    "options": [
                        {"value": "undergrad", "label": "An undergraduate student"},
                        {"value": "masters", "label": "A masters student"},
                        {"value": "phd", "label": "A PHD student"},  # New
                    ],
                    "description": "Updated Description",  # Updated
                    "headline": "Question 1 Updated",  # Updated
                    "placeholder": "Select an Option...",
                    "is_required": True,  # Updated
                    "type": "multi-choice",
                    "validation_text": None,  # Updated
                    "order": 1
                }
            ],
            "name": "Section 1 Updated"
        },
        {
            "id": 2,  # Existing section with 1 new question
            "description": "Description of the section (UPDATED)",  # Updated
            "order": 3,  # Updated
            # "depends_on_question_id": 1,
            "show_for_values": None,
            "key": None,
            "questions": [
                {
                    "id": 2,
                    "validation_regex": "^\\W*(\\w+(\\W+|$)){0,10}$",  # Updated
                    "options": None,
                    "description": "Question description",
                    "headline": "Section 2, question 1",
                    "placeholder": "Some question",
                    "is_required": False,
                    "type": "long-text",  # Updated
                    "validation_text": "You must enter no more than 10 words",  # Updated
                    "order": 2  # Updated
                },
                {  # New because there is no ID
                    "validation_regex": "^\\W*(\\w+(\\W+|$)){0,150}$",
                    "options": None,
                    "description": "New Question description",
                    "headline": "Section 2, question 2",
                    "placeholder": "Some new question",
                    "is_required": True,
                    "type": "short-text",
                    "validation_text": "You must enter no more than 150 words",
                    "order": 1
                },
            ],
            "name": "Section 2"
        },
        {   # New section
            "description": "Description of the NEW section",
            "order": 2,
            # "depends_on_question_id": 1,
            "show_for_values": None,
            "key": None,
            "questions": [
                {
                    "validation_regex": "^\\W*(\\w+(\\W+|$)){0,150}$",
                    "options": None,
                    "description": "Question description",
                    "headline": "Section 3, question 1",
                    "placeholder": "Some question",
                    "is_required": True,
                    "type": "long-text",
                    "validation_text": "You must enter no more than 150 words",
                    "order": 1
                }
            ],
            "name": "Section 3"  
        }
    ]
}

class ApplicationFormUpdateTest(ApiTestCase):
    """
    Test that an application form's sections and question are updated by an admin with the correct permissions
    """

    def _seed_data_update(self):
        self.event = self.add_event()
        self.system_admin = self.add_user(is_admin=True)
        self.event_admin = self.add_user(email='user2@user.com')
        self.normal_user = self.add_user(email='user3@user.com')
        self.event.add_event_role('admin', self.event_admin.id)
        db.session.commit()

        # Set up the application form
        application_form = self.create_application_form(event_id=1, is_open=True, nominations=False)
        section1 = Section(application_form.id, 'Section 1', 'Old description of the section', 1)
        section2 = Section(application_form.id, 'Section 2', 'Description of the section', 2)
        section_deleted = Section(application_form.id, 'Section deleted', 'Description of the section', 3)
        db.session.add_all([section1, section2, section_deleted])
        db.session.commit()

        section1_question1 = Question(application_form.id, section1.id, 'Question 1', 'Select an Option...',
            1, 'multi-choice', 'Blah', 'Blah', False, 'Description', options=[
                {'value': 'undergrad', 'label': 'An undergraduate student'},
                {'value': 'masters', 'label': 'A masters student'}
            ])

        section2_question1 = Question(application_form.id, section2.id, 'Section 2, question 1', 'Some question',
            1, 'short-text', None, None, True, 'Question description', None)
        
        db.session.add_all([section1_question1, section2_question1])
        db.session.commit()

    def test_event_admin_permission(self):
        """
        Tests that the application form can be updated by an event admin
        """
        self._seed_data_update()

        response = self.app.put(
            '/api/v1/application-form',
            data=json.dumps(APPLICATION_FORM_PUT_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.event_admin.email)
        )

        self.assertEqual(response.status_code, 200)

    def test_non_event_admin_permission(self):
        """
        Test that the application form can't be updated by a non event-admin
        """
        self._seed_data_update()

        response = self.app.put(
            '/api/v1/application-form',
            data=json.dumps(APPLICATION_FORM_PUT_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.normal_user.email)
        )

        self.assertEqual(response.status_code, 403)

    def test_app_form_updated(self):
        self._seed_data_update()

        response = self.app.put(
            '/api/v1/application-form',
            data=json.dumps(APPLICATION_FORM_PUT_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.system_admin.email)
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.data)
        print("Response data:", response_data)

        self.assertEqual(response_data['id'], 1)
        self.assertEqual(response_data['event_id'], 1)
        self.assertFalse(response_data['is_open'])
        self.assertFalse(response_data['nominations'])
        self.assertEqual(len(response_data['sections']), 3)

        # Check section 1 (updated)
        section1_actual = response_data['sections'][0]
        section1_expected = APPLICATION_FORM_PUT_DATA['sections'][0]
        for key in section1_expected.keys():
            if key == 'questions':
                continue
            self.assertEqual(section1_actual[key], section1_expected[key],
                             '{}: actual "{}" vs expected "{}"'.format(key, section1_actual[key], section1_expected[key]))

        self.assertEqual(len(section1_actual['questions']), 1)

        # Check question 1 in section 1 (updated)
        section1_question1_actual = response_data['sections'][0]['questions'][0]
        section1_question1_expected = APPLICATION_FORM_PUT_DATA['sections'][0]['questions'][0]
        for key in section1_question1_expected.keys():
            if key == 'options':
                continue
            self.assertEqual(section1_question1_actual[key], section1_question1_expected[key], key)

        section1_question1_options_actual = response_data['sections'][0]['questions'][0]['options']
        section1_question1_options_expected = APPLICATION_FORM_PUT_DATA['sections'][0]['questions'][0]['options']
        self.assertEqual(len(section1_question1_options_actual), len(section1_question1_options_expected))        

        # Check section 2 (updated)
        section2_actual = response_data['sections'][1]
        section2_expected = APPLICATION_FORM_PUT_DATA['sections'][1]
        for key in section2_expected.keys():
            if key == 'questions':
                continue
            self.assertEqual(section2_actual[key], section2_expected[key])

        self.assertEqual(len(section2_actual['questions']), len(section2_expected['questions']))

        # Check question 1 in section 2 (updated)
        section2_question1_actual = response_data['sections'][1]['questions'][0]
        section2_question1_expected = APPLICATION_FORM_PUT_DATA['sections'][1]['questions'][0]
        for key in section2_question1_expected.keys():
            self.assertEqual(section2_question1_actual[key], section2_question1_expected[key], key)

        # Check question 2 in section 2 (NEW)
        section2_question2_actual = response_data['sections'][1]['questions'][1]
        section2_question2_expected = APPLICATION_FORM_PUT_DATA['sections'][1]['questions'][1]
        self.assertIsNotNone(section2_question1_actual['id'])
        for key in section2_question2_expected.keys():
            self.assertEqual(section2_question2_actual[key], section2_question2_expected[key], key)

        # Check section 3 (NEW)
        section3_actual = response_data['sections'][2]
        section3_expected = APPLICATION_FORM_PUT_DATA['sections'][2]
        self.assertIsNotNone(section3_actual['id'])
        for key in section3_expected.keys():
            if key == 'questions':
                continue
            self.assertEqual(section3_actual[key], section3_expected[key], key)

        self.assertEqual(len(section3_actual['questions']), len(section3_expected['questions']))

        # Check question 1 in section 3 (NEW)
        section3_question1_actual = response_data['sections'][2]['questions'][0]
        section3_question1_expected = APPLICATION_FORM_PUT_DATA['sections'][2]['questions'][0]
        self.assertIsNotNone(section3_question1_actual['id'])
        for key in section3_question1_expected.keys():
            self.assertEqual(section3_question1_actual[key], section3_question1_expected[key], key)


class QuestionListApiTest(ApiTestCase):
    def _seed_static_data(self):
        self.user1 = self.add_user('user1@mail.com')
        self.user2 = self.add_user('user2@mail.com')
        self.event = self.add_event()
        self.event.add_event_role('admin', self.user1.id)
        db.session.commit()

        self.user1header = self.get_auth_header_for('user1@mail.com')
        self.user2header = self.get_auth_header_for('user2@mail.com')

        self.application_form = self.create_application_form()

        # Deliberately create these in reverse order to test ordering
        self.section1 = self.add_section(self.application_form.id, order=2)
        self.section2 = self.add_section(self.application_form.id, order=1)

        self.section1question1 = self.add_question(self.application_form.id, self.section1.id, order=2)
        self.add_question_translation(
            self.section1question1.id, 'en', headline='English Section 1 Question 1'
        )
        self.add_question_translation(
            self.section1question1.id, 'fr', headline='French Section 1 Question 1'
        )

        self.section1question2 = self.add_question(self.application_form.id, self.section1.id, order=1)
        self.add_question_translation(
            self.section1question2.id, 'en', headline='English Section 1 Question 2'
        )
        self.add_question_translation(
            self.section1question2.id, 'fr', headline='French Section 1 Question 2'
        )

        self.section2question1 = self.add_question(self.application_form.id, self.section2.id, order=1)
        self.add_question_translation(self.section2question1.id, 'en', 'English Section 2 Question 1')
        # Deliberately not adding a French translation to test defaulting behaviour

    def test_get(self):
        """Test a typical get request."""
        self._seed_static_data()

        response = self.app.get(
            '/api/v1/questions',
            headers=self.user1header,
            query_string={'event_id': 1, 'language': 'en'}
        )

        data = json.loads(response.data)

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['question_id'], 3)
        self.assertEqual(data[0]['headline'], 'English Section 2 Question 1')
        self.assertEqual(data[0]['type'], 'short-text')

        self.assertEqual(data[1]['question_id'], 2)
        self.assertEqual(data[1]['headline'], 'English Section 1 Question 2')
        self.assertEqual(data[1]['type'], 'short-text')

        self.assertEqual(data[2]['question_id'], 1)
        self.assertEqual(data[2]['headline'], 'English Section 1 Question 1')
        self.assertEqual(data[2]['type'], 'short-text')

    def test_get_language(self):
        """Test get in a specified language and defaulting."""
        self._seed_static_data()

        response = self.app.get(
            '/api/v1/questions',
            headers=self.user1header,
            query_string={'event_id': 1, 'language': 'fr'}
        )

        data = json.loads(response.data)

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['question_id'], 3)
        self.assertEqual(data[0]['headline'], 'English Section 2 Question 1')
        self.assertEqual(data[0]['type'], 'short-text')

        self.assertEqual(data[1]['question_id'], 2)
        self.assertEqual(data[1]['headline'], 'French Section 1 Question 2')
        self.assertEqual(data[1]['type'], 'short-text')

        self.assertEqual(data[2]['question_id'], 1)
        self.assertEqual(data[2]['headline'], 'French Section 1 Question 1')
        self.assertEqual(data[2]['type'], 'short-text')

    def test_event_admin(self):
        """Test that a non event admin is blocked from accessing the data."""
        self._seed_static_data()

        response = self.app.get(
            '/api/v1/questions',
            headers=self.user2header,  # Not an event admin
            query_string={'event_id': 1, 'language': 'fr'}
        )

        self.assertEqual(response.status_code, 403)
