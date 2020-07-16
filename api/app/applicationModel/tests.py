import json
from datetime import datetime, timedelta
from pytz import UTC
from app import db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.applicationModel.models import ApplicationForm, Section, Question
from app.organisation.models import Organisation
from app.events.models import EventType
from app.applicationModel.repository import ApplicationFormRepository as application_form_repository


class ApplicationFormApiTest(ApiTestCase):

    def setUp(self):
        super(ApplicationFormApiTest, self).setUp()  # python2 syntax
        self._seed_data()

    def _seed_data(self):
        self.add_organisation('IndabaX')
        self.start_time = datetime.now() + timedelta(days=30)
        self.end_time = datetime.now() + timedelta(days=60)

        self.test_event = self.add_event('Test Event', 'Event Description', self.start_time, self.end_time)
        self.add_to_db(self.test_event)
        self.test_form = self.create_application_form(
            self.test_event.id, True, False)
        self.add_to_db(self.test_form)
        self.test_section = Section(
            self.test_form.id, 'Test Section', 'Test Description', 1)
        self.add_to_db(self.test_section)
        self.test_question = Question(
            application_form_id=self.test_form.id, section_id=self.test_section.id,
            headline='Test Question Headline', placeholder='Test question placeholder',
            order=1, questionType='multi-choice',
            validation_regex=None, is_required=True,
            description='Test Question Description', options=None)
        self.add_to_db(self.test_question)
        # Section 2
        self.test_section2 = Section(
            self.test_form.id, 'Test Section 2', 'Test Description 2', 2)
        self.add_to_db(self.test_section2)
        self.test_question2 = Question(
            application_form_id=self.test_form.id, section_id=self.test_section2.id,
            headline='Test Question 2 Headline', placeholder='Test question 2 placeholder',
            order=1, questionType='text',
            validation_regex=None, is_required=True,
            description='Test Question 2 Description')
        self.add_to_db(self.test_question2)

    def test_get_form(self):
        response = self.app.get('/api/v1/application-form?event_id=1')
        data = json.loads(response.data)
        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['is_open'], True)
        self.assertEqual(data['sections'][0]['description'], 'Test Description')
        self.assertEqual(data['sections'][0]['name'], 'Test Section')
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['description'], 'Test Question Description')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['nominations'], False)

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
            "description": "Description of the section",
            "order": 1,
            "questions": [
                {
                    "validation_regex": None,
                    "options": [
                        {"value": "undergrad", "label": "An undergraduate student"},
                        {"value": "masters", "label": "A masters student"},
                    ],
                    "description": None,
                    "headline": "Question 1",
                    "placeholder": "Select an Option...",
                    "is_required": True,
                    "type": "multi-choice",
                    "validation_text": None,
                    "order": 1
                }
            ],
            "name": "Section 1"
        },
        {
            "description": "Description of the section",
            "order": 2,
            "questions": [
                {
                    "validation_regex": "^\\W*(\\w+(\\W+|$)){0,150}$",
                    "options": None,
                    "description": "Question description",
                    "headline": "Section 2, question 1",
                    "placeholder": "Some question",
                    "is_required": True,
                    "type": "long-text",
                    "validation_text": "You must enter no more than 150 words",
                    "order": 1
                },
                {
                    "validation_regex": "^\\W*(\\w+(\\W+|$)){0,10}$",
                    "options": None,
                    "description": "Question description",
                    "headline": "Section 2, question 2",
                    "placeholder": "Some question",
                    "is_required": False,
                    "type": "long-text",
                    "validation_text": "You must enter no more than 10 words",
                    "order": 2
                }
            ],
            "name": "Section 2"
        }
    ]
}


class ApplicationFormCreateTest(ApiTestCase):
    """
    Test that an application form is created by an event admin with the correct permission
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
            '/api/v1/application-form',
            data=json.dumps(APPLICATION_FORM_POST_DATA),
            content_type='application/json',
            headers=self.get_auth_header_for(self.event_admin.email)
        )

        self.assertEqual(response.status_code, 201)

    def test_non_event_admin_permission(self):
        """
        Test that the application form can't be created by a non event-admin
        """
        self._seed_data_update()

        response = self.app.post(
            '/api/v1/application-form',
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
            '/api/v1/application-form',
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
        self.assertEqual(section0['name'], APPLICATION_FORM_POST_DATA['sections'][0]['name'])
        self.assertEqual(len(section0['questions']), len(APPLICATION_FORM_POST_DATA['sections'][0]['questions']))

        section0_question0 = section0['questions'][0]
        self.assertIsNotNone(section0_question0['id'])
        self.assertEqual(section0_question0['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][0]['questions'][0]['headline'])

        section1 = response_data['sections'][1]
        self.assertIsNotNone(section1['id'])
        self.assertEqual(section1['name'], APPLICATION_FORM_POST_DATA['sections'][1]['name'])
        self.assertEqual(len(section1['questions']), len(APPLICATION_FORM_POST_DATA['sections'][1]['questions']))

        section1_question0 = section1['questions'][0]
        self.assertIsNotNone(section1_question0['id'])
        self.assertEqual(section1_question0['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][1]['questions'][0]['headline'])

        section1_question1 = section1['questions'][1]
        self.assertIsNotNone(section1_question1['id'])
        self.assertEqual(section1_question1['headline'],
                         APPLICATION_FORM_POST_DATA['sections'][1]['questions'][1]['headline'])


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

# TODO: What about a deleted section or deleted question? 


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
        db.session.add_all([section1, section2])
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
            self.assertEqual(section1_actual[key], section1_expected[key])

        self.assertEqual(len(section1_actual['questions']), 1)

        # Check question 1 in section 1 (updated)
        section1_question1_actual = response_data['sections'][0]['questions'][0]
        section1_question1_expected = APPLICATION_FORM_PUT_DATA['sections'][0]['questions'][0]
        for key in section1_question1_expected.keys():
            if key == 'options':
                continue
            self.assertEqual(section1_question1_actual[key], section1_question1_expected[key])

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
            self.assertEqual(section2_question1_actual[key], section2_question1_expected[key])

        # Check question 2 in section 2 (NEW)
        section2_question2_actual = response_data['sections'][1]['questions'][1]
        section2_question2_expected = APPLICATION_FORM_PUT_DATA['sections'][1]['questions'][1]
        self.assertIsNotNone(section2_question1_actual['id'])
        for key in section2_question2_expected.keys():
            self.assertEqual(section2_question2_actual[key], section2_question2_expected[key])

        # Check section 3 (NEW)
        section3_actual = response_data['sections'][2]
        section3_expected = APPLICATION_FORM_PUT_DATA['sections'][2]
        self.assertIsNotNone(section3_actual['id'])
        for key in section3_expected.keys():
            if key == 'questions':
                continue
            self.assertEqual(section3_actual[key], section3_expected[key])

        self.assertEqual(len(section3_actual['questions']), len(section3_expected['questions']))

        # Check question 1 in section 3 (NEW)
        section3_question1_actual = response_data['sections'][2]['questions'][0]
        section3_question1_expected = APPLICATION_FORM_PUT_DATA['sections'][2]['questions'][0]
        self.assertIsNotNone(section3_question1_actual['id'])
        for key in section3_question1_expected.keys():
            self.assertEqual(section3_question1_actual[key], section3_question1_expected[key])
