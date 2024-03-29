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
    'policy_agreed': True,
    'language': 'en'
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

        self.add_email_template('guest-invitation-with-registration')
        self.add_email_template('guest-invitation')
        self.add_email_template('new-guest-registration')
        self.add_email_template('new-guest-no-registration')

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
            f'/api/v1/invitedGuestList?event_id={event_id}&language=en', headers=self.adminHeaders)

        data = json.loads(response.data)
        data = sorted(data, key=lambda k: k['invited_guest_id'])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['user']['email'],
                         INVITED_GUEST['email'])
        self.assertEqual(data[1]['user']['email'],
                         INVITED_GUEST_2['email'])

class InvitedGuestTagAPITest(ApiTestCase):
    def _seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        db.session.commit()

        self.event1admin = self.add_user('event1admin@mail.com')
        self.user1 = self.add_user('user1@mail.com')
        self.user2 = self.add_user('user2@mail.com')
        db.session.commit()

        self.invited_guest1 = self.add_invited_guest(user_id=self.user1.id, event_id=self.event1.id, role="Guest")
        self.invited_guest2 = self.add_invited_guest(user_id=self.user2.id, event_id=self.event1.id, role="Mentor")
        db.session.commit()

        self.event1.add_event_role('admin', self.event1admin.id)
        db.session.commit()

        self.tag1 = self.add_tag(tag_type='REGISTRATION')
        self.tag2 = self.add_tag(names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'}, descriptions={'en': 'Tag 2 en description', 'fr': 'Tag 2 fr description'}, tag_type='REGISTRATION')
        self.tag_invited_guest(self.invited_guest1.id, self.tag1.id)
        self.tag_invited_guest(self.invited_guest2.id, self.tag2.id)
        db.session.commit()
        db.session.flush()

    def test_tag_admin(self):
        """Test that an event admin can add a tag to an invited guest."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag2.id,
            'invited_guest_id': self.invited_guest1.id,
            'language': 'en',
        }

        response = self.app.post(
            '/api/v1/invitedguesttag',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 201)

        params = {
            'event_id': self.event1.id,
            'invited_guest_id' : self.invited_guest1.id,
            'language': 'en',
        }
        response = self.app.get(
            '/api/v1/invitedGuest?',
            json=params,
            headers=self.get_auth_header_for('event1admin@mail.com')
            )
        data = json.loads(response.data)

        self.assertEqual(len(data['tags']), 2)
        self.assertEqual(data['tags'][0]['id'], 1)
        self.assertEqual(data['tags'][1]['id'], 2)

    def test_remove_tag_admin(self):
        """Test that an event admin can remove a tag from an invited guest."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag2.id,
            'invited_guest_id': self.invited_guest2.id,
            'language': 'en'
        }

        response = self.app.delete(
            '/api/v1/invitedguesttag',
            headers=self.get_auth_header_for('event1admin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 200)

        params = {
            'event_id': self.event1.id,
            'invited_guest_id' : self.invited_guest2.id,
            'language': 'en',
        }
        response = self.app.get(
            '/api/v1/invitedGuest?',
            json=params,
            headers=self.get_auth_header_for('event1admin@mail.com')
            )
        data = json.loads(response.data)
        
        self.assertEqual(len(data['tags']), 0)

    def test_tag_non_admin(self):
        """Test that a non admin can't add a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'invited_guest_id': self.invited_guest1.id,
            'language': 'en'
        }

        response = self.app.post(
            '/api/v1/invitedguesttag',
            headers=self.get_auth_header_for('user2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

    def test_remove_tag_non_admin(self):
        """Test that a non admin can't remove a tag."""
        self._seed_static_data()

        params = {
            'event_id': self.event1.id,
            'tag_id': self.tag1.id,
            'invited_guest_id': self.invited_guest1.id,
            'language': 'en'
        }

        response = self.app.delete(
            '/api/v1/invitedguesttag',
            headers=self.get_auth_header_for('user2@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)