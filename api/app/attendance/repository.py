from app import db
from app.attendance.models import Attendance


class AttendanceRepository:
    @staticmethod
    def exists(event_id, user_id):
        return (
            db.session.query(Attendance.id)
            .filter_by(event_id=event_id, user_id=user_id)
            .first()
            is not None
        )

    @staticmethod
    def get(event_id, user_id):
        return (
            db.session.query(Attendance)
            .filter_by(event_id=event_id, user_id=user_id)
            .first()
        )

    @staticmethod
    def create(attendance):
        db.session.add(attendance)
        db.session.commit()

    @staticmethod
    def delete(attendance):
        db.session.delete(attendance)
        db.session.commit()
