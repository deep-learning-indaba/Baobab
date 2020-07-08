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


class ApplicationFormCreateTest(ApiTestCase):
    """
    Test that an application form is created by an event admin
    """
    def _seed_data_create(self):
        """
        Mock data used for test simulation
        """
        pass

    def test_event_admin_permission(self):
        """
        Tests that the application form is being created by a user with the correct permissions
        """
        pass

    def test_app_form_is_created(self):
        """
        Tests that the application form is created and an ID is returned
        """
        pass

    def test_sections_are_created(self):
        """
        Tests that the correct sections are added and can be accessed by the respective app id
        """
        pass


class ApplicationFormUpdateTest(ApiTestCase):
    """
    Test that an application form's sections and question are updated
    """
    def _seed_data_update(self):
        """
        Mock data used for test simulation
        """
        pass

    def test_section_id_matches_app_id(self):
        """
        Confirm the sections to be updated belong to the respective application form
        """
        pass

    def test_question_matches_app_sesction_id(self):
        pass

    def test_updated_app_form_returned(self):
        """
        Tests that the new, updated application form is returned
        """
        pass