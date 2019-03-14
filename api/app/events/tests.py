import json

from datetime import datetime, timedelta
from app import db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.responses.models import Response, Answer
from app.events.models import Event
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question


class EventsAPITest(ApiTestCase):

    def seed_static_data(self):
        test_country = Country('Indaba Land')
        db.session.add(test_country)
        db.session.commit()

        test_category = UserCategory('Category1')
        db.session.add(test_category)
        db.session.commit()

        self.test_user = AppUser('something@email.com', 'Some', 'Thing', 'Mr', 1, 1,
                                 'Male', 'University', 'Computer Science', 'None', 1,
                                 datetime(1984, 12, 12),
                                 'Zulu',
                                 '123456')
        self.test_user.verified_email = True
        db.session.add(self.test_user)
        db.session.commit()

        test_event = Event('Test Event', 'Event Description',
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60))
        db.session.add(test_event)
        db.session.commit()

        self.test_form = ApplicationForm(
            test_event.id, True, datetime.now() + timedelta(days=60))
        db.session.add(self.test_form)
        db.session.commit()

        db.session.flush()

    def test_get_events_unauthed(self):
        self.seed_static_data()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Apply now'

    def test_get_events_applied(self):
        self.seed_static_data()

        test_response = Response(
            self.test_form.id, self.test_user.id, is_submitted=True)
        db.session.add(test_response)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': '123456'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Applied'

    def test_get_events_withdrawn(self):
        self.seed_static_data()

        test_response = Response(
            self.test_form.id, self.test_user.id, is_submitted=True, is_withdrawn=True)
        db.session.add(test_response)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': '123456'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application withdrawn'

    def test_get_events_closed(self):
        self.seed_static_data()

        self.test_form.deadline = datetime.now() - timedelta(days=1)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': '123456'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application closed'

    def test_get_events_unauthed_closed(self):
        self.seed_static_data()

        self.test_form.deadline = datetime.now() - timedelta(days=1)
        db.session.commit()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application closed'

    def test_get_events_not_available(self):
        self.seed_static_data()

        db.session.delete(self.test_form)
        db.session.commit()

        response = self.app.post('/api/v1/authenticate', data={
            'email': 'something@email.com',
            'password': '123456'
        })

        assert response.status_code == 200

        data = json.loads(response.data)

        response = self.app.get(
            '/api/v1/events', headers={'Authorization': data["token"]})
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application not available'

    def test_get_events_unauthed_not_available(self):
        self.seed_static_data()

        db.session.delete(self.test_form)
        db.session.commit()

        response = self.app.get('/api/v1/events')
        data = json.loads(response.data)

        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["description"] == 'Event Description'
        assert data[0]["status"] == 'Application not available'
