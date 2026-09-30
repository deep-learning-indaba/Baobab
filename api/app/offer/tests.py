import json
from datetime import datetime, timedelta
from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.users.models import UserCategory, Country
from app.offer.models import Offer, OfferTag
from app.forms.models import Form, FormResponse
from app.offer.repository import OfferRepository as offer_repository
from app.outcome.repository import OutcomeRepository as outcome_repository
from app.outcome.models import Outcome, Status
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

        self.add_email_template('offer-nofee')
        self.add_email_template('offer-fee')
        self.add_email_template('offer-nofee-grants', template='These are your grants: {grants}')
        self.add_email_template('offer-fee-grants', template='These are your grants: {grants}')
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

        outcome = outcome_repository.get_latest_by_user_for_event(OFFER_DATA['user_id'], OFFER_DATA['event_id'])
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

    def test_create_offer_with_note_tags(self):
        self._seed_static_data(add_offer=False)

        tag1 = self.add_tag(event_id=self.event_id, names={'en': 'Note 1 en', 'fr': 'Note 1 fr'}, descriptions={'en': 'Note 1 en description', 'fr': 'Note 1 fr description'}, tag_type='OFFER_NOTE')
        tag2 = self.add_tag(event_id=self.event_id, tag_type='OFFER_NOTE')

        offer_data = OFFER_DATA.copy()
        offer_data['note_tags'] = [{'id': tag1.id}, {'id': tag2.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        offer = offer_repository.get_by_id(data['id'])
        self.assertEqual(len(offer.offer_tags), 2)

    def test_create_offer_with_grant_and_note_tags(self):
        self._seed_static_data(add_offer=False)

        grant_tag = self.add_tag(event_id=self.event_id, tag_type='GRANT')
        note_tag = self.add_tag(event_id=self.event_id, tag_type='OFFER_NOTE')

        offer_data = OFFER_DATA.copy()
        offer_data['grant_tags'] = [{'id': grant_tag.id}]
        offer_data['note_tags'] = [{'id': note_tag.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 201)
        offer = offer_repository.get_by_id(data['id'])
        self.assertEqual(len(offer.offer_tags), 2)

    def test_create_offer_with_non_offer_note_tags(self):
        self._seed_static_data(add_offer=False)

        tag1 = self.add_tag(event_id=self.event_id, tag_type='REGISTRATION')

        offer_data = OFFER_DATA.copy()
        offer_data['note_tags'] = [{'id': tag1.id}]

        response = self.app.post(
            '/api/v1/offer',
            data=json.dumps(offer_data),
            headers=self.adminHeaders,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

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

class OfferAdminApiTest(ApiTestCase):

    def setUp(self):
        super().setUp()
        self.admin = self.add_user('offer_admin@ea.com', 'event_admin', is_admin=True)
        self.admin_id = self.admin.id
        self.candidate_id = self.add_user('candidate@email.com').id
        self.other_candidate_id = self.add_user('other@email.com').id
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        db.session.add(UserCategory('Offer Category'))
        db.session.add(Country('Suid Afrika'))
        db.session.commit()

        event = self.add_event(key='SPEEDNET')
        self.event_id = event.id
        app_form = self.create_application_form()
        self.add_response(app_form.id, self.candidate_id, True, False)
        self.add_response(app_form.id, self.other_candidate_id, True, False)

        self.grant_tag_id = self.add_tag(event_id=self.event_id, tag_type='GRANT').id
        self.grant_tag2_id = self.add_tag(event_id=self.event_id, tag_type='GRANT').id
        self.note_tag_id = self.add_tag(event_id=self.event_id, tag_type='OFFER_NOTE').id
        self.response_tag_id = self.add_tag(event_id=self.event_id, tag_type='RESPONSE').id

        self.add_email_template('offer-reset', template='Reset until {expiry_date} {host}/{event_key}/offer {event_email_from}')
        self.headers = self.get_auth_header_for('offer_admin@ea.com')

    def get_auth_header_for(self, email):
        response = self.app.post('api/v1/authenticate', data={'email': email, 'password': 'abc'})
        return {'Authorization': json.loads(response.data)['token']}

    def _make_offer(self, **kwargs):
        offer = self.add_offer(self.candidate_id, event_id=self.event_id, **kwargs)
        return offer.id

    def _put(self, body):
        body = dict(body, event_id=self.event_id)
        return self.app.put('/api/v1/offerAdmin', data=json.dumps(body),
                            headers=self.headers, content_type='application/json')

    def _reset(self, body):
        body = dict(body, event_id=self.event_id)
        return self.app.post('/api/v1/offerReset', data=json.dumps(body),
                             headers=self.headers, content_type='application/json')

    def _tag_ids(self, offer_id):
        return {ot.tag_id for ot in offer_repository.get_by_id(offer_id).offer_tags}

    def test_edit_expiry_date_only_leaves_tags(self):
        offer_id = self._make_offer()
        db.session.add(OfferTag(offer_id, self.grant_tag_id))
        db.session.commit()

        response = self._put({'id': offer_id, 'expiry_date': '2031-05-04'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['expiry_date'], '2031-05-04')
        self.assertEqual(self._tag_ids(offer_id), {self.grant_tag_id})

    def test_edit_adds_and_removes_tags(self):
        offer_id = self._make_offer()
        db.session.add(OfferTag(offer_id, self.grant_tag_id))
        db.session.add(OfferTag(offer_id, self.note_tag_id))
        db.session.commit()

        response = self._put({
            'id': offer_id,
            'grant_tags': [{'id': self.grant_tag2_id}],
            'note_tags': []})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._tag_ids(offer_id), {self.grant_tag2_id})
        self.assertEqual([t['id'] for t in json.loads(response.data)['tags']], [self.grant_tag2_id])

    def test_edit_omitted_tag_type_is_untouched(self):
        offer_id = self._make_offer()
        db.session.add(OfferTag(offer_id, self.grant_tag_id))
        db.session.add(OfferTag(offer_id, self.note_tag_id))
        db.session.commit()

        response = self._put({'id': offer_id, 'grant_tags': []})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._tag_ids(offer_id), {self.note_tag_id})

    def test_edit_keeps_accepted_flag_of_retained_tags(self):
        offer_id = self._make_offer()
        db.session.add(OfferTag(offer_id, self.grant_tag_id, accepted=True))
        db.session.commit()

        self._put({'id': offer_id, 'grant_tags': [{'id': self.grant_tag_id}, {'id': self.grant_tag2_id}]})

        accepted = {ot.tag_id: ot.accepted for ot in offer_repository.get_by_id(offer_id).offer_tags}
        self.assertEqual(accepted, {self.grant_tag_id: True, self.grant_tag2_id: None})

    def test_edit_rejects_tag_of_wrong_type(self):
        offer_id = self._make_offer()

        response = self._put({'id': offer_id, 'grant_tags': [{'id': self.note_tag_id}]})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(self._tag_ids(offer_id), set())

    def test_edit_rejects_tag_from_another_event(self):
        offer_id = self._make_offer()
        other_event = self.add_event(key='OTHER')
        foreign_tag_id = self.add_tag(event_id=other_event.id, tag_type='GRANT').id

        response = self._put({'id': offer_id, 'grant_tags': [{'id': foreign_tag_id}]})

        self.assertEqual(response.status_code, 404)

    def test_edit_keeps_already_attached_inactive_tag(self):
        offer_id = self._make_offer()
        inactive_tag_id = self.add_tag(event_id=self.event_id, tag_type='GRANT', active=False).id
        db.session.add(OfferTag(offer_id, inactive_tag_id))
        db.session.commit()

        response = self._put({'id': offer_id, 'grant_tags': [{'id': self.grant_tag_id}]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._tag_ids(offer_id), {inactive_tag_id, self.grant_tag_id})

    def test_edit_offer_from_another_event_not_found(self):
        other_event = self.add_event(key='OTHER')
        offer_id = self.add_offer(self.candidate_id, event_id=other_event.id).id

        response = self._put({'id': offer_id, 'expiry_date': '2031-05-04'})

        self.assertEqual(response.status_code, 404)

    def test_reset_rejected_offer(self):
        offer_id = self._make_offer(candidate_response=False)
        offer = offer_repository.get_by_id(offer_id)
        offer.rejected_reason = 'Cannot travel'
        offer.responded_at = datetime.now()
        db.session.add(OfferTag(offer_id, self.grant_tag_id, accepted=False))
        db.session.commit()

        response = self._reset({'id': offer_id})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(data['candidate_response'])
        self.assertIsNone(data['rejected_reason'])
        self.assertIsNone(data['responded_at'])
        self.assertIsNone(data['tags'][0]['accepted'])

    def test_reset_sends_email_to_candidate(self):
        offer_id = self._make_offer(candidate_response=False)

        with mock.patch('app.utils.emailer.send_mail') as send_mail:
            response = self._reset({'id': offer_id})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['email_sent'])
        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.kwargs['recipient'], 'candidate@email.com')
        self.assertIn('/offer', send_mail.call_args.kwargs['body_text'])

    def test_reset_succeeds_when_email_fails(self):
        offer_id = self._make_offer(candidate_response=False)

        with mock.patch('app.utils.emailer.send_mail', side_effect=Exception('smtp down')):
            response = self._reset({'id': offer_id})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(json.loads(response.data)['email_sent'])
        self.assertIsNone(offer_repository.get_by_id(offer_id).candidate_response)

    def test_reset_with_new_expiry_date(self):
        offer_id = self._make_offer(candidate_response=False, expiry_date=datetime.now() - timedelta(days=3))

        response = self._reset({'id': offer_id, 'expiry_date': '2031-05-04'})
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['expiry_date'], '2031-05-04')
        self.assertFalse(data['is_expired'])

    def test_reset_expired_offer_requires_new_expiry_date(self):
        offer_id = self._make_offer(candidate_response=False, expiry_date=datetime.now() - timedelta(days=3))

        response = self._reset({'id': offer_id})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(offer_repository.get_by_id(offer_id).candidate_response is None)

    def test_reset_only_allowed_for_rejected_offers(self):
        pending_id = self._make_offer()
        accepted_id = self.add_offer(self.other_candidate_id, event_id=self.event_id, candidate_response=True).id

        self.assertEqual(self._reset({'id': pending_id}).status_code, 409)
        self.assertEqual(self._reset({'id': accepted_id}).status_code, 409)
        self.assertTrue(offer_repository.get_by_id(accepted_id).candidate_response)

    def test_reset_requires_event_admin(self):
        offer_id = self._make_offer(candidate_response=False)
        self.add_user('plain@email.com')
        headers = self.get_auth_header_for('plain@email.com')

        response = self.app.post('/api/v1/offerReset',
                                 data=json.dumps({'id': offer_id, 'event_id': self.event_id}),
                                 headers=headers, content_type='application/json')

        self.assertEqual(response.status_code, 403)

    def test_candidates_excludes_users_with_offers_and_rejected(self):
        self._make_offer()
        response = self.app.get(f'/api/v1/offerCandidates?event_id={self.event_id}', headers=self.headers)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([c['user_id'] for c in data['candidates']], [self.other_candidate_id])

        outcome_repository.add(Outcome(self.event_id, self.other_candidate_id, Status.REJECTED, self.admin_id))
        response = self.app.get(f'/api/v1/offerCandidates?event_id={self.event_id}', headers=self.headers)
        self.assertEqual(json.loads(response.data)['candidates'], [])

    def test_candidates_includes_event_fees(self):
        self.add_event_fee(self.event_id, self.admin_id, amount=150)

        response = self.app.get(f'/api/v1/offerCandidates?event_id={self.event_id}', headers=self.headers)
        fees = json.loads(response.data)['event_fees']

        self.assertEqual(len(fees), 1)
        self.assertEqual(fees[0]['amount'], 150)

    def _add_new_application_form(self, submitted_user_ids, withdrawn_user_ids=()):
        form = Form(self.event_id, self.admin_id)
        form.form_type = 'application'
        db.session.add(form)
        db.session.commit()
        for user_id in list(submitted_user_ids) + list(withdrawn_user_ids):
            response = FormResponse(form.id, user_id)
            response.is_submitted = True
            response.is_withdrawn = user_id in withdrawn_user_ids
            db.session.add(response)
        db.session.commit()

    def test_candidates_come_only_from_new_form_when_event_has_one(self):
        # The legacy responses for both candidates exist, but the new form is authoritative.
        self._add_new_application_form([self.other_candidate_id])

        response = self.app.get(f'/api/v1/offerCandidates?event_id={self.event_id}', headers=self.headers)

        self.assertEqual([c['user_id'] for c in json.loads(response.data)['candidates']],
                         [self.other_candidate_id])

    def test_candidates_from_new_form_exclude_withdrawn_and_users_with_offers(self):
        third_id = self.add_user('third@email.com').id
        self._add_new_application_form(
            [self.candidate_id, self.other_candidate_id], withdrawn_user_ids=[third_id])
        self._make_offer()

        response = self.app.get(f'/api/v1/offerCandidates?event_id={self.event_id}', headers=self.headers)

        self.assertEqual([c['user_id'] for c in json.loads(response.data)['candidates']],
                         [self.other_candidate_id])
