from app import db
from app.programme.models import Session, SessionTranslation, Speaker, SessionSpeaker, SessionTag
from app.tags.models import Tag, TagType
from app.users.models import AppUser
from app.attendance.repository import AttendanceRepository
from sqlalchemy.sql import func


class ProgrammeRepository:

    @staticmethod
    def list_sessions(event_id):
        return (db.session.query(Session)
                .filter_by(event_id=event_id)
                .order_by(Session.start_time)
                .all())

    @staticmethod
    def get_session(session_id):
        return db.session.query(Session).filter_by(id=session_id).first()

    @staticmethod
    def create_session(session):
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def delete_session(session):
        db.session.delete(session)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def list_speakers(event_id):
        return db.session.query(Speaker).filter_by(event_id=event_id).all()

    @staticmethod
    def get_speaker(speaker_id):
        return db.session.query(Speaker).filter_by(id=speaker_id).first()

    @staticmethod
    def create_speaker(speaker):
        db.session.add(speaker)
        db.session.commit()
        return speaker

    @staticmethod
    def find_linked_user(event_id, name, email):
        if email:
            u = db.session.query(AppUser).filter(func.lower(AppUser.email) == email.lower()).first()
            if u:
                return u.id
        if name:
            for row in AttendanceRepository.get_all_guests_for_event(event_id):
                user = row[0]
                if user.full_name.lower() == name.lower():
                    return user.id
        return None

    @staticmethod
    def list_session_types(event_id):
        return (db.session.query(Tag)
                .filter_by(event_id=event_id, tag_type=TagType.SESSION_TYPE, active=True)
                .all())

    @staticmethod
    def list_tracks(event_id):
        return (db.session.query(Tag)
                .filter_by(event_id=event_id, tag_type=TagType.TRACK, active=True)
                .all())
