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

        self.test_event = self.add_event({'en': 'Test Event'}, {'en': 'Event Description'}, self.start_time, self.end_time)
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