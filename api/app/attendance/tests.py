from datetime import datetime
import json

from app import db
from app.attendance.models import Attendance, EventQRToken, Checkin, EventIndemnity
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.attendance.repository import QRTokenRepository as qr_token_repository
from app.attendance.repository import CheckinRepository as checkin_repository
from app.events.models import EventRole
from app.users.models import Country, UserCategory
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, FORBIDDEN
from app.utils.testing import ApiTestCase
from app.tags.models import Tag, TagTranslation
from app.offer.models import Offer, OfferTag
from app.registration.models import RegistrationQuestion, RegistrationQuestionTag
from app.registration.models import RegistrationForm
from app.registration.models import Registration
from app.registration.models import RegistrationSection
from app.registration.models import RegistrationAnswer
from app.invitedGuest.models import InvitedGuest
from datetime import datetime, timedelta
from app import LOGGER
import json
import unittest


class AttendanceApiTest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        user_category = UserCategory('PhD')
        db.session.add(user_category)
        db.session.commit()

        country = Country('South Africa')
        db.session.add(country)

        self.attendee = self.add_user(email='attendee@mail.com')

        registration_admin = self.add_user('ra@ra.com')

        event = self.add_event({'en': 'indaba 2019'}, {'en': 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya '}, datetime(2019, 8, 25), datetime(2019, 8, 31),'JOLLOF')
        self.event = event
        db.session.add(self.event)

        event_role = EventRole('registration-admin', 2, 1)
        db.session.add(event_role)
        db.session.commit()
        offer = Offer(
            user_id=self.attendee.id,
            event_id=event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False
        )
        db.session.add_all([offer])
        
        self.tags = [
            Tag(self.event.id, "RESPONSE"),
            Tag(self.event.id, "QUESTION")
            ]
        db.session.add_all(self.tags)
        db.session.commit()

        tag_translations = [
            TagTranslation(self.tags[0].id, 'en', 'Offer Tag', 'Offer Tag Description'),
            TagTranslation(self.tags[1].id, 'en', 'Registration Question Tag', 'Registration Question Tag Description')
        ]
        db.session.add_all(tag_translations)
        db.session.commit()

        offer_tag = OfferTag(offer.id, self.tags[0].id)
        db.session.add(offer_tag)
        db.session.commit()

        form = RegistrationForm(
            event_id=event.id
        )
        db.session.add(form)
        db.session.commit()
        self.form = form
        section = RegistrationSection(
            registration_form_id=form.id,
            name="Section 1",
            description="the section description",
            order=1
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

        self.rq_tag = RegistrationQuestionTag(rq.id, self.tags[1].id)
        db.session.add(self.rq_tag)
        db.session.commit()

        registration = Registration(
            offer_id=offer.id,
            registration_form_id=form.id,
            confirmed=True)

        db.session.add_all([registration])
        db.session.commit()
        ra = RegistrationAnswer(
            registration_id=registration.id,
            registration_question_id=rq.id,
            value="yes"
        )
        db.session.add_all([ra])
        db.session.commit()

        self.add_email_template('attendance-confirmation')

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def test_non_admin_cannot_get_post_delete(self):
        self.seed_static_data()
        header = self.get_auth_header_for('attendee@mail.com')
        params = {'user_id': 2, 'event_id': 1, 'indemnity_signed': True}

        response_get = self.app.get(
            '/api/v1/attendance', headers=header, data=params)
        response_post = self.app.post(
            '/api/v1/attendance', headers=header, data=params)
        response_delete = self.app.delete(
            '/api/v1/attendance', headers=header, data=params)

        self.assertEqual(response_get.status_code, FORBIDDEN[1])
        self.assertEqual(response_post.status_code, FORBIDDEN[1])
        self.assertEqual(response_delete.status_code, FORBIDDEN[1])

    def setup_get_attendance(self):
        attendance = Attendance(1, 1, 2)
        attendance_repository.add(attendance)
        attendance_repository.save()

    def test_get_attendance(self):
        self.seed_static_data()
        self.setup_get_attendance()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.get('/api/v1/attendance',
                                headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['event_id'], 1)
        self.assertEqual(len(data['registration_metadata']), 1)
        self.assertEqual(data['registration_metadata'][0]['name'], "Registration Question Tag")
        self.assertEqual(len(data['offer_metadata']), 1)
        self.assertEqual(data['offer_metadata'][0]['name'], "Offer Tag")

    # Normal Attendance
    @unittest.skip("Deprecated API")
    def test_get_attendance_list(self):
        self.seed_static_data()

        attendee2 = self.add_user('attendee2@mail.com')
        db.session.commit()

        offer2 = Offer(
            user_id=attendee2.id,
            event_id=self.event.id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False
        )
        db.session.add(offer2)
        db.session.commit()

        registration2 = Registration(
            offer_id=offer2.id,
            registration_form_id=self.form.id,
            confirmed=False)
        db.session.add(registration2)
        db.session.commit()

        header = self.get_auth_header_for('ra@ra.com')

        user_id = 1
        params = {'event_id': 1}
        result = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data = json.loads(result.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['user_id'], user_id)

        params = {'user_id': user_id, 'event_id': 1}
        self.app.post('/api/v1/attendance',
                      headers=header, data=params)

        # Exclude signed in
        params = { 'event_id': 1,
                  'exclude_already_signed_in': True}
        result2 = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data2 = json.loads(result2.data)
        self.assertEqual(len(data2), 1)

        # Include signed in - possible to undo
        params = {'exclude_already_signed_in': 'false','event_id': 1}
        LOGGER.debug(params)
        result2 = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data2 = json.loads(result2.data)
        self.assertEqual(len(data2), 2)

    # Invited Guests attendance
    @unittest.skip("Deprecated API")
    def test_get_attendance_list_2(self):
        self.seed_static_data()
        mrObama = self.add_user('obama@mail.com', 'Barack', 'Obama', 'Mr')
        db.session.add(mrObama)
        db.session.commit()
        invited_guest_id = mrObama.id
        role = "EveryRole"
        mrObamaInvitedGuest = InvitedGuest(event_id=1, user_id=invited_guest_id, role=role)
        db.session.add(mrObamaInvitedGuest)
        db.session.commit()
        header = self.get_auth_header_for('ra@ra.com')

        # Invited Guests always get returned
        params = { 'event_id': 1}
        result = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data = json.loads(result.data)
        self.assertGreaterEqual(len(data),1)
        is_invited_guest_returned = False
        for attendee in data:
            if(attendee['user_id'] == invited_guest_id):
                is_invited_guest_returned = True
        self.assertTrue(is_invited_guest_returned)

        # Confirm Attendance of Invited Guest
        params = {'user_id': invited_guest_id, 'event_id': 1}
        attendance_response = self.app.get('/api/v1/attendance',
                      headers=header, data=params)
      
        response = json.loads(attendance_response.data)
        self.assertEqual(response['is_invitedguest'],True)
        self.assertEqual(response['invitedguest_role'],role)

        attendance_response = self.app.post('/api/v1/attendance',
                      headers=header, data=params)

        # No Invited Guest since he/she has already been signed in.
        params = { 'event_id': 1,
                  'exclude_already_signed_in': True}
        result2 = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data2 = json.loads(result2.data)
        is_invited_guest_returned = False
        for attendee in data2:
            if(attendee['user_id'] == invited_guest_id):
                is_invited_guest_returned = True
        
        self.assertFalse(is_invited_guest_returned)

   # No duplicate attendances
    def test_get_attendance_list_3(self):
        self.seed_static_data()
        # Add attendee as Invited Guest as well
        invited_guest_id = self.attendee.id
        dupl_attendee = InvitedGuest(event_id=1, user_id=invited_guest_id, role='EveryRole')
        db.session.add(dupl_attendee)
        db.session.commit()

        header = self.get_auth_header_for('ra@ra.com')
        params = { 'event_id': 1}
        result = self.app.get(
            '/api/v1/registration/confirmed', headers=header, data=params)
        data = json.loads(result.data)
        occurences_in_attendance_list = [att for att in data if att['user_id'] == invited_guest_id]
        num_occurences_in_attendance_list = len(occurences_in_attendance_list)
        self.assertEqual(num_occurences_in_attendance_list,1)


    def test_cannot_register_attendance_twice(self):
        self.seed_static_data()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.post('/api/v1/attendance',
                                 headers=header, data=params)
        response = self.app.post('/api/v1/attendance',
                                 headers=header, data=params)

        self.assertEqual(response.status_code, ATTENDANCE_ALREADY_CONFIRMED[1])

    def test_manual_confirm_creates_checkin_record(self):
        # The manual/no-ticket confirm path (used from the Event Attendance
        # page) must write a Checkin row too, not just mark Attendance
        # confirmed, so "already checked in" detection and the guest list's
        # Checked In status agree with what the QR scan path produces.
        self.seed_static_data()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1, 'indemnity_signed': True}

        response = self.app.post('/api/v1/attendance', headers=header, data=params)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(checkin_repository.is_checked_in(1, 1))
        self.assertIn(1, checkin_repository.checked_in_user_ids(1))

    def setup_delete_attendance(self):
        attendance = Attendance(1, 1, 2)
        attendance.confirm()
        attendance_repository.add(attendance)
        attendance_repository.save()

    def test_delete_attendance(self):
        self.seed_static_data()
        self.setup_delete_attendance()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.delete(
            '/api/v1/attendance', headers=header, data=params)

        attendance = attendance_repository.get(1, 1)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(attendance)
        self.assertFalse(attendance.confirmed)

    def test_delete_attendance_preserves_badge_and_indemnity(self):
        # Undo is meant to reverse a check-in, not erase the physical facts
        # that a badge was already printed and a form already signed.
        self.seed_static_data()
        attendance = Attendance(1, 1, 2)
        attendance.confirm()
        attendance.sign_indemnity()
        attendance.mark_badge_exported()
        attendance_repository.add(attendance)
        attendance_repository.save()

        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}
        response = self.app.delete(
            '/api/v1/attendance', headers=header, data=params)

        attendance = attendance_repository.get(1, 1)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(attendance.confirmed)
        self.assertTrue(attendance.indemnity_signed)
        self.assertTrue(attendance.badge_exported)


class IndemnitySigningTest(AttendanceApiTest):

    def seed_static_data(self):
        super(IndemnitySigningTest, self).seed_static_data()
        # The base fixture leaves the offer unanswered; these flows all gate on
        # the user being a confirmed guest.
        offer = db.session.query(Offer).filter_by(event_id=1, user_id=1).first()
        offer.candidate_response = True
        db.session.add(EventIndemnity(
            event_id=1, indemnity_form='I, {attendee_name}, agree.'))
        self.add_email_template('indemnity-signed')
        db.session.commit()

    def _attendance_rows(self, event_id, user_id):
        return (db.session.query(Attendance)
                .filter_by(event_id=event_id, user_id=user_id)
                .all())

    def test_signing_indemnity_after_badge_export_updates_same_row(self):
        # Badge export creates an attendance row to hold badge_exported. Signing
        # the indemnity afterwards must land on that row, or check-in reads one
        # row for the badge and another for the signature.
        self.seed_static_data()
        attendance_repository.mark_exported(1, [1], 2)

        header = self.get_auth_header_for('attendee@mail.com')
        response = self.app.post(
            '/api/v1/indemnity', headers=header, data={'event_id': 1})

        self.assertEqual(response.status_code, 201)
        rows = self._attendance_rows(1, 1)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].indemnity_signed)
        self.assertTrue(rows[0].badge_exported)

    def test_badge_export_after_signing_indemnity_updates_same_row(self):
        self.seed_static_data()
        header = self.get_auth_header_for('attendee@mail.com')
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})

        attendance_repository.mark_exported(1, [1], 2)

        rows = self._attendance_rows(1, 1)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].indemnity_signed)
        self.assertTrue(rows[0].badge_exported)

    def test_signing_indemnity_twice_does_not_duplicate(self):
        self.seed_static_data()
        header = self.get_auth_header_for('attendee@mail.com')
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})

        self.assertEqual(len(self._attendance_rows(1, 1)), 1)

    def test_checkin_after_badge_export_keeps_badge_exported(self):
        # The confusing signal at check-in: the console reports badge_exported
        # off the attendance row the check-in touches.
        self.seed_static_data()
        attendance_repository.mark_exported(1, [1], 2)

        header = self.get_auth_header_for('attendee@mail.com')
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})

        volunteer_header = self.get_auth_header_for('ra@ra.com')
        response = self.app.post(
            '/api/v1/checkin', headers=volunteer_header,
            data={'event_id': 1, 'user_id': 1})

        self.assertEqual(response.status_code, 201)
        self.assertTrue(json.loads(response.data)['badge_exported'])
        self.assertEqual(len(self._attendance_rows(1, 1)), 1)

    def test_indemnity_date_reflects_signature_not_badge_export(self):
        # `timestamp` is shown to the attendee as the date they signed, so
        # reusing a row created earlier by badge export must restamp it.
        self.seed_static_data()
        attendance_repository.mark_exported(1, [1], 2)
        export_time = attendance_repository.get(1, 1).timestamp

        header = self.get_auth_header_for('attendee@mail.com')
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})

        self.assertGreaterEqual(
            attendance_repository.get(1, 1).timestamp, export_time)

    def test_indemnity_get_reports_signed_for_badge_exported_attendee(self):
        self.seed_static_data()
        attendance_repository.mark_exported(1, [1], 2)

        header = self.get_auth_header_for('attendee@mail.com')
        self.app.post('/api/v1/indemnity', headers=header, data={'event_id': 1})
        response = self.app.get(
            '/api/v1/indemnity', headers=header, query_string={'event_id': 1})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['signed'])


class MyTicketAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.guest = self.add_user('guest@test.com')
        self.non_guest = self.add_user('nongGuest@test.com')
        self.guest_fullname = self.guest.full_name
        self.event = self.add_event(
            {'en': 'Ticket Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'TICKEV'
        )
        self.event_id = self.event.id
        self.guest_id = self.guest.id
        self.non_guest_id = self.non_guest.id
        offer = Offer(
            user_id=self.guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer)
        db.session.commit()

    def test_my_ticket_returns_qr_for_confirmed_guest(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('qr_url', data)
        self.assertEqual(data['fullname'], self.guest_fullname)
        self.assertEqual(data['role'], 'General Attendee')
        self.assertFalse(data['checked_in'])
        self.assertFalse(data['has_indemnity_form'])
        self.assertFalse(data['indemnity_signed'])

    def test_my_ticket_has_indemnity_form_true_when_form_exists(self):
        self.seed_static_data()
        indemnity = EventIndemnity(event_id=self.event_id, indemnity_form='Please agree to this.')
        db.session.add(indemnity)
        db.session.commit()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['has_indemnity_form'])
        self.assertFalse(data['indemnity_signed'])

    def test_my_ticket_returns_not_a_guest_for_non_guest(self):
        self.seed_static_data()
        header = self.get_auth_header_for('nongGuest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 403)

    def test_my_ticket_returns_invited_guest_role(self):
        self.seed_static_data()
        ig = InvitedGuest(event_id=self.event_id, user_id=self.non_guest_id, role='Speaker')
        db.session.add(ig)
        db.session.commit()
        header = self.get_auth_header_for('nongGuest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['role'], 'Speaker')

    def test_my_ticket_shows_checked_in_after_checkin(self):
        self.seed_static_data()
        token = qr_token_repository.get_or_create(self.event_id, self.guest_id)
        checkin_repository.create(self.event_id, self.guest_id, None, 'self', None)
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['checked_in'])


class CheckinAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.guest = self.add_user('guest@test.com')
        self.volunteer = self.add_user('volunteer@test.com')
        self.non_guest = self.add_user('nongGuest@test.com')
        self.guest_fullname = self.guest.full_name
        self.guest_id = self.guest.id
        self.non_guest_id = self.non_guest.id
        self.event = self.add_event(
            {'en': 'Checkin Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'CHKEV'
        )
        self.event_id = self.event.id
        self.add_event_role('registration-volunteer', self.volunteer.id, self.event_id)
        offer = Offer(
            user_id=self.guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer)
        db.session.commit()
        self.token = qr_token_repository.get_or_create(self.event_id, self.guest_id)
        self.token_str = self.token.token
        self.add_email_template('attendance-confirmation')

    def test_volunteer_can_checkin_guest_by_token(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['checked_in'])
        self.assertEqual(data['fullname'], self.guest_fullname)

    def test_checkin_is_idempotent_per_event(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['already_checked_in'])

    def test_non_volunteer_cannot_checkin_with_token(self):
        self.seed_static_data()
        header = self.get_auth_header_for('nongGuest@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_token_returns_invalid_qr(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': 'notarealtoken'}
        )
        self.assertEqual(response.status_code, 400)

    def test_non_guest_token_returns_not_on_guest_list(self):
        self.seed_static_data()
        non_guest_token_obj = qr_token_repository.get_or_create(self.event_id, self.non_guest_id)
        non_guest_token_str = non_guest_token_obj.token
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': non_guest_token_str}
        )
        self.assertEqual(response.status_code, 403)

    def test_resolve_returns_preview_for_volunteer(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['fullname'], self.guest_fullname)
        self.assertFalse(data['already_checked_in'])
        self.assertFalse(data['has_indemnity_form'])

    def test_resolve_has_indemnity_form_true_when_form_exists(self):
        self.seed_static_data()
        indemnity = EventIndemnity(event_id=self.event_id, indemnity_form='Please sign this.')
        db.session.add(indemnity)
        db.session.commit()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['has_indemnity_form'])
        self.assertFalse(data['indemnity_signed'])

    def test_resolve_forbidden_for_non_volunteer(self):
        self.seed_static_data()
        header = self.get_auth_header_for('nongGuest@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 403)

    def test_resolve_invalid_token_returns_invalid_qr(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': 'badtoken'}
        )
        self.assertEqual(response.status_code, 400)

    def test_resolve_reports_badge_not_exported_by_default(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['badge_exported'])

    def test_resolve_reports_badge_exported_after_mark(self):
        self.seed_static_data()
        attendance_repository.mark_exported(self.event_id, [self.guest_id], self.volunteer.id)
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['badge_exported'])

    def test_resolve_tags_empty_when_no_checkin_tags(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['tags'], [])

    def test_resolve_includes_checkin_tags(self):
        self.seed_static_data()
        tag = Tag(self.event_id, "CHECKIN")
        db.session.add(tag)
        db.session.commit()
        db.session.add(TagTranslation(tag.id, 'en', 'Yellow T-shirt'))
        db.session.commit()
        offer = attendance_repository.get_offer(self.event_id, self.guest_id)
        db.session.add(OfferTag(offer.id, tag.id))
        db.session.commit()

        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/resolve', headers=header,
            query_string={'event_id': self.event_id, 't': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['tags'], ['Yellow T-shirt'])

    def test_checkin_response_includes_checkin_tags(self):
        self.seed_static_data()
        tag = Tag(self.event_id, "CHECKIN")
        db.session.add(tag)
        db.session.commit()
        db.session.add(TagTranslation(tag.id, 'en', 'Yellow T-shirt'))
        db.session.commit()
        offer = attendance_repository.get_offer(self.event_id, self.guest_id)
        db.session.add(OfferTag(offer.id, tag.id))
        db.session.commit()

        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['tags'], ['Yellow T-shirt'])

    def test_already_checked_in_response_includes_checkin_tags(self):
        self.seed_static_data()
        tag = Tag(self.event_id, "CHECKIN")
        db.session.add(tag)
        db.session.commit()
        db.session.add(TagTranslation(tag.id, 'en', 'Yellow T-shirt'))
        db.session.commit()
        offer = attendance_repository.get_offer(self.event_id, self.guest_id)
        db.session.add(OfferTag(offer.id, tag.id))
        db.session.commit()

        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['already_checked_in'])
        self.assertEqual(data['tags'], ['Yellow T-shirt'])

    def test_checkin_response_includes_badge_exported(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': self.token_str}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('badge_exported', data)
        self.assertFalse(data['badge_exported'])

    def test_volunteer_can_checkin_guest_by_user_id(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['checked_in'])
        self.assertEqual(data['fullname'], self.guest_fullname)
        checkin = checkin_repository.get_latest(self.event_id, self.guest_id)
        self.assertEqual(checkin.method, 'manual')

    def test_manual_checkin_is_idempotent(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['already_checked_in'])

    def test_manual_checkin_non_guest_returns_not_on_guest_list(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.non_guest_id}
        )
        self.assertEqual(response.status_code, 403)

    def test_checkin_without_token_or_user_id_returns_missing_fields(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 400)

    def test_guestlist_reflects_checkin(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/guestlist', headers=header,
            query_string={'event_id': self.event_id}
        )
        data = json.loads(response.data)
        guest_row = [g for g in data if g['id'] == self.guest_id][0]
        self.assertFalse(guest_row['checked_in'])

        self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        response = self.app.get(
            '/api/v1/guestlist', headers=header,
            query_string={'event_id': self.event_id}
        )
        data = json.loads(response.data)
        guest_row = [g for g in data if g['id'] == self.guest_id][0]
        self.assertTrue(guest_row['checked_in'])

    def test_undo_removes_checkin(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        self.assertTrue(checkin_repository.is_checked_in(self.event_id, self.guest_id))
        response = self.app.delete(
            '/api/v1/attendance', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(checkin_repository.is_checked_in(self.event_id, self.guest_id))
        attendance = attendance_repository.get(self.event_id, self.guest_id)
        self.assertIsNotNone(attendance)
        self.assertFalse(attendance.confirmed)


class BadgeExportAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.admin = self.add_user('admin@test.com')
        self.guest = self.add_user('guest@test.com')
        self.guest_fullname = self.guest.full_name
        self.guest_firstname = self.guest.firstname
        self.guest_lastname = self.guest.lastname
        self.guest_id = self.guest.id
        self.event = self.add_event(
            {'en': 'Badge Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'BDGEV'
        )
        self.event_id = self.event.id
        self.add_event_role('admin', self.admin.id, self.event_id)
        offer = Offer(
            user_id=self.guest_id,
            event_id=self.event_id,
            offer_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            payment_required=False,
            candidate_response=True,
        )
        db.session.add(offer)
        db.session.commit()

    def test_badge_export_returns_guest_list_with_qr(self):
        self.seed_static_data()
        header = self.get_auth_header_for('admin@test.com')
        response = self.app.get(
            '/api/v1/checkin/badge-export', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['fullname'], self.guest_fullname)
        self.assertEqual(data[0]['firstname'], self.guest_firstname)
        self.assertEqual(data[0]['lastname'], self.guest_lastname)
        self.assertIn('token', data[0])
        self.assertIn('qr_url', data[0])

    def test_badge_export_forbidden_for_non_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.get(
            '/api/v1/checkin/badge-export', headers=header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 403)

    def test_badge_export_post_marks_guests(self):
        self.seed_static_data()
        header = self.get_auth_header_for('admin@test.com')
        response = self.app.post(
            '/api/v1/checkin/badge-export', headers=header,
            data={'event_id': self.event_id, 'user_ids': self.guest_id}
        )
        self.assertEqual(response.status_code, 200)
        attendance = attendance_repository.get(self.event_id, self.guest_id)
        self.assertIsNotNone(attendance)
        self.assertTrue(attendance.badge_exported)
        self.assertIsNotNone(attendance.badge_exported_at)
        # A row created purely to hold the flag must not be treated as confirmed.
        self.assertFalse(attendance.confirmed)

    def test_badge_export_post_defaults_to_all_guests(self):
        self.seed_static_data()
        header = self.get_auth_header_for('admin@test.com')
        response = self.app.post(
            '/api/v1/checkin/badge-export', headers=header,
            data={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['exported_count'], 1)
        attendance = attendance_repository.get(self.event_id, self.guest_id)
        self.assertTrue(attendance.badge_exported)

    def test_badge_export_post_forbidden_for_non_admin(self):
        self.seed_static_data()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.post(
            '/api/v1/checkin/badge-export', headers=header,
            data={'event_id': self.event_id, 'user_ids': self.guest_id}
        )
        self.assertEqual(response.status_code, 403)


class BlankBadgeAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.volunteer = self.add_user('volunteer@test.com')
        self.outsider = self.add_user('outsider@test.com')
        self.event = self.add_event(
            {'en': 'Blank Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'BLNKEV'
        )
        self.event_id = self.event.id
        self.add_event_role('registration-volunteer', self.volunteer.id, self.event_id)
        db.session.commit()

    def test_blank_badges_returns_requested_count_with_unique_tokens(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/blank-badges', headers=header,
            query_string={'event_id': self.event_id, 'count': 5}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 5)
        tokens = [b['token'] for b in data]
        self.assertEqual(len(set(tokens)), 5)
        for b in data:
            self.assertIn('token', b)
            self.assertIn('qr_url', b)
            self.assertIn(b['token'], b['qr_url'])

    def test_blank_badges_not_persisted(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/blank-badges', headers=header,
            query_string={'event_id': self.event_id, 'count': 3}
        )
        data = json.loads(response.data)
        # A blank token must not exist in the DB until it's linked to someone.
        for b in data:
            self.assertIsNone(qr_token_repository.resolve(b['token']))

    def test_blank_badges_forbidden_for_non_volunteer(self):
        self.seed_static_data()
        header = self.get_auth_header_for('outsider@test.com')
        response = self.app.get(
            '/api/v1/checkin/blank-badges', headers=header,
            query_string={'event_id': self.event_id, 'count': 2}
        )
        self.assertEqual(response.status_code, 403)

    def test_blank_badges_invalid_count_returns_missing_fields(self):
        self.seed_static_data()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.get(
            '/api/v1/checkin/blank-badges', headers=header,
            query_string={'event_id': self.event_id, 'count': 0}
        )
        self.assertEqual(response.status_code, 400)


class LinkBadgeAPITest(ApiTestCase):

    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba', 'blah.png', 'blah_big.png', 'deeplearningindaba')
        self.guest = self.add_user('guest@test.com')
        self.other_guest = self.add_user('other@test.com')
        self.volunteer = self.add_user('volunteer@test.com')
        self.non_guest = self.add_user('nonguest@test.com')
        self.guest_id = self.guest.id
        self.other_guest_id = self.other_guest.id
        self.non_guest_id = self.non_guest.id
        self.guest_fullname = self.guest.full_name
        self.event = self.add_event(
            {'en': 'Link Event'}, {'en': 'Desc'},
            datetime(2025, 6, 1), datetime(2025, 6, 10), 'LNKEV'
        )
        self.event_id = self.event.id
        self.add_event_role('registration-volunteer', self.volunteer.id, self.event_id)
        for uid in (self.guest_id, self.other_guest_id):
            offer = Offer(
                user_id=uid,
                event_id=self.event_id,
                offer_date=datetime.now(),
                expiry_date=datetime.now() + timedelta(days=15),
                payment_required=False,
                candidate_response=True,
            )
            db.session.add(offer)
        db.session.commit()
        self.add_email_template('attendance-confirmation')

    def _blank_token(self):
        return 'blankbadge' + str(datetime.now().timestamp()).replace('.', '')

    def test_link_replaces_attendee_token(self):
        self.seed_static_data()
        original = qr_token_repository.get_or_create(self.event_id, self.guest_id)
        original_token = original.token
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['token'], blank)
        self.assertEqual(data['fullname'], self.guest_fullname)
        # New token resolves to the guest; old token is now dead.
        resolved = qr_token_repository.resolve(blank)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.user_id, self.guest_id)
        self.assertIsNone(qr_token_repository.resolve(original_token))

    def test_my_ticket_reflects_linked_token(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        guest_header = self.get_auth_header_for('guest@test.com')
        response = self.app.get(
            '/api/v1/my-ticket', headers=guest_header,
            query_string={'event_id': self.event_id}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['token'], blank)

    def test_linked_badge_checks_in_attendee(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        response = self.app.post(
            '/api/v1/checkin', headers=header,
            data={'event_id': self.event_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['checked_in'])
        self.assertEqual(data['fullname'], self.guest_fullname)

    def test_cannot_link_badge_already_linked_to_another(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        # Attempting to link the same physical badge to a different attendee fails.
        response = self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.other_guest_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 409)
        # The badge still belongs to the original guest.
        self.assertEqual(qr_token_repository.resolve(blank).user_id, self.guest_id)

    def test_relinking_same_badge_to_same_user_is_idempotent(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        response = self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 200)

    def test_cannot_link_to_non_guest(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('volunteer@test.com')
        response = self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.non_guest_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 403)

    def test_link_forbidden_for_non_volunteer(self):
        self.seed_static_data()
        blank = self._blank_token()
        header = self.get_auth_header_for('guest@test.com')
        response = self.app.post(
            '/api/v1/checkin/link-badge', headers=header,
            data={'event_id': self.event_id, 'user_id': self.guest_id, 'token': blank}
        )
        self.assertEqual(response.status_code, 403)
