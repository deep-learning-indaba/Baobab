import json
from datetime import datetime, timedelta
from app import db
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.applicationModel.models import ApplicationForm, Section, Question


class ApplicationFormApiTest(ApiTestCase):

    def seed_static_data(self):
        test_event = Event('Test Event', 'Event Description',
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60))
        db.session.add(test_event)
        db.session.commit()
        test_form = ApplicationForm(
            test_event.id, True, datetime.now() + timedelta(days=60))
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
        assert data['deadline'] == 'Sun, 24 Mar 2019 00:00:00 -0000'
        assert data['event_id'] == 1
        assert data['is_open'] == True
        assert data['sections'][0]['description'] == 'Test Description'
        assert data['sections'][0]['name'] == 'Test Section'
        assert data['sections'][0]['order'] == 1
        assert data['sections'][0]['questions'][0]['description'] == 'Test Question Description'
        assert data['sections'][0]['questions'][0]['order'] == 1
        assert data['sections'][0]['questions'][0]['type'] == 'multi-choice'
