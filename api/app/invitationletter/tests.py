from app.registration.models import RegistrationForm
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


INVITATION_LETTER = {
   'registration_id': 1,
   'event_id': 1,
   'work_address': "Somewhere over the rainbow",
   'addressed_to': "Sir",
   'residential_address': "Way up high",
   'passport_name': "Jane Doe",
   'passport_no': "23456565",
   'passport_issued_by': "Neverland",
   'to_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
   'from_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
}


class InvitationLetterTests(ApiTestCase):

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

        event = Event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),

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

        form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(form)
        db.session.commit()

        registration = Registration(
            offer_id=event.id,
            registration_form_id=form.id,
            confirmed=True)
        db.session.add(registration)
        db.session.commit()

        template = InvitationTemplate(
            event_id=event.id,
            template_path="https://wwww.template.com/blah ",
            send_for_travel_award_only=False,
            send_for_accommodation_award_only=False,
            send_for_both_travel_accommodation=True)
        db.session.add(template)
        db.session.commit()

        self.headers = self.get_auth_header_for("something@email.com")

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
        assert letter.passport_name == "Jane Doe"
        assert letter.passport_no == "23456565"
        assert letter.passport_issued_by == "Neverland"
        assert letter.to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')\
            == datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert letter.from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')\
            == datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


class PDFConvetorTest(ApiTestCase):
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

        event = Event(
            name="Tech Talk",
            description="tech talking",
            start_date=datetime(2019, 12, 12, 10, 10, 10),
            end_date=datetime(2020, 12, 12, 10, 10, 10),

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

        form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(form)
        db.session.commit()

        registration = Registration(
            offer_id=event.id,
            registration_form_id=form.id,
            confirmed=True)
        db.session.add(registration)
        db.session.commit()

        template = InvitationTemplate(
            event_id=event.id,
            template_path="https://docs.google.com/document/d/1OA-ER_Oscb_P3YETj_rfpql6Txiqg1cYCa0QbB01ZX0/edit",
            send_for_travel_award_only=False,
            send_for_accommodation_award_only=False,
            send_for_both_travel_accommodation=True)
        db.session.add(template)
        db.session.commit()

        self.headers = self.get_auth_header_for("something@email.com")

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

    def test_generator(self):
        self.assertEqual(generate(template_path='app/invitationletter/letter/testsample.docx', event_id=1,
                                  work_address='my-work-address', addressed_to='Mr.', residential_address='PTA',
                                  passport_name='mypassport', passport_no='098765', passport_issued_by='RSA',
                                  invitation_letter_sent_at='', to_date=datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                  from_date=datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                  country_of_residence='South Africa', nationality='South African',
                                  date_of_birth=datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                                  email='info@gmail.com', firstname='Lindani', lastname='Mabaso'), True)

    def test_convert_to(self):
        self.assertEqual(convert_to(folder='app/invitationletter/letter',
                                    source='app/invitationletter/letter/testsample.docx'), True)

       




