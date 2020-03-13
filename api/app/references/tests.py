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

        nomination_event = self.add_event(key="AWARD_NOMINATIONS_ONLY")
        nomination_event.add_event_role('admin', 1)
        self.test_nomination_event_data = copy.deepcopy(nomination_event.__dict__)
        self.add_to_db(nomination_event)

        self.test_form = self.create_application_form(test_event.id, True, False)
        self.add_to_db(self.test_form)

        self.test_nomination_form = self.create_application_form(nomination_event.id, True, True)

        sections = [
            Section(test_event.id, 'Nominations', 'Nominate yourself for an award', 1),
            Section(nomination_event.id, 'Nominations', 'Nominate someone else for an award', 1)
        ]
        db.session.add_all(sections)
        db.session.commit()

        questions = [
            Question(test_event.id, sections[0].id,
                     'name',
                     'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(test_event.id, sections[0].id,
                     'email', 'Enter 50 to 150 words', 2, 'long_text', ''),
            Question(nomination_event.id, sections[1].id,
                     'name', 'Enter 50 to 150 words', 1, 'long_text', ''),
            Question(nomination_event.id, sections[1].id,
                     'email', 'Enter 50 to 150 words', 2, 'long_text', ''),
        ]
        db.session.add_all(questions)
        db.session.commit()

        self.test_response = Response(
            self.test_form.id, self.other_user_data.id)
        self.add_to_db(self.test_response)
        answers = [Answer(self.test_response.id, question.id,
                          "answer to '{}' from section {}".format(question.headline, question.section_id))
                   for question in questions]
        db.session.add_all(answers)
        db.session.commit()

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
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_reference_request_detail_by_token(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        response = self.app.get(
                '/api/v1/reference-request/detail', data={'token': reference_req.token}, headers=self.headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('name' in data['candidate'])
        self.assertTrue('email' in data['candidate'])
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

    def test_reference_api_update(self):
        self._seed_data()
        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            'token':reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }
        REFERENCE_DETAIL_2 = {
            'token':reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-79000',
        }
        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.headers)
        self.assertEqual(response.status_code, 201)

        response = self.app.put(
            '/api/v1/reference', data=REFERENCE_DETAIL_2, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        response = self.app.get(
            '/api/v1/reference', data={'response_id':1}, headers=self.headers)
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        reference_request = reference_request_repository.get_by_id(1)
        self.assertEqual(reference_request.has_reference(), True)
        reference = reference_request_repository.get_reference_by_reference_request_id(reference_request.id)
        self.assertEqual(reference.uploaded_document, REFERENCE_DETAIL_2['uploaded_document'])

    def test_reference_application_closed(self):

        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png')
        other_user_data = self.add_user('someuser@mail.com')

        test_event = self.add_event()
        test_event.add_event_role('admin', 1)
        test_event.set_application_close(datetime.now())

        self.add_to_db(test_event)
        self.test_form = self.create_application_form(test_event.id, True, False)
        self.add_to_db(self.test_form)

        self.test_response = Response(
            self.test_form.id, other_user_data.id)
        self.add_to_db(self.test_response)
        self.headers = self.get_auth_header_for("someuser@mail.com")

        db.session.flush()

        reference_req = ReferenceRequest(1, 'Mr', 'John', 'Snow', 'Supervisor', 'common@email.com')
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            'token':reference_req.token,
            'uploaded_document': 'DOCT-UPLOAD-78999',
        }
        response = self.app.post(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.headers)
        self.assertEqual(response.status_code, 403)

        response = self.app.put(
            '/api/v1/reference', data=REFERENCE_DETAIL, headers=self.headers)
        self.assertEqual(response.status_code, 403)
