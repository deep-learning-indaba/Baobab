import json

from app import db
from app.utils.testing import ApiTestCase
from app.applicationModel.models import ApplicationForm, Section, Question
from app.events.models import Event



class UserApiTest(ApiTestCase):
    test_event = Event('Test Event', 'Event Description', '2019/02/24', '2019/03/24')
    test_form = ApplicationForm(1, True, '2019/03/24')
    test_section = Section(test_form.id, 'Test Section', 'Test Description', 1)
    test_question = Question(test_form.id, test_section.id, 'Test Question Description', 1, 'Test Type')


    def seed_static_data(self):
        test_event = Event('Test Event', 'Event Description', '2019/02/24', '2019/03/24')
        db.session.add(test_event)
        db.session.commit()
        test_form = ApplicationForm(1, True, '2019/03/24')
        db.session.add(test_form)
        db.session.commit()
        test_section = Section(test_form.id, 'Test Section', 'Test Description', 1)
        db.session.add(test_section)
        db.session.commit()
        test_question = Question(test_form.id, test_section.id, 'Test Question Description', 1, 'Test Type')
        db.session.add(test_question)
        db.session.flush()
        return test_form, test_section, test_question, test_event
    
    def delete_seed_data(self, form, section, question, event):
        db.delete(form)
        db.delete(section)
        db.delete(question)
        db.delete(event)
        db.flush()

    def test_get_user(self):
        test_form, test_section, test_question, test_event = self.seed_static_data()  

        response = self.app.get('/api/v1/application-form?event_id=1')
        data = json.loads(response.data)
        assert data['deadline'] == '2019/03/24'
        assert data['event_id'] == 1
        assert data['is_open'] == True
        assert data['sections']['description'] == 'Test Description'
        assert data['sections']['name'] == 'Test Section'
        assert data['sections']['order'] == 1
        assert data['sections']['questions']['description'] == 'Test Question Description'
        assert data['sections']['questions']['order'] == 1
        assert data['sections']['questions']['type'] == 'Test Type'

        self.delete_seed_data(test_form, test_section, test_question, test_event)



