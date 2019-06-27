from app.registration.models import RegistrationForm
import json
from datetime import datetime, timedelta
from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, UserCategory, Country
from app.events.models import Event
from app.registration.models import Offer
from app.registration.models import Registration
from app.invitationletter.models import InvitationTemplate

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
        LOGGER.debug(
            "invitation letter: {}".format(data))
        assert response.status_code == 201
        assert data['invitation_letter_request_id'] == 1
       




