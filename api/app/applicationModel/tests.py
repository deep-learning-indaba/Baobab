import json
from datetime import datetime, timedelta
from pytz import UTC
from app import db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.applicationModel.models import ApplicationForm, Section, Question


class ApplicationFormApiTest(ApiTestCase):

    def seed_static_data(self):
        self.start_time = datetime.now() + timedelta(days=30)
        self.end_time = datetime.now() + timedelta(days=60)

        test_event = Event('Test Event', 'Event Description',
                           self.start_time, self.end_time)
        db.session.add(test_event)
        db.session.commit()
        test_form = ApplicationForm(
            test_event.id, True, self.end_time)
        db.session.add(test_form)
        db.session.commit()
        test_section = Section(
            test_form.id, 'Test Section', 'Test Description', 1)
        db.session.add(test_section)
        db.session.commit()
        test_question = Question(test_form.id, test_section.id, 'Test Question Headline',
                                 'Test question placeholder', 1, 'multi-choice', None, True, 'Test Question Description', None)
        db.session.add(test_question)
        db.session.flush()

    def test_get_form(self):
        self.seed_static_data()

        response = self.app.get('/api/v1/application-form?event_id=1')
        data = json.loads(response.data)
        assert data['deadline'] == self.end_time.strftime(
            "%a, %d %b %Y %H:%M:%S") + " -0000"
        assert data['event_id'] == 1
        assert data['is_open'] == True
        assert data['sections'][0]['description'] == 'Test Description'
        assert data['sections'][0]['name'] == 'Test Section'
        assert data['sections'][0]['order'] == 1
        assert data['sections'][0]['questions'][0]['description'] == 'Test Question Description'
        assert data['sections'][0]['questions'][0]['order'] == 1
        assert data['sections'][0]['questions'][0]['type'] == 'multi-choice'
