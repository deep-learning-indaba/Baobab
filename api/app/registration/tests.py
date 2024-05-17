from app.registration.models import RegistrationForm
from app.registration.models import RegistrationQuestion
from app.registration.models import RegistrationSection
import json
from datetime import datetime, timedelta
from app import db
from app.utils.testing import ApiTestCase
from app.users.models import UserCategory, Country
from app.offer.models import OfferTag


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


class RegistrationTest(ApiTestCase):

    def _seed_static_data(self):
        test_user_no_tag = self.add_user('something@email.com', 'Some', 'Thing', 'Mr')
        test_user_tag = self.add_user('something2@email.com', 'Some', 'Thing', 'Ms')
        event_admin = self.add_user('event_admin@ea.com', 'event_admin', is_admin=True)
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png')
        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))
        db.session.commit()

        event = self.add_event(
            name={'en': "Tech Talk"},
            description={'en': "tech talking"},
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),
            key='SPEEDNET'
        )
        db.session.commit()

        tag = self.add_tag(event.id, 
                     tag_type='GRANT', 
                     names={'en': 'Grant Tag', 'fr': 'Grant Tag fr'}, 
                     descriptions={'en': 'Grant Tag description', 'fr': 'Grant Tag fr description'})

        self.event_id = event.id

        offer_no_tag = self.add_offer(
            user_id=test_user_no_tag.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True)

        self.offer_no_tag_id = offer_no_tag.id

        offer_with_tag = self.add_offer(
            user_id=test_user_tag.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True)
        offer_tag = self.tag_offer(offer_with_tag.id, tag.id)
        self.offer_tag_id = offer_tag.id
        self.offer_with_tag_id = offer_with_tag.id

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
            show_for_tag_id=None
        )
        db.session.add(section)
        db.session.commit()

        section2 = RegistrationSection(
            registration_form_id=form.id,
            name="Section 2",
            description="the section 2 description",
            order=2,
            show_for_tag_id=tag.id
        )
        db.session.add(section2)
        db.session.commit()

        section3 = RegistrationSection(
            registration_form_id=form.id,
            name="Section 3",
            description="the section 3 description",
            order=3,
            show_for_tag_id=None,
            show_for_invited_guest=True
        )
        db.session.add(section3)
        db.session.commit()

        section4 = RegistrationSection(
            registration_form_id=form.id,
            name="Section 4",
            description="the section 4 description",
            order=3,
            show_for_tag_id=tag.id,
            show_for_invited_guest=True
        )
        db.session.add(section4)
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

        self.headers_no_tag = self.get_auth_header_for("something@email.com")
        self.headers_with_tag = self.get_auth_header_for("something2@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        db.session.flush()

    def test_offer_no_tag(self):
        """Test that an offer without a tag sees the correct sections."""
        self._seed_static_data()

        params = {'offer_id': self.offer_no_tag_id, 'event_id': self.event_id}
        response = self.app.get("/api/v1/registration-form", headers=self.headers_no_tag, data=params)

        form = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(form['registration_sections']), 1)
        self.assertEqual(form['registration_sections'][0]['name'], 'Section 1')
        self.assertEqual(len(form['registration_sections'][0]['registration_questions']), 1)


    def test_offer_with_tag(self):
        """Test that an offer with a tag sees the correct sections."""
        self._seed_static_data()

        params = {'offer_id': self.offer_with_tag_id, 'event_id': self.event_id}
        response = self.app.get("/api/v1/registration-form", headers=self.headers_with_tag, data=params)

        form = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(form['registration_sections']), 2)
        self.assertEqual(form['registration_sections'][0]['name'], 'Section 1')
        self.assertEqual(len(form['registration_sections'][0]['registration_questions']), 1)
        self.assertEqual(form['registration_sections'][1]['name'], 'Section 2')

    def test_offer_with_tag_not_accepted(self):
        """Test that an offer with an unaccepted tag sees the correct sections."""
        self._seed_static_data()
        db.session.query(OfferTag).filter(OfferTag.id == self.offer_tag_id).update({'accepted': False})
        db.session.commit()
        
        params = {'offer_id': self.offer_with_tag_id, 'event_id': self.event_id}
        response = self.app.get("/api/v1/registration-form", headers=self.headers_with_tag, data=params)

        form = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(form['registration_sections']), 1)
        self.assertEqual(form['registration_sections'][0]['name'], 'Section 1')


class OfferListAPITest(ApiTestCase):
    
        def _seed_static_data(self):
            """Seed static data for the tests."""
            test_user1 = self.add_user('something@email.com', 'Some', 'Thing', 'Mr')
            test_user2 = self.add_user('something2@email.com', 'Some', 'Thing2', 'Ms')
            event_admin = self.add_user('event_admin@ea.com', 'event_admin', is_admin=True)

            event = self.add_event(
                name={'en': "Tech Talk"},
                description={'en': "tech talking"},
                start_date=datetime(2019, 12, 12, 10, 10, 10),
                end_date=datetime(2020, 12, 12, 10, 10, 10),
                key='SPEEDNET'
            )
            db.session.commit()

            self.event_id = event.id

            self.add_offer(
                user_id=test_user1.id,
                event_id=event.id,
                offer_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=False,
                candidate_response=True)
            
            self.add_offer(
                user_id=test_user2.id,
                event_id=event.id,
                offer_date=datetime.now() - timedelta(days=30),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=False,
                candidate_response=False)
            
            db.session.commit()
            self.headers = self.get_auth_header_for(event_admin.email)
            
        def test_offer_list(self):
            """Test that an offer list is returned."""
            self._seed_static_data()

            params = {'event_id': self.event_id}
            response = self.app.get("/api/v1/offerlist", headers=self.headers, data=params)

            offers = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(offers), 2)
            self.assertEqual(offers[0]['firstname'], 'Some')
            self.assertEqual(offers[0]['lastname'], 'Thing')
            self.assertTrue(offers[0]['candidate_response'])
            self.assertEqual(offers[1]['lastname'], 'Thing2')
            self.assertEqual(offers[1]['firstname'], 'Some')
            self.assertFalse(offers[1]['candidate_response'])
