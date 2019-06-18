from app.registration.models import RegistrationForm
from app.registration.models import RegistrationSection
import json
from datetime import datetime, timedelta
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.registration.models import Offer
from app.registration.models import RegistrationQuestion
from app import app, db


class RegistrationApiTest(ApiTestCase):

    def seed_static_data(self):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.commit()

        test_user = AppUser('something@email.com', 'Some', 'Thing', 'Mr', 1, 1,
                            'Male', 'University', 'Computer Science', 'None', 1,
                            datetime(1984, 12, 12),
                            'Zulu',
                            '123456')
        test_user.verified_email = True
        db.session.add(test_user)
        db.session.commit()

        event_admin = AppUser('event_admin@ea.com', 'event_admin', '1', 'Ms', 1,
                              1, 'F', 'NWU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', '123456', True)
        event_admin.verified_email = True
        db.session.add(event_admin)

        db.session.commit()

        event = Event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),

        )
        db.session.add(event)
        db.session.commit()

        self.offer = Offer(
            user_id=test_user.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            travel_award=True,
            responded_at=datetime.now())
        db.session.add(self.offer)
        db.session.commit()

        self.form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(self.form)
        db.session.commit()

        section = RegistrationSection(
            registration_form_id=self.form.id,
            name="Section 1",
            description="the section description",
            order=1,
            show_for_travel_award=True,
            show_for_accommodation_award=False,
            show_for_payment_required=False,
        )
        db.session.add(section)
        db.session.commit()

        section2 = RegistrationSection(
            registration_form_id=self.form.id,
            name="Section 2",
            description="the section 2 description",
            order=1,
            show_for_travel_award=True,
            show_for_accommodation_award=False,
            show_for_payment_required=False,
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

        self.headers = self.get_auth_header_for("something@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        db.session.flush()

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': '123456'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)

        header = {'Authorization': data['token']}
        return header

    def test_create_registration(self):
        with app.app_context():
            self.seed_static_data()
            registration_data = {
                'offer_id': self.offer.id,
                'registration_form_id': self.form.id,
                'answers': [
                    {
                        'registration_question_id': self.question.id,
                        'value': 'Answer 1'
                    },
                    {
                        'registration_question_id': self.question2.id,
                        'value': 'Hello world, this is the 2nd answer.'
                    },
                    {
                        'registration_question_id': self.question3.id,
                        'value': 'Hello world, this is the 3rd answer.'
                    }
                ]
            }
            response = self.app.post(
                '/api/v1/registration-response',
                data=json.dumps(registration_data),
                content_type='application/json',
                headers=self.headers)
            self.assertEqual(response.status_code, 201)

    def test_get_registration(self):
        with app.app_context():
            self.seed_static_data()

            registration_data = {
                'offer_id': self.offer.id,
                'registration_form_id': self.form.id,
                'answers': [
                    {
                        'registration_question_id': self.question.id,
                        'value': 'Answer 1'
                    },
                    {
                        'registration_question_id': self.question2.id,
                        'value': 'Hello world, this is the 2nd answer.'
                    },
                    {
                        'registration_question_id': self.question3.id,
                        'value': 'Hello world, this is the 3rd answer.'
                    }
                ]
            }
            response = self.app.post(
                '/api/v1/registration-response',
                data=json.dumps(registration_data),
                content_type='application/json',
                headers=self.headers
            )
            response = self.app.get(
                '/api/v1/registration-response',
                content_type='application/json',
                headers=self.headers)
            self.assertEqual(response.status_code, 200)

    def test_update_200(self):
        """Test if update work"""
        with app.app_context():
            self.seed_static_data()
            registration_data = {
                'offer_id': self.offer.id,
                'registration_form_id': self.form.id,
                'answers': [
                    {
                        'registration_question_id': self.question.id,
                        'value': 'Answer 1'
                    },
                    {
                        'registration_question_id': self.question2.id,
                        'value': 'Hello world, this is the 2nd answer.'
                    },
                    {
                        'registration_question_id': self.question3.id,
                        'value': 'Hello world, this is the 3rd answer.'
                    }
                ]
            }

            response = self.app.post(
                '/api/v1/registration-response',
                data=json.dumps(registration_data),
                content_type='application/json',
                headers=self.headers
            )
            data = json.loads(response.data)
            put_registration_data = {
                'registration_id': data['id'],
                'offer_id': self.offer.id,
                'registration_form_id': self.form.id,
                'answers': [
                    {
                        'registration_question_id': self.question.id,
                        'value': 'Answer 1'
                    },
                    {
                        'registration_question_id': self.question2.id,
                        'value': 'Hello world, this is the 2nd answer.'
                    },
                    {
                        'registration_question_id': self.question3.id,
                        'value': 'Hello world, this is the 3rd answer.'
                    }
                ]
            }
            post_response = self.app.put(
                '/api/v1/registration-response',
                data=json.dumps(put_registration_data),
                content_type='application/json',
                headers=self.headers)
            self.assertEqual(post_response.status_code, 200)

    def test_update_missing(self):
        """Test that 404 is returned if we try to update a registration for a user that doesnt exist"""
        with app.app_context():
            self.seed_static_data()
            registration_data = {
                'registration_id': 50,
                'offer_id': self.offer.id,
                'registration_form_id': self.form.id,
                'answers': [
                    {
                        'registration_question_id': self.question.id,
                        'value': 'Answer 1'
                    },
                    {
                        'registration_question_id': self.question2.id,
                        'value': 'Hello world, this is the 2nd answer.'
                    },
                    {
                        'registration_question_id': self.question3.id,
                        'value': 'Hello world, this is the 3rd answer.'
                    }
                ]
            }

            response = self.app.put(
                '/api/v1/registration-response',
                data=json.dumps(registration_data),
                content_type='application/json',
                headers=self.headers)
            self.assertEqual(response.status_code, 404)
