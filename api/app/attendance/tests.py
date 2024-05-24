from datetime import datetime
import json

from app import db
from app.attendance.models import Attendance
from app.attendance.repository import AttendanceRepository as attendance_repository
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

    def setup_delete_attendance(self):
        attendance = Attendance(1, 1, 2)
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
        self.assertEqual(attendance, None)
