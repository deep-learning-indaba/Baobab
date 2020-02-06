import json

from datetime import datetime, date
from app import app, db, LOGGER
from app.events.models import Event
from app.utils.testing import ApiTestCase
from app.responses.models import Response, Answer
from app.events.models import Event, EventRole
from app.users.models import AppUser, Country, UserCategory
from app.applicationModel.models import ApplicationForm, Section, Question
from app.utils.errors import FORBIDDEN
from app.organisation.models import Organisation
from app.references.repository import ReferenceRequestRepository as reference_request_repository
from app.references.models import ReferenceRequest


class ReferenceAPITest(ApiTestCase):

    def _seed_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png')
        other_user_data = self.add_user('someuser@mail.com')

        test_event = self.add_event()
        self.test_form = ApplicationForm(test_event.id, True, date(2019, 3, 24))
        self.add_to_db(self.test_form)
        
        self.test_response = Response(
            self.test_form.id, other_user_data.id)
        self.add_to_db(self.test_response)
        self.headers = self.get_auth_header_for("someuser@mail.com")

        db.session.flush()

    def test_create_reference_request(self):
        self._seed_data()
        REFERENCE_REQUEST_DETAIL = {
            'response_id':1, 
            'title': 'Mr',
            'firstname': 'John',
            'lastname':'Snow', 
            'relation' : 'Suppervisor',
            'email' :'common@email.com'
        }
        response = self.app.post(
            '/api/v1/reference-request', data=REFERENCE_REQUEST_DETAIL, headers=self.headers)
        resference_requests = reference_request_repository.get_all()
        assert len(resference_requests) == 1
        assert response.status_code == 201


    def test_get_reference_request_by_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        response = self.app.get(
            '/api/v1/reference-request', data={'id':1}, headers=self.headers)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['firstname'] == 'John'

    def test_get_reference_request_by_response_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_req2 = ReferenceRequest(1, 'Mrs', 'John', 'Jones', 'Manager', 'john@email.com')
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)
        response = self.app.get(
            '/api/v1/reference-request/list', data={'response_id':1}, headers=self.headers)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert len(data) == 2

    def test_reference_api(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            'token':reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }
        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.headers)
        assert response.status_code == 201

        response = self.app.get(
            '/api/v1/reference', data={'response_id':1}, headers=self.headers)
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert len(data) == 1
