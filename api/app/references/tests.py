import copy
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
        self.other_user_data = self.add_user('someuser@mail.com')

        test_event = self.add_event()
        test_event.add_event_role('admin', 1)
        self.test_event_data = copy.deepcopy(test_event.__dict__)
        self.add_to_db(test_event)

        self.test_form = self.create_application_form(test_event.id, True, False)

        self.test_response = Response(
            self.test_form.id, self.other_user_data.id)
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
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resference_requests), 1)


    def test_get_reference_request_by_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        response = self.app.get(
            '/api/v1/reference-request', data={'id':1}, headers=self.headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['firstname'], 'John')

    def test_get_reference_request_by_response_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_req2 = ReferenceRequest(1, 'Mrs', 'John', 'Jones', 'Manager', 'john@email.com')
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)
        response = self.app.get(
            '/api/v1/reference-request/list', data={'response_id':1}, headers=self.headers)
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_reference_request_detail_by_token(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        response = self.app.get(
                '/api/v1/reference-request/detail', data={'token': reference_req.token}, headers=self.headers)
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['candidate_title'], self.other_user_data.user_title)
        self.assertEqual(data['candidate_firstname'], self.other_user_data.firstname)
        self.assertEqual(data['candidate_lastname'], self.other_user_data.lastname)
        self.assertEqual(data['candidate_email'], self.other_user_data.email)
        self.assertEqual(data['relation'], reference_req.relation)
        self.assertEqual(data['name'], self.test_event_data['name'])
        self.assertEqual(data['description'], self.test_event_data['description'])
        self.assertEqual(data['is_application_open'], True)
        self.assertEqual(data['email_from'], self.test_event_data['email_from'])
        self.assertIsNone(data['reference_submitted_timestamp'])

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
        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            '/api/v1/reference', data={'response_id':1}, headers=self.headers)
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        reference_request = reference_request_repository.get_by_id(1)
        self.assertEqual(reference_request.has_reference(), True)

