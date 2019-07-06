from app import db
from app.attendance.models import Attendance

class AttendanceRepository():

    @staticmethod
    def is_exists(event_id, user_id):
        return db.session.query(Attendance.id)\
                         .filter_by(event_id=event_id, user_id=user_id)\
                         .first() is not None

    @staticmethod
    def create(attendance):
        db.session.add(attendance)
        db.session.commit()