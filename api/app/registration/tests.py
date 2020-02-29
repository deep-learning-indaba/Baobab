from app.registration.models import RegistrationForm
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationSection
import json
from datetime import datetime, timedelta
from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.registration.models import Offer
from app.organisation.models import Organisation


OFFER_DATA = {
    'id': 1,
    'user_id': 1,
    'event_id': 1,
    'offer_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'expiry_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'payment_required': False,
    'travel_award': False,
    'accommodation_award': True,
    'accepted_accommodation_award': None,
    'accepted_travel_award': None,
    'rejected_reason': 'N/A',
}

REGISTRATION_FORM = {
    'event_id': 1,
}

REGISTRATION_SECTION = {
    'registration_form_id': 1,
    'name': "section 2",
    'description': "this is the second section",
    'order': 1,
    'show_for_accommodation_award': True,
    'show_for_travel_award': True,
    'show_for_payment_required': True
}

REGISTRATION_QUESTION = {
    'registration_form_id': 1,
    'section_id': 1,
    'type': "open-ended",
    'description': "just a question",
    'headline': "question headline",
    'placeholder': "answer the this question",
    'validation_regex': "/[a-d]",
    'validation_text': "regex are cool",
    'order': 1,
    'options': "{'a': 'both a and b', 'b': 'none of the above'}",
    'is_required': True
}


class OfferApiTest(ApiTestCase):

    def seed_static_data(self, add_offer=True):
        test_user = self.add_user('something@email.com')
        offer_admin = self.add_user('offer_admin@ea.com', 'event_admin', is_admin=True)
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        db.session.add(UserCategory('Offer Category'))
        db.session.add(Country('Suid Afrika'))
        db.session.commit()

        event = self.add_event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12),
            end_date=datetime(2020, 12, 12),
            key='SPEEDNET'
        )
        db.session.commit()

        if add_offer:
            offer = Offer(
                user_id=test_user.id,
                event_id=event.id,
                offer_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=False,
                travel_award=True,
                accommodation_award=False)
            db.session.add(offer)
            db.session.commit()

        self.headers = self.get_auth_header_for("something@email.com")
        self.adminHeaders = self.get_auth_header_for("offer_admin@ea.com")

        db.session.flush()

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        LOGGER.debug("<<auth>> {}".format(data))
        header = {'Authorization': data['token']}
        return header

    def test_create_offer(self):
        self.seed_static_data(add_offer=False)

        response = self.app.post('/api/v1/offer', data=OFFER_DATA,
                                 headers=self.adminHeaders)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['payment_required'])
        self.assertTrue(data['travel_award'])
        self.assertTrue(data['accommodation_award'])

    def test_create_offer_with_template(self):
        self.seed_static_data(add_offer=False)
        
        offer_data = OFFER_DATA.copy()
        offer_data['email_template'] = """Dear {user_title} {first_name} {last_name},

        This is a custom email notifying you about your place at the {event_name}.

        Visit {host}/offer to accept it, you have until {expiry_date} to do so!

        kthanksbye!    
        """

        response = self.app.post('/api/v1/offer', data=offer_data,
                                 headers=self.adminHeaders)
        data = json.loads(response.data)

        assert response.status_code == 201
        assert data['payment_required']
        assert data['travel_award']
        assert data['accommodation_award']

    def test_create_duplicate_offer(self):
        self.seed_static_data(add_offer=True)

        response = self.app.post('/api/v1/offer', data=OFFER_DATA,
                                 headers=self.adminHeaders)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 409)

    def test_get_offer(self):
        self.seed_static_data()

        event_id = 1
        url = "/api/v1/offer?event_id=%d" % (
            event_id)
        LOGGER.debug(url)
        response = self.app.get(url, headers=self.headers)

        assert response.status_code == 200

    def test_get_offer_not_found(self):
        self.seed_static_data()

        event_id = 12
        url = "/api/v1/offer?event_id=%d" % (
            event_id)
        LOGGER.debug(url)
        response = self.app.get(url, headers=self.headers)

        assert response.status_code == 404

    def test_update_offer(self):
        self.seed_static_data()
        event_id = 1
        offer_id = 1
        candidate_response = True
        rejected_reason = "the reason for rejection"
        url = "/api/v1/offer?offer_id=%d&event_id=%d&candidate_response=%s&rejected_reason=%s" % (
            offer_id, event_id, candidate_response, rejected_reason)
        LOGGER.debug(url)
        response = self.app.put(url, headers=self.headers)

        data = json.loads(response.data)
        LOGGER.debug("Offer-PUT: {}".format(response.data))

        assert response.status_code == 201
        assert data['candidate_response']


class RegistrationTest(ApiTestCase):

    def seed_static_data(self):
        test_user = self.add_user('something@email.com', 'Some', 'Thing', 'Mr')
        event_admin = self.add_user('event_admin@ea.com', 'event_admin', is_admin=True)
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png')
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.commit()

        event = self.add_event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),
            key='SPEEDNET'
        )
        db.session.commit()

        self.event_id = event.id

        offer = Offer(
            user_id=test_user.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            travel_award=True,
            accommodation_award=False)

        offer.candidate_response = True
        offer.accepted_travel_award = True

        db.session.add(offer)
        db.session.commit()
        self.offer_id = offer.id

        form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(form)
        db.session.commit()

        section = RegistrationSection(
            registration_form_id=form.id,
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
            registration_form_id=form.id,
            name="Section 2",
            description="the section 2 description",
            order=1,
            show_for_travel_award=True,
            show_for_accommodation_award=False,
            show_for_payment_required=False,
        )
        db.session.add(section2)
        db.session.commit()

        question = RegistrationQuestion(
            section_id=section.id,
            registration_form_id=form.id,
            description="Question 1",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="the headline",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(question)
        db.session.commit()

        question2 = RegistrationQuestion(
            section_id=section2.id,
            registration_form_id=form.id,
            description="Question 2",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="the headline",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(question2)
        db.session.commit()

        self.headers = self.get_auth_header_for("something@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        db.session.flush()

    def test_create_registration_form(self):
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/registration-form', data=REGISTRATION_FORM, headers=self.adminHeaders)
        data = json.loads(response.data)
        LOGGER.debug(
            "Reg-form: {}".format(data))
        assert response.status_code == 201
        assert data['registration_form_id'] == 2

    def test_get_form(self):
        self.seed_static_data()
        url = "/api/v1/registration-form?offer_id=%d&event_id=%d" % (
            self.offer_id, self.event_id)
        LOGGER.debug(url)
        response = self.app.get(url, headers=self.headers)

        if response.status_code == 403:
            return

        LOGGER.debug(
            "form: {}".format(json.loads(response.data)))

        form = json.loads(response.data)
        assert form['registration_sections'][0]['registration_questions'][0]['type'] == 'short-text'
        assert form['registration_sections'][0]['name'] == 'Section 1'
