import json

from datetime import datetime, timedelta

from app import app, db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import AppUser, PasswordReset, UserCategory, Country, UserComment
from app.events.models import Event, EventRole
from app.applicationModel.models import ApplicationForm
from app.responses.models import Response
from app.organisation.models import Organisation


INVITED_GUEST = {
    'event_id': 1,
    'email': 'something@email.com',
    'role': 'jedi'
}

INVITED_GUEST_2 = {
    'event_id': 1,
    'email': 'something2@email.com',
    'role': 'jedi'
}

INVITED_GUEST_NEW_USER = {
    'event_id': 1,
    'email': 'new@email.com',
    'role': 'jedi'
}
USER_DATA = {
    'email': 'newsomething@email.com',
    'firstname': 'Some',
    'lastname': 'Thing',
    'user_title': 'Mr',
    'role': 'mentor',
    'event_id': 1,
    'policy_agreed': True
}


class InvitedGuestTest(ApiTestCase):

    def seed_static_data(self):
        test_user = self.add_user('something@email.com')
        test_user2 = self.add_user('something2@email.com')

        event_admin = self.add_user('event_admin@ea.com')
        db.session.commit()
        self.add_organisation('Deep Learning Indaba')
        self.add_organisation('Deep Learning IndabaX')
        db.session.commit()

        db.session.add(UserCategory('Postdoc'))
        db.session.add(Country('South Africa'))

        self.event1 = self.add_event({'en': 'Indaba'}, {'en': 'Indaba Event'}, datetime.now(), datetime.now(), 'LBFSOLVER')
        self.event2 = self.add_event({'en': 'IndabaX'}, {'en': 'IndabaX Sudan'}, datetime.now(), datetime.now(), 'NAGSOLVER', 2)
        db.session.commit()

        adminRole = EventRole('admin', event_admin.id, self.event1.id)
        db.session.add(adminRole)
        db.session.commit()

        self.event1_id = self.event1.id
        self.event2_id = self.event2.id
        self.headers = self.get_auth_header_for("something@email.com")
        self.adminHeaders = self.get_auth_header_for("event_admin@ea.com")

        db.session.flush()

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        print(data)
        header = {'Authorization': data['token']}
        return header

    def test_create_invitedGuest(self):
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST, headers=self.headers)
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data['invitedGuest_id'] == 1

    def test_create_invitedGuest_duplicate(self):
        self.seed_static_data()
        self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST, headers=self.headers)
        response = self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST, headers=self.headers)
        assert response.status_code == 409

    def test_create_invitedGuest_user_not_found(self):
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST_NEW_USER, headers=self.headers)
        assert response.status_code == 404

    def test_create_invitedGuest_create_user(self):
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/invitedGuest/create', data=USER_DATA, headers=self.headers)
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data['fullname'] == '{} {} {}'.format(USER_DATA["user_title"], USER_DATA["firstname"], USER_DATA["lastname"])

    def test_create_invitedGuest_list(self):
        self.seed_static_data()
        # Adding some invited guests
        event_id = 1
        self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST, headers=self.headers)
        response = self.app.post(
            '/api/v1/invitedGuest', data=INVITED_GUEST_2, headers=self.headers)
        response = self.app.get(
            '/api/v1/invitedGuestList?event_id='+str(event_id), headers=self.adminHeaders)
        data = json.loads(response.data)
        data = sorted(data, key=lambda k: k['invited_guest_id'])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['user']['email'],
                         INVITED_GUEST['email'])
        self.assertEqual(data[1]['user']['email'],
                         INVITED_GUEST_2['email'])
