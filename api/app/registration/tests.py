import json

from datetime import datetime, timedelta

from app import app, db
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country, UserComment
from app.events.models import Event, EventRole
from app.registration.models import Offer
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response

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
     'email': 'something@email.com',
    'password': '123456'
}


class OfferApiTest(ApiTestCase):

    def seed_static_data(self):

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

        headers = {'Authorization': data['token']}

        response = self.app.get('/api/v1/offerAPI', headers=headers)
        data = json.loads(response.data)
        assert data['id'] == '1'
        assert data['user_id'] == '1'
        assert data['event_id'] == '1'
        assert data['offer_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert data['expiry_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')'
        assert data['payment_required'] == 'payment required'
        assert data['travel_award'] == 'Travel  award'
        assert data['accomodation_award'] == 'award_accom'
        assert data['rejected'] == False
        assert data['rejected_reason'] == 'None'
        assert data['updated_at'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


    def test_update_offer(self):
        self.seed_static_data()
        response = self.app.post('/api/v1/offerAPI', data=USER_DATA)
        data = json.loads(response.data)
        assert response.status_code == 201

        headers = {'Authorization': data['token']}

        response = self.app.put('/api/v1/offerAPI', headers=headers, data={
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
        })
        assert response.status_code == 200

        response = self.app.get('/api/v1/offerAPI', headers=headers)
        data = json.loads(response.data)
        assert data['id'] == '1'
        assert data['user_id'] == '1'
        assert data['event_id'] == '1'
        assert data['offer_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert data['expiry_date'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        assert data['payment_required'] == 'payment required'
        assert data['travel_award'] == 'Travel  award'
        assert data['accomodation_award'] == 'award_accom'
        assert data['rejected'] == False
        assert data['rejected_reason'] == 'None'
        assert data['updated_at'] == datetime(2019, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ')



