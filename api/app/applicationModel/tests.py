import json
from datetime import datetime, timedelta
from pytz import UTC
from app import db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.applicationModel.models import ApplicationForm, Section, Question
from app.organisation.models import Organisation
from app.events.models import EventType


class ApplicationFormApiTest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('IndabaX')
        self.start_time = datetime.now() + timedelta(days=30)
        self.end_time = datetime.now() + timedelta(days=60)

        test_event = self.add_event('Test Event', 'Event Description', self.start_time, self.end_time)
        db.session.add(test_event)
        db.session.commit()
        test_form = self.create_application_form(
            test_event.id, True, False)
        db.session.add(test_form)
        db.session.commit()
        test_section = Section(
            test_form.id, 'Test Section', 'Test Description', 1)
        db.session.add(test_section)
        db.session.commit()
        test_question = Question(
            application_form_id=test_form.id, section_id=test_section.id, 
            headline='Test Question Headline', placeholder='Test question placeholder', 
            order=1, questionType='multi-choice', 
            validation_regex=None, is_required=True,
            description='Test Question Description', options=None)
        db.session.add(test_question)
        db.session.flush()

    def test_get_form(self):
        self.seed_static_data()

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
