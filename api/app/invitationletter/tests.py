from app.registration.models import RegistrationForm, RegistrationQuestion, RegistrationAnswer, RegistrationSection
import json
from datetime import datetime, timedelta
from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.registration.models import Offer
from app.registration.models import Registration
from app.invitationletter.models import InvitationLetterRequest
from app.invitationletter.models import InvitationTemplate
from app.utils.pdfconvertor import convert_to
from app.invitationletter.generator import generate
from nose.tools import nottest


INVITATION_LETTER = {
   'registration_id': 1,
   'event_id': 1,
   'work_address': "Somewhere over the rainbow",
   'addressed_to': "Sir",
   'residential_address': "Way up high",
   'passport_name': "Jane Do\u7231",
   'passport_no': "23456565",
   'passport_issued_by': "Neverland",
   'passport_expiry_date': datetime(1984, 12, 12).strftime('%Y-%m-%d'),
   'to_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
   'from_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
}


class InvitationLetterTests(ApiTestCase):

    def seed_static_data(self):
        organisation = Organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        db.session.add(organisation)
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

        test_user_2 = AppUser('somethingelse@email.com', 'Some', 'Thing', 'Mr', 1, 1,
                            'Female', 'University', 'Computer Science', 'None', 1,
                            datetime(1984, 12, 12),
                            'Zulu',
                            '123456')
        test_user_2.verified_email = True
        db.session.add(test_user_2)
        db.session.commit()


        event = Event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),
            key='REGINAL', 
            organisation_id=1, 
            email_from='abx@indaba.deeplearning',
            url='indaba.deeplearning'
        )
        db.session.add(event)
        db.session.commit()

        offer = Offer(
            user_id=test_user.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            accommodation_award=True,
            travel_award=True,
            accepted_accommodation_award=True,
            accepted_travel_award=True
        )
        db.session.add(offer)
        db.session.commit()


        offer_2 = Offer(
            user_id=test_user_2.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=True,
            accommodation_award=False,
            travel_award=False,
            accepted_accommodation_award=False,
            accepted_travel_award=False,
        )
        db.session.add(offer_2)
        db.session.commit()

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

        rq = RegistrationQuestion(
            section_id=section.id,
            registration_form_id=form.id,
            description="Will you be bringing a poster?",
            type="short-text",
            is_required=True,
            order=1,
            placeholder="the placeholder",
            headline="Will you be bringing a poster?",
            validation_regex="[]/",
            validation_text=" text"
        )
        db.session.add(rq)
        db.session.commit()


        registration = Registration(
            offer_id=offer.id,
            registration_form_id=form.id,
            confirmed=True)
        db.session.add(registration)
        db.session.commit()

        registration_2 = Registration(
            offer_id=offer_2.id,
            registration_form_id=form.id,
            confirmed=True)
        db.session.add(registration_2)
        db.session.commit()


        ra = RegistrationAnswer(
            registration_id=registration_2.id,
            registration_question_id=rq.id,
            value="yes"
        )
        db.session.add(ra)
        db.session.commit()

        template = InvitationTemplate(
            event_id=event.id,
            template_path="Indaba 2019  - Invitation Letter - General.docx",
            send_for_travel_award_only=False,
            send_for_accommodation_award_only=False,
            send_for_both_travel_accommodation=True)
        db.session.add(template)

        template_2 = InvitationTemplate(
            event_id=event.id,
            template_path="Indaba 2019 - Invitation Letter - Travel & Accomodation.docx",
            send_for_travel_award_only=False,
            send_for_accommodation_award_only=False,
            send_for_both_travel_accommodation=False)
        db.session.add(template_2)
        db.session.commit()

        self.headers = self.get_auth_header_for("something@email.com")
        self.headers_2 = self.get_auth_header_for("somethingelse@email.com")

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
    
    @nottest
    def test_create_create_invitation_letter(self):
        self.seed_static_data()
        response = self.app.post(
                '/api/v1/invitation-letter', data=INVITATION_LETTER, headers=self.headers)
        data = json.loads(response.data)
        LOGGER.debug("invitation letter: {}".format(data))

        letter = db.session.query(InvitationLetterRequest).filter(
            InvitationLetterRequest.id == data['invitation_letter_request_id']).first()

        assert response.status_code == 201
        assert data['invitation_letter_request_id'] == 1
        assert letter.event_id == 1
        assert letter.work_address == "Somewhere over the rainbow"
        assert letter.addressed_to == "Sir"
        assert letter.residential_address == "Way up high"
        assert letter.passport_name == "Jane Do\u7231"
        assert letter.passport_no == "23456565"
        assert letter.passport_issued_by == "Neverland"

    @nottest
    def test_create_create_invitation_letter_no_work(self):
        self.seed_static_data()
        INVITATION_LETTER['work_address'] = None
        response = self.app.post(
                '/api/v1/invitation-letter', data=INVITATION_LETTER, headers=self.headers)
        data = json.loads(response.data)
        print(data)
        LOGGER.debug("invitation letter: {}".format(data))

        letter = db.session.query(InvitationLetterRequest).filter(
            InvitationLetterRequest.id == data['invitation_letter_request_id']).first()

        assert response.status_code == 201
        assert data['invitation_letter_request_id'] == 1
        assert letter.event_id == 1
        assert letter.work_address == " "
        assert letter.addressed_to == "Sir"
        assert letter.residential_address == "Way up high"
        assert letter.passport_name == "Jane Do\u7231"
        assert letter.passport_no == "23456565"
        assert letter.passport_issued_by == "Neverland"

    
    def test_create_create_invitation_letter_correct_template(self):
        self.seed_static_data()
        INVITATION_LETTER_2 = {
            'registration_id': 2,
            'event_id': 1,
            'work_address': "Somewhere over the rainbow",
            'addressed_to': "Sir",
            'residential_address': "Way up high",
            'passport_name': "Jane Do\u7231",
            'passport_no': "23456565",
            'passport_issued_by': "Neverland",
            'passport_expiry_date': datetime(1984, 12, 12).strftime('%Y-%m-%d'),
            'to_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'from_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        response = self.app.post(
                '/api/v1/invitation-letter', data=INVITATION_LETTER_2, headers=self.headers_2)
        data = json.loads(response.data)
        print(data)
        LOGGER.debug("invitation letter: {}".format(data))

        letter = db.session.query(InvitationLetterRequest).filter(
            InvitationLetterRequest.id == data['invitation_letter_request_id']).first()

        assert response.status_code == 201
        assert data['invitation_letter_request_id'] == 1
        assert letter.event_id == 1
        assert letter.work_address == " "
        assert letter.addressed_to == "Sir"
        assert letter.residential_address == "Way up high"
        assert letter.passport_name == "Jane Do\u7231"
        assert letter.passport_no == "23456565"
        assert letter.passport_issued_by == "Neverland"



    @nottest
    def test_create_create_invitation_letter_correct_template(self):
        self.seed_static_data()
        INVITATION_LETTER_2 = {
            'registration_id': 2,
            'event_id': 1,
            'work_address': "Somewhere over the rainbow",
            'addressed_to': "Sir",
            'residential_address': "Way up high",
            'passport_name': "Jane Do\u7231",
            'passport_no': "23456565",
            'passport_issued_by': "Neverland",
            'passport_expiry_date': datetime(1984, 12, 12).strftime('%Y-%m-%d'),
            'to_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'from_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }
        response = self.app.post(
                '/api/v1/invitation-letter', data=INVITATION_LETTER_2, headers=self.headers_2)
        data = json.loads(response.data)
        print(data)
        LOGGER.debug("invitation letter: {}".format(data))

        letter = db.session.query(InvitationLetterRequest).filter(
            InvitationLetterRequest.id == data['invitation_letter_request_id']).first()

        assert response.status_code == 201
        assert data['invitation_letter_request_id'] == 1
        assert letter.event_id == 1
        assert letter.addressed_to == "Sir"
        assert letter.residential_address == "Way up high"
        assert letter.passport_name == "Jane Do\u7231"
        assert letter.passport_no == "23456565"
        assert letter.passport_issued_by == "Neverland"

    

class PDFConverterTest(ApiTestCase):

    def seed_static_data(self):
        organisation = Organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        db.session.add(organisation)
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

        event = Event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),
            key='REGINAL', 
            organisation_id=1, 
            email_from='abx@indaba.deeplearning',
            url='indaba.deeplearning'
        )
        db.session.add(event)
        db.session.commit()
        self.event = event

    @nottest
    def test_generator(self):
        self.seed_static_data()
        self.assertEqual(generate(template_path='Indaba 2019  - Invitation Letter - General.docx',
                                  event_id=self.event.id,
                                  work_address='19 Melle Steet\nRetro Rabbit\nSouth Africa\n1000',
                                  addressed_to='Man with the Visa Power',
                                  residential_address='123 Magic Street\nDance\nMore Dance\n1000',
                                  passport_name='Jeff Jeffdejeff',
                                  passport_no='09876512344',
                                  passport_issued_by='RSA',
                                  invitation_letter_sent_at=datetime(1984, 12, 12).strftime('%Y-%m-%d'),
                                  to_date=datetime(1984, 12, 12).strftime('%Y-%m-%d'),
                                  from_date=datetime(1984, 12, 12).strftime('%Y-%m-%d'),
                                  country_of_residence='South Africa',
                                  nationality='South African',
                                  date_of_birth=datetime(1984, 12, 12).strftime('%Y-%m-%d'),
                                  email='info@gmail.com',
                                  user_title='Mr',
                                  firstname='Jeff',
                                  lastname='Jeffdejeff',
                                  bringing_poster='',
                                  expiry_date=datetime(1984, 12, 12).strftime('%Y-%m-%d')), True)



       




