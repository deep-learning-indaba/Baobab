import copy
import json
from datetime import date, datetime

from app import LOGGER, app, db
from app.applicationModel.models import ApplicationForm, Question, Section
from app.events.models import Event, EventRole
from app.organisation.models import Organisation
from app.references.models import ReferenceRequest
from app.references.repository import (
    ReferenceRequestRepository as reference_request_repository,
)
from app.responses.models import Answer, Response
from app.users.models import AppUser, Country, UserCategory
from app.utils.errors import FORBIDDEN
from app.utils.testing import ApiTestCase


class ReferenceAPITest(ApiTestCase):
    def _seed_data(self):
        self.add_organisation("Deep Learning Indaba", "blah.png", "blah_big.png")
        self.first_user_data = self.add_user(
            "firstuser@mail.com", "First", "User", "Mx"
        )
        self.other_user_data = self.add_user("someuser@mail.com")

        test_event = self.add_event()
        test_event.add_event_role("admin", 1)
        self.test_event_data = copy.deepcopy(test_event.__dict__)
        self.test_event_data["name"] = test_event.get_name("en")
        self.test_event_data["description"] = test_event.get_description("en")
        self.add_to_db(test_event)

        nomination_event = self.add_event(key="AWARD_NOMINATIONS_ONLY")
        nomination_event.add_event_role("admin", 1)
        self.test_nomination_event_data = copy.deepcopy(nomination_event.__dict__)
        self.add_to_db(nomination_event)

        self.test_form = self.create_application_form(test_event.id, True, False)
        self.add_to_db(self.test_form)

        self.test_nomination_form = self.create_application_form(
            nomination_event.id, True, True
        )

        sections = [
            Section(test_event.id, 1),
            Section(nomination_event.id, 1, key="nominee_section"),
        ]
        db.session.add_all(sections)
        db.session.commit()

        questions = [
            Question(self.test_form.id, sections[0].id, 1, "long_text"),
            Question(self.test_form.id, sections[0].id, 2, "long_text"),
            Question(self.test_nomination_form.id, sections[1].id, 1, "long_text"),
            Question(self.test_nomination_form.id, sections[1].id, 2, "long_text"),
            Question(self.test_nomination_form.id, sections[1].id, 3, "long_text"),
            Question(self.test_nomination_form.id, sections[1].id, 4, "long_text"),
        ]
        questions[0].key = "nominating_capacity"
        questions[2].key = "nomination_title"
        questions[3].key = "nomination_firstname"
        questions[4].key = "nomination_lastname"
        questions[5].key = "nomination_email"
        db.session.add_all(questions)
        db.session.commit()

        self.test_response1 = self.add_response(  # Self nomination
            self.test_form.id, self.first_user_data.id
        )

        self.add_to_db(self.test_response1)
        answers = [
            Answer(self.test_response1.id, questions[0].id, "self"),
            Answer(self.test_response1.id, questions[1].id, "Blah"),
        ]
        db.session.add_all(answers)
        db.session.commit()

        self.test_response2 = self.add_response(  # Nominating other
            self.test_form.id, self.other_user_data.id
        )

        self.add_to_db(self.test_response2)
        answers = [
            Answer(self.test_response2.id, questions[0].id, "other"),
            Answer(self.test_response2.id, questions[1].id, "Blah"),
            Answer(self.test_response2.id, questions[2].id, "Mx"),
            Answer(self.test_response2.id, questions[3].id, "Skittles"),
            Answer(self.test_response2.id, questions[4].id, "Cat"),
            Answer(self.test_response2.id, questions[5].id, "skittles@box.com"),
        ]
        db.session.add_all(answers)
        db.session.commit()

        self.first_headers = self.get_auth_header_for("firstuser@mail.com")
        self.other_headers = self.get_auth_header_for("someuser@mail.com")

        self.add_email_template("reference-request-self-nomination")
        self.add_email_template("reference-request")

        db.session.flush()

    def test_create_reference_request(self):
        self._seed_data()
        REFERENCE_REQUEST_DETAIL = {
            "response_id": 1,
            "title": "Mr",
            "firstname": "John",
            "lastname": "Snow",
            "relation": "Suppervisor",
            "email": "common@email.com",
        }
        response = self.app.post(
            "/api/v1/reference-request",
            data=REFERENCE_REQUEST_DETAIL,
            headers=self.first_headers,
        )
        resference_requests = reference_request_repository.get_all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(resference_requests), 1)

    def test_get_reference_request_by_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        response = self.app.get(
            "/api/v1/reference-request", data={"id": 1}, headers=self.first_headers
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["title"], "Mr")
        self.assertEqual(data["firstname"], "John")
        self.assertEqual(data["lastname"], "Snow")
        self.assertEqual(data["relation"], "Supervisor")
        self.assertEqual(data["email"], "common@email.com")
        self.assertIsNone(data["email_sent"])
        self.assertFalse(data["reference_submitted"])

    def test_get_reference_request_by_response_id(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_req2 = ReferenceRequest(
            1, "Mrs", "John", "Jones", "Manager", "john@email.com"
        )
        reference_request_repository.create(reference_req)
        reference_request_repository.create(reference_req2)
        response = self.app.get(
            "/api/v1/reference-request/list",
            data={"response_id": 1},
            headers=self.first_headers,
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_reference_request_detail_by_token_self_nomination(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        response = self.app.get(
            "/api/v1/reference-request/detail",
            data={"token": reference_req.token},
            headers=self.first_headers,
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["candidate"], "Mx First User")
        self.assertEqual(data["relation"], reference_req.relation)
        self.assertEqual(data["name"], self.test_event_data["name"])
        self.assertEqual(data["description"], self.test_event_data["description"])
        self.assertEqual(data["is_application_open"], True)
        self.assertEqual(data["email_from"], self.test_event_data["email_from"])
        self.assertIsNone(data["reference_submitted_timestamp"])
        self.assertIsNone(data["nominator"])

    def test_get_reference_request_detail_by_token_other_nomination(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            2, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        response = self.app.get(
            "/api/v1/reference-request/detail",
            data={"token": reference_req.token},
            headers=self.other_headers,
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["candidate"], "Mx Skittles Cat")
        self.assertEqual(data["nominator"], "Mrs User Lastname")
        self.assertEqual(data["relation"], reference_req.relation)
        self.assertEqual(data["name"], self.test_event_data["name"])
        self.assertEqual(data["description"], self.test_event_data["description"])
        self.assertEqual(data["is_application_open"], True)
        self.assertEqual(data["email_from"], self.test_event_data["email_from"])
        self.assertIsNone(data["reference_submitted_timestamp"])

    def test_reference_api(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            "token": reference_req.token,
            "uploaded_document": "DOCT-UPLOAD-78999",
        }
        response = self.app.post(
            "/api/v1/reference", data=REFERENCE_DETAIL, headers=self.first_headers
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.get(
            "/api/v1/reference", data={"response_id": 1}, headers=self.first_headers
        )
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        reference_request = reference_request_repository.get_by_id(1)
        self.assertEqual(reference_request.has_reference, True)

    def test_reference_api_update(self):
        self._seed_data()
        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            "token": reference_req.token,
            "uploaded_document": "DOCT-UPLOAD-78999",
        }
        REFERENCE_DETAIL_2 = {
            "token": reference_req.token,
            "uploaded_document": "DOCT-UPLOAD-79000",
        }
        response = self.app.post(
            "/api/v1/reference", data=REFERENCE_DETAIL, headers=self.first_headers
        )
        self.assertEqual(response.status_code, 201)

        response = self.app.put(
            "/api/v1/reference", data=REFERENCE_DETAIL_2, headers=self.first_headers
        )
        self.assertEqual(response.status_code, 200)

        response = self.app.get(
            "/api/v1/reference", data={"response_id": 1}, headers=self.first_headers
        )
        LOGGER.debug(response.data)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        reference_request = reference_request_repository.get_by_id(1)
        self.assertEqual(reference_request.has_reference, True)
        reference = reference_request_repository.get_reference_by_reference_request_id(
            reference_request.id
        )
        self.assertEqual(
            reference.uploaded_document, REFERENCE_DETAIL_2["uploaded_document"]
        )

    def test_reference_application_closed(self):

        self.add_organisation("Deep Learning Indaba", "blah.png", "blah_big.png")
        other_user_data = self.add_user("someuser@mail.com")

        test_event = self.add_event()
        test_event.add_event_role("admin", 1)
        test_event.set_application_close(datetime.now())

        self.add_to_db(test_event)
        self.test_form = self.create_application_form(test_event.id, True, False)
        self.add_to_db(self.test_form)

        self.test_response = self.add_response(self.test_form.id, other_user_data.id)
        self.headers = self.get_auth_header_for("someuser@mail.com")

        db.session.flush()

        reference_req = ReferenceRequest(
            1, "Mr", "John", "Snow", "Supervisor", "common@email.com"
        )
        reference_request_repository.create(reference_req)
        REFERENCE_DETAIL = {
            "token": reference_req.token,
            "uploaded_document": "DOCT-UPLOAD-78999",
        }
        response = self.app.post(
            "/api/v1/reference", data=REFERENCE_DETAIL, headers=self.headers
        )
        self.assertEqual(response.status_code, 403)

        response = self.app.put(
            "/api/v1/reference", data=REFERENCE_DETAIL, headers=self.headers
        )
        self.assertEqual(response.status_code, 403)
