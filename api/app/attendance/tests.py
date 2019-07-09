from datetime import datetime
import json

from app import db
from app.attendance.models import Attendance
from app.attendance.repository import AttendanceRepository as attendance_repository
from app.events.models import Event, EventRole
from app.users.models import AppUser, Country, UserCategory
from app.utils.errors import ATTENDANCE_ALREADY_CONFIRMED, FORBIDDEN
from app.utils.testing import ApiTestCase

class AttendanceApiTest(ApiTestCase):
    
    def seed_static_data(self):
        user_category = UserCategory('PhD')
        db.session.add(user_category)

        country = Country('South Africa')
        db.session.add(country)

        attendee = AppUser('attendee@mail.com', 'attendee', 'attendee', 'Mr', 1, 1, 'M', 'Wits', 'CS', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        registration_admin = AppUser('ra@ra.com', 'registration', 'admin', 'Ms', 1, 1, 'F', 'NWU', 'Math', 'NA', 1, datetime(1984, 12, 12), 'Eng', 'abc')
        users = [attendee, registration_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)

        event = Event('indaba 2019', 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya ', datetime(2019, 8, 25), datetime(2019, 8, 31))
        db.session.add(event)

        event_role = EventRole('registration-admin', 2, 1)
        db.session.add(event_role)
        db.session.commit()
    
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
        params = {'user_id': 2, 'event_id': 1}

        response_get = self.app.get('/api/v1/attendance', headers=header, data=params)
        response_post = self.app.post('/api/v1/attendance', headers=header, data=params)
        response_delete = self.app.delete('/api/v1/attendance', headers=header, data=params)

        self.assertEqual(response_get.status_code, FORBIDDEN[1])
        self.assertEqual(response_post.status_code, FORBIDDEN[1])
        self.assertEqual(response_delete.status_code, FORBIDDEN[1])

    def setup_get_attendance(self):
        attendance = Attendance(1, 1, 2)
        attendance_repository.create(attendance)

    def test_get_attendance(self):
        self.seed_static_data()
        self.setup_get_attendance()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.get('/api/v1/attendance', headers=header, data=params)
        
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['updated_by_user_id'], 2)

    def test_post_attendance(self):
        self.seed_static_data()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.post('/api/v1/attendance', headers=header, data=params)

        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['event_id'], 1)
        self.assertEqual(data['updated_by_user_id'], 2)
    
    def test_cannot_register_attendance_twice(self):
        self.seed_static_data()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.post('/api/v1/attendance', headers=header, data=params)
        response = self.app.post('/api/v1/attendance', headers=header, data=params)

        self.assertEqual(response.status_code, ATTENDANCE_ALREADY_CONFIRMED[1])

    def setup_delete_attendance(self):
        attendance = Attendance(1, 1, 2)
        attendance_repository.create(attendance)

    def test_delete_attendance(self):
        self.seed_static_data()
        self.setup_delete_attendance()
        header = self.get_auth_header_for('ra@ra.com')
        params = {'user_id': 1, 'event_id': 1}

        response = self.app.delete('/api/v1/attendance', headers=header, data=params)

        attendance = attendance_repository.get(1, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(attendance, None)

