import json

from datetime import datetime, timedelta

from app import app, db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country, UserComment
from app.events.models import Event, EventRole
from app.registration.models import Offer
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response
from app.utils.errors import FORBIDDEN


OFFER_DATA = {
    'id': '1',
    'user_id': '1',
    'event_id': '1',
    'offer_date': datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'expiry_date': datetime(2020, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'payment_required': False,
    'travel_award': False,
    'accomodation_award': 'accomodation award',
    'rejected': False,
    'rejected_reason': False,
    'updated_at': datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
}




AUTH_DATA = {
     'email': 'something1@email.com',
    'password': '123456'
}


class OfferApiTest(ApiTestCase):

    def seed_static_data(self):
        test_country = Country('Indaba Land')
        db.session.add(test_country)
        db.session.commit()

        test_category = UserCategory('Category1')
        db.session.add(test_category)
        db.session.commit()

        self.test_user = AppUser('something1@email.com', 'Some', 'Thing', 'Mr', 1, 1,
                                 'Male', 'University', 'Computer Science', 'None', 1,
                                 datetime(1984, 12, 12),
                                 'Zulu',
                                 '123456')
        self.test_user.verified_email = True
        db.session.add(self.test_user)
        db.session.commit()

        test_event = Event('Test Event', 'Event Description',
                           datetime.now() + timedelta(days=30), datetime.now() + timedelta(days=60))
        db.session.add(test_event)
        db.session.commit()

        self.test_form = ApplicationForm(
            test_event.id, True, datetime.now() + timedelta(days=60))
        db.session.add(self.test_form)
        db.session.commit()

        db.session.flush()

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def test_get_offer(self):
        self.seed_static_data()

        response = self.app.post('/api/v1/offerAPI', data=OFFER_DATA)
        data = json.loads(response.data)

        self.headers = self.get_auth_header_for('something1@email.com')

        response = self.app.get('/api/v1/offerAPI')
        data = json.loads(response.data)
        assert data['user_id'] == '1'
        assert data['event_id'] == '1'
        assert data['offer_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert data['expiry_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert data['payment_required'] == 'payment required'
        assert data['travel_award'] == 'Travel  award'
        assert data['accomodation_award'] == 'award_accom'
        assert data['accepted'] == True
        assert data['rejected'] == False
        assert data['rejected_reason'] == 'None'
        assert data['updated_at'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


    def test_update_offer(self):
        self.seed_static_data()

        response = self.app.post('/api/v1/offerAPI', data=OFFER_DATA)
        data = json.loads(response.data)
        LOGGER.debbug(" <<response.status>>  {}".format( response.status_code))
        assert response.status_code == 404

        self.headers = self.get_auth_header_for("something1@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        response = self.app.put('/api/v1/offerAPI', data={
            'user_id': '1',
            'event_id': '1',
            'offer_date': datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'expiry_date': datetime(2020, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'payment_required': False,
            'travel_award': False,
            'accomodation_award': 'accomodation award',
            'accepted': True,
            'rejected': False,
            'rejected_reason': False,
            'updated_at': datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        })
        assert response.status_code == 200

        response = self.app.get('/api/v1/offerAPI')
        data = json.loads(response.data)
        assert data['user_id'] == '1'
        assert data['accepted'] == True
        assert data['rejected'] == False
        assert data['rejected_reason'] == 'None'
