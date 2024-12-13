import json
from datetime import datetime, timedelta
from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import UserCategory, Country
from app.offer.models import Offer
from app.offer.repository import OfferRepository as offer_repository
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.outcome.models import Status
import mock

OFFER_DATA = {
    'id': 1,
    'user_id': 1,
    'event_id': 1,
    'offer_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'expiry_date': datetime(1984, 12, 12).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    'payment_required': False,
    'rejected_reason': 'N/A',
}


class OfferApiTest(ApiTestCase):

    def _seed_static_data(self, add_offer=True):
        test_user = self.add_user('something@email.com')
        test_user2 = self.add_user('something2@email.com')
        offer_admin = self.add_user('offer_admin@ea.com', 'event_admin', is_admin=True)
        self.offer_admin_id = offer_admin.id
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')

        db.session.add(UserCategory('Offer Category'))
        db.session.add(Country('Suid Afrika'))
        db.session.commit()

        event = self.add_event(
            name={'en': "Tech Talk"},
            description={'en': "tech talking"},
            start_date=datetime(2019, 12, 12),
            end_date=datetime(2020, 12, 12),
            key='SPEEDNET'
        )
        db.session.commit()
        self.event_id = event.id

        app_form = self.create_application_form()
        self.add_response(app_form.id, test_user.id, True, False)
        self.add_response(app_form.id, test_user2.id, True, False)

        self.add_event_fee(self.event_id, self.offer_admin_id, amount=1000)

        if add_offer:
            offer_without_payment = Offer(
                user_id=test_user.id,
                event_id=event.id,
                offer_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=False)
            offer_with_payment = Offer(
                user_id=test_user2.id,
                event_id=event.id,
                offer_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=True,
                event_fee_id=1)
            db.session.add(offer_without_payment)
            db.session.add(offer_with_payment)
            db.session.commit()

            self.offer_without_payment_id = offer_without_payment.id
            self.offer_with_payment_id = offer_with_payment.id

        self.headers = self.get_auth_header_for("something@email.com")
        self.headers2 = self.get_auth_header_for("something2@email.com")
        self.adminHeaders = self.get_auth_header_for("offer_admin@ea.com")

        self.add_email_template('offer')
        self.add_email_template('offer-grants', template='These are your grants: {grants}')
        self.add_email_template('offer-paid')
        self.add_email_template('invoice')

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

    def test_create_offer(self):
        self._seed_static_data(add_offer=False)

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(OFFER_DATA),
            headers=self.adminHeaders,
            content_type='application/json'
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertFalse(data['payment_required'])

        outcome = outcome_repository.get_latest_by_user_for_event_response(OFFER_DATA['user_id'],None, OFFER_DATA['event_id'])
        self.assertEqual(outcome.status, Status.ACCEPTED)

    def test_create_offer_with_template(self):
        self._seed_static_data(add_offer=False)
        
        offer_data = OFFER_DATA.copy()
        offer_data['email_template'] = """Dear {user_title} {first_name} {last_name},

        This is a custom email notifying you about your place at the {event_name}.

        Visit {host}/offer to accept it, you have until {expiry_date} to do so!

        kthanksbye!    
        """

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertFalse(data['payment_required'])

    def test_create_offer_with_grant_tags(self):
        self._seed_static_data(add_offer=False)

        tag1 = self.add_tag(event_id=self.event_id, names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'}, descriptions={'en': 'Tag 2 en description', 'fr': 'Tag 2 fr description'}, tag_type='GRANT')
        tag2 = self.add_tag(event_id=self.event_id, tag_type='GRANT')

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': tag1.id}, {'id': tag2.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        self.assertFalse(data['payment_required'])

        offer = offer_repository.get_by_id(data['id'])
        self.assertEqual(len(offer.offer_tags), 2)

    def test_create_offer_with_non_grant_tags(self):
        self._seed_static_data(add_offer=False)

        tag1 = self.add_tag(event_id=self.event_id, tag_type='REGISTRATION')

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': tag1.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

    def test_create_offer_with_non_existent_tags(self):
        self._seed_static_data(add_offer=False)

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': 9999}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_create_offer_with_inactive_tags(self):
        self._seed_static_data(add_offer=False)

        tag1 = self.add_tag(event_id=self.event_id, tag_type='GRANT', active=False)

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': tag1.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

    def test_create_offer_with_tags_from_another_event(self):
        self._seed_static_data(add_offer=False)

        event2 = self.add_event(name={'en': 'Event 2'})

        tag = self.add_tag(event_id=event2.id, tag_type='GRANT')

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': tag.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_create_duplicate_offer(self):
        self._seed_static_data(add_offer=True)

        response = self.app.post('/api/v1/offer', data=OFFER_DATA,
                                 headers=self.adminHeaders)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 409)

    def test_get_offer(self):
        self._seed_static_data(add_offer=True)

        event_id = 1
        url = "/api/v1/offer?event_id=%d" % (
            event_id)

        response = self.app.get(url, headers=self.headers)

        self.assertEqual(response.status_code, 200)

    def test_get_offer_not_found(self):
        self._seed_static_data()

        event_id = 12
        url = "/api/v1/offer?event_id=%d" % (
            event_id)

        response = self.app.get(url, headers=self.headers)

        self.assertEqual(response.status_code, 404)

    def test_update_offer(self):
        self._seed_static_data()
        event_id = 1
        offer_id = 1
        candidate_response = True
        rejected_reason = "the reason for rejection"
        url = "/api/v1/offer?offer_id=%d&event_id=%d&candidate_response=%s&rejected_reason=%s" % (
            offer_id, event_id, candidate_response, rejected_reason)

        response = self.app.put(url, headers=self.headers)

        data = json.loads(response.data)
        LOGGER.debug("Offer-PUT: {}".format(response.data))

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data['candidate_response'])

    def test_offer_invoice(self):
        """Test that an invoice is issued when offer with payment required is accepted."""
        self._seed_static_data()
        event_id = 1
        offer_id = self.offer_with_payment_id
        candidate_response = True
        url = "/api/v1/offer?offer_id=%d&event_id=%d&candidate_response=%s" % (
            offer_id, event_id, candidate_response)

        # Mock storage
        with mock.patch('app.utils.storage.get_storage_bucket'):
            response = self.app.put(url, headers=self.headers2)
        
        self.assertEqual(response.status_code, 201)
        response = self.app.get(f'/api/v1/offer?event_id={event_id}', headers=self.headers2)
        data = json.loads(response.data)

        print(data)

        self.assertFalse(data['is_paid'])
        self.assertTrue(data['payment_required'])
        self.assertEqual(data['payment_amount'], 1000)
        self.assertEqual(data['payment_currency'], 'usd')
        self.assertEqual(data['invoice_id'], 1)
        

