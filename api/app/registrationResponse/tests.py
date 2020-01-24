from app.registration.models import RegistrationForm, Registration
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

    def seed_static_data(self, create_registration=False):
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.commit()

        test_user = AppUser('something@email.com', 'Some', 'Thing', 'Mr', 
                            '123456')
        test_user.verified_email = True
        db.session.add(test_user)
        db.session.commit()

        test_user2 = AppUser('something2@email.com', 'Something2', 'Thing2', 'Mrs', 
                            '123456')
        test_user2.verified_email = True
        db.session.add(test_user2)
        db.session.commit()

        event_admin = AppUser('event_admin@ea.com', 'event_admin', '1', 'Ms', '123456', True)
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
            accommodation_award=False,
            responded_at=datetime.now())
        self.offer.candidate_response = True
        self.offer.accepted_travel_award = True
        db.session.add(self.offer)
        db.session.commit()

        self.offer2 = Offer(
            user_id=test_user2.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=True,
            travel_award=True,
            accommodation_award=False,
            responded_at=datetime.now())
        db.session.add(self.offer2)
        db.session.commit()

        self.offer3 = Offer(
            user_id=event_admin.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=True,
            travel_award=False,
            accommodation_award=True,
            responded_at=datetime.now())
        db.session.add(self.offer3)
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
        self.headers2 = self.get_auth_header_for("something2@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        if create_registration:
            self.registration1 = Registration(self.offer.id, self.form.id, confirmed=False)
            db.session.add(self.registration1)
            db.session.commit()
            self.registration2 = Registration(self.offer2.id, self.form.id, confirmed=True)
            db.session.add(self.registration2)
            db.session.commit()
            self.registration3 = Registration(self.offer3.id, self.form.id, confirmed=False)
            db.session.add(self.registration3)
            db.session.commit()

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
            self.seed_static_data(create_registration=False)
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


    def test_get_unconfirmed_not_event_admin(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/registration/unconfirmed?event_id=1',
                    headers=self.headers)
            self.assertEqual(response.status_code, 403)

    def test_get_unconfirmed(self):
        with app.app_context():
            self.seed_static_data(create_registration=True)
            response = self.app.get('/api/v1/registration/unconfirmed?event_id=1',
                    headers=self.adminHeaders)
            responses = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(responses), 2)

            self.assertEqual(responses[0]['registration_id'], self.registration1.id)
            self.assertEqual(responses[0]['user_id'], self.offer.user_id)
            self.assertEqual(responses[0]['firstname'], 'Some')
            self.assertEqual(responses[0]['lastname'], 'Thing')
            self.assertEqual(responses[0]['email'], 'something@email.com')
            # TODO re-add once we get these fields outside of AppUser
            # self.assertEqual(responses[0]['user_category'], 'Postdoc')
            # self.assertEqual(responses[0]['affiliation'], 'University')
            self.assertEqual(responses[0]['created_at'][:9], datetime.today().isoformat()[:9])

            self.assertEqual(responses[1]['registration_id'], self.registration3.id)
            self.assertEqual(responses[1]['user_id'], self.offer3.user_id)
            self.assertEqual(responses[1]['firstname'], 'event_admin')
            self.assertEqual(responses[1]['lastname'], '1')
            self.assertEqual(responses[1]['email'], 'event_admin@ea.com')
            # TODO re-add once we get these fields outside of AppUser
            # self.assertEqual(responses[1]['user_category'], 'Postdoc')
            # self.assertEqual(responses[1]['affiliation'], 'NWU')
            self.assertEqual(responses[1]['created_at'][:9], datetime.today().isoformat()[:9])

    def test_get_confirmed_not_event_admin(self):
        with app.app_context():
            self.seed_static_data()
            response = self.app.get('/api/v1/registration/confirmed?event_id=1',
                    headers=self.headers)
            self.assertEqual(response.status_code, 403)


    
    def test_get_confirmed(self):
        with app.app_context():
            self.seed_static_data(create_registration=True)
            response = self.app.get('/api/v1/registration/confirmed?event_id=1',
                    headers=self.adminHeaders)
            responses = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(responses), 3)

    def test_confirm_admin(self):
        with app.app_context():
            self.seed_static_data(create_registration=True)
            response = self.app.post('/api/v1/registration/confirm',
                    data={'registration_id': self.registration1.id},
                    headers=self.headers)
            self.assertEqual(response.status_code, 403)

    def test_confirm(self):
        with app.app_context():
            self.seed_static_data(create_registration=True)
            response = self.app.post('/api/v1/registration/confirm',
                    data={'registration_id': self.registration1.id},
                    headers=self.adminHeaders)
            self.assertEqual(response.status_code, 200)

            updated_registration = db.session.query(Registration).filter(Registration.id == self.registration1.id).one()
            self.assertTrue(updated_registration.confirmed)
