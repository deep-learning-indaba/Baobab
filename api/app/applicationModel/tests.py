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
        self.section_translation_en = self.add_section_translation(self.section.id, 'en', 'Test Section', 'Test Description')
        self.section_translation_fr = self.add_section_translation(self.section.id, 'fr', 'Section francaise', 'Description du test')
        self.question = self.add_question(self.form.id, self.section.id, question_type='multi-choice')
        self.question_translation_en = self.add_question_translation(self.question.id, 'en', 'English Headline')
        self.question_translation_fr = self.add_question_translation(self.question.id, 'fr', 'Titre francais')

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
        self.assertEqual(data['sections'][0]['description'], 'Test Description')
        self.assertEqual(data['sections'][0]['name'], 'Test Section')
        self.assertEqual(data['sections'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['headline'], 'English Headline')
        self.assertEqual(data['sections'][0]['questions'][0]['order'], 1)
        self.assertEqual(data['sections'][0]['questions'][0]['type'], 'multi-choice')
        self.assertEqual(data['nominations'], False)