class OfferTagAPITest(ApiTestCase):

    def _seed_static_data(self):

        self.event = self.add_event(key='event1')
        db.session.commit()

        test_user = self.add_user('test_user@mail.com')
        offer_admin = self.add_user('offeradmin@mail.com')
        db.session.commit()
        self.test_user_id = test_user.id

        self.event.add_event_role('admin', offer_admin.id)
        db.session.commit()

        app_form = self.create_application_form()
        self.add_response(app_form.id, self.test_user_id, True, False)

        self.offer = self.add_offer(self.test_user_id, self.event.id)

        self.tag1 = self.add_tag(tag_type='REGISTRATION')
        self.tag2 = self.add_tag(names={'en': 'Tag 2 en', 'fr': 'Tag 2 fr'}, descriptions={'en': 'Tag 2 en description', 'fr': 'Tag 2 fr description'}, tag_type='REGISTRATION')
        self.tag_offer(self.offer.id, self.tag1.id)

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

    def test_tag_admin(self):
        """Test that an event admin can add a tag to an offer."""
        self._seed_static_data()

        params = {
            'event_id': self.event.id,
            'tag_id': self.tag2.id,
            'offer_id': self.offer.id
        }

        response = self.app.post(
            '/api/v1/offertag',
            headers=self.get_auth_header_for('offeradmin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 201)

        params = {
            'event_id': self.event.id,
            'user_id' : self.test_user_id,
            'language': 'en',
        }

        response = self.app.get(
            '/api/v1/offer',
            headers=self.get_auth_header_for('test_user@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data['tags']), 2)
        self.assertEqual(data['tags'][0]['id'], 1)

    def test_remove_tag_admin(self):
        """Test that an event admin can remove a tag from an offer."""
        self._seed_static_data()

        params = {
            'event_id': self.event.id,
            'tag_id': self.tag1.id,
            'offer_id': self.offer.id
        }

        response = self.app.delete(
            '/api/v1/offertag',
            headers=self.get_auth_header_for('offeradmin@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 200)

        params = {
            'event_id': self.event.id,
            'user_id' : self.test_user_id,
            'language': 'en',
        }

        response = self.app.get(
            '/api/v1/offer',
            headers=self.get_auth_header_for('test_user@mail.com'),
            json=params)

        data = json.loads(response.data)

        self.assertEqual(len(data['tags']), 0)

    def test_tag_non_admin(self):
        """Test that a non admin can't add a tag to an offer."""
        self._seed_static_data()

        params = {
            'event_id': self.event.id,
            'tag_id': self.tag1.id,
            'offer_id': self.offer.id
        }

        response = self.app.post(
            '/api/v1/offertag',
            headers=self.get_auth_header_for('test_user@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)

    def test_remove_tag_non_admin(self):
        """Test that a non admin can't remove a tag from an offer."""
        self._seed_static_data()

        params = {
            'event_id': self.event.id,
            'tag_id': self.tag1.id,
            'offer_id': self.offer.id
        }

        response = self.app.delete(
            '/api/v1/offertag',
            headers=self.get_auth_header_for('test_user@mail.com'),
            json=params)

        self.assertEqual(response.status_code, 403)