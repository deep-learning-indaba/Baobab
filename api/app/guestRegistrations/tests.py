from app.registration.models import RegistrationForm
from app.registration.models import RegistrationSection
import json
from datetime import datetime, timedelta
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.registration.models import RegistrationQuestion
from app import app, db

from app import db, LOGGER
from app.organisation.models import Organisation


class GuestRegistrationApiTest(ApiTestCase):

    def seed_static_data(self):
        test_user = self.add_user('something@email.com')
        event_admin = self.add_user('event_admin@ea.com')
        
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.commit()

        event = self.add_event(
            name={'en': "Tech Talk"},
            description={'en': "tech talking"},
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),
            key='REGINAL'
        )

        db.session.commit()

        self.form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(self.form)
        db.session.commit()
        self.form_id = self.form.id

        self.event_id = event.id

        section = RegistrationSection(
            registration_form_id=self.form.id,
            name="Section 1",
            description="the section description",
            order=1,
            show_for_travel_award=None,
            show_for_accommodation_award=None,
            show_for_payment_required=None,
        )
        db.session.add(section)
        db.session.commit()

        section2 = RegistrationSection(
            registration_form_id=self.form.id,
            name="Section 2",
            description="the section 2 description",
            order=1,
            show_for_travel_award=None,
            show_for_accommodation_award=None,
            show_for_payment_required=None,
        )
        db.session.add(section2)
        db.session.commit()

        self.question = RegistrationQuestion(
            section_id=section.id,
            registration_form_id=self.form.id,
            description="Question 1",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="the headline",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(self.question)
        db.session.commit()
        self.question_id = self.question.id

        self.question2 = RegistrationQuestion(
            section_id=section2.id,
            registration_form_id=self.form.id,
            description="Question 2",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="the headline",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(self.question2)
        db.session.commit()
        self.question2_id = self.question2.id

        self.question3 = RegistrationQuestion(
            section_id=section2.id,
            registration_form_id=self.form.id,
            description="Question 3",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="the headline",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(self.question3)
        db.session.commit()
        self.question3_id = self.question3.id

        db.session.flush()

        self.headers = self.get_auth_header_for("something@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)

        header = {'Authorization': data['token']}
        return header

    def test_create_registration(self):
        self.seed_static_data()
        registration_data = {
            'registration_form_id': self.form_id,
            'answers': [
                {
                    'registration_question_id': self.question_id,
                    'value': 'Answer 1'
                },
                {
                    'registration_question_id': self.question2_id,
                    'value': 'Hello world, this is the 2nd answer.'
                },
                {
                    'registration_question_id': self.question3_id,
                    'value': 'Hello world, this is the 3rd answer.'
                }
            ]
        }
        response = self.app.post(
            '/api/v1/guest-registration',
            data=json.dumps(registration_data),
            content_type='application/json',
            headers=self.headers)
        self.assertEqual(response.status_code, 201)

    def test_get_registration(self):
        self.seed_static_data()

        registration_data = {
            'registration_form_id': self.form_id,
            'answers': [
                {
                    'registration_question_id': self.question_id,
                    'value': 'Answer 1'
                },
                {
                    'registration_question_id': self.question2_id,
                    'value': 'Hello world, this is the 2nd answer.'
                },
                {
                    'registration_question_id': self.question3_id,
                    'value': 'Hello world, this is the 3rd answer.'
                }
            ]
        }
        response = self.app.post(
            '/api/v1/guest-registration',
            data=json.dumps(registration_data),
            content_type='application/json',
            headers=self.headers
        )
        LOGGER.debug("hi: {}".format(response.data))
        response = self.app.get(
            '/api/v1/guest-registration',
            content_type='application/json',
            headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_update_200(self):
        """Test if update work"""
        self.seed_static_data()
        registration_data = {
            'registration_form_id': self.form_id,
            'answers': [
                {
                    'registration_question_id': self.question_id,
                    'value': 'Answer 1'
                },
                {
                    'registration_question_id': self.question2_id,
                    'value': 'Hello world, this is the 2nd answer.'
                },
                {
                    'registration_question_id': self.question3_id,
                    'value': 'Hello world, this is the 3rd answer.'
                }
            ]
        }

        response = self.app.post(
            '/api/v1/guest-registration',
            data=json.dumps(registration_data),
            content_type='application/json',
            headers=self.headers
        )
        data = json.loads(response.data)
        LOGGER.debug(
            "Reg-form: {}".format(data))
        put_registration_data = {
            'guest_registration_id': data['id'],
            'registration_form_id': self.form_id,
            'answers': [
                {
                    'registration_question_id': self.question_id,
                    'value': 'Answer Other'
                },
                {
                    'registration_question_id': self.question2_id,
                    'value': 'Hello world, this is the 2nd answer.'
                },
                {
                    'registration_question_id': self.question3_id,
                    'value': 'Hello world, this is the 3rd answer.'
                }
            ]
        }
        post_response = self.app.put(
            '/api/v1/guest-registration',
            data=json.dumps(put_registration_data),
            content_type='application/json',
            headers=self.headers)

        LOGGER.debug(
            "put response: {}".format(post_response))
        self.assertEqual(post_response.status_code, 200)

        response = self.app.get(
            '/api/v1/guest-registration',
            content_type='application/json',
            headers=self.headers)
        updated_data = json.loads(response.data)
        self.assertEqual(updated_data['answers'][0]['value'], "Answer Other")

    def test_get_form(self):
        self.seed_static_data()
        url = "/api/v1/guest-registration-form?event_id=%d" % self.event_id
        LOGGER.debug(url)
        response = self.app.get(url, headers=self.headers)

        if response.status_code == 403:
            return

        LOGGER.debug(
            "form: {}".format(json.loads(response.data)))

        form = json.loads(response.data)
        self.assertEqual(form['registration_sections'][0]['registration_questions'][0]['type'], 'short-text')
        self.assertEqual(form['registration_sections'][0]['name'], 'Section 1')

    def test_if_user_is_guest(self):
        self.seed_static_data()
        USER_DATA = {
            'email': 'something@email.com',
            'role': 'mentor',
            'event_id': 1
        }
        response = self.app.post(
            '/api/v1/invitedGuest', data=USER_DATA, headers=self.headers)
        response_guest = self.app.get(
            '/api/v1/checkIfInvitedGuest?event_id=%d' % self.event_id, headers=self.headers)
        LOGGER.debug(
            "guest response: {}".format(response_guest))
        self.assertEqual(response_guest.status_code, 200)

    def test_if_user_is_not_guest(self):
        self.seed_static_data()
        USER_DATA = {
            'email': 'some@email.com',
            'role': 'mentor',
            'event_id': 1
        }
        response = self.app.post(
            '/api/v1/invitedGuest', data=USER_DATA, headers=self.headers)
        response_guest = self.app.get(
            '/api/v1/checkIfInvitedGuest?event_id=%d' % self.event_id, headers=self.headers)
        LOGGER.debug(
            "guest response: {}".format(response_guest))
        self.assertEqual(response_guest.status_code, 404)
