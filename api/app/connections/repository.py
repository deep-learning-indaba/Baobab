from datetime import datetime

from sqlalchemy import or_

from app import db
from app.connections.models import Connection, ConnectionStatus, ConnectionReport


class ConnectionRepository:

    @staticmethod
    def get(event_id, from_id, to_id):
        return db.session.query(Connection).filter_by(
            event_id=event_id, from_user_id=from_id, to_user_id=to_id).first()

    @staticmethod
    def is_blocked(event_id, scanner_id, target_id):
        row = ConnectionRepository.get(event_id, scanner_id, target_id)
        return row is not None and row.status == ConnectionStatus.BLOCKED

    @staticmethod
    def upsert_request(event_id, from_id, to_id, method='scan'):
        row = ConnectionRepository.get(event_id, from_id, to_id)
        if row is None:
            row = Connection(
                event_id=event_id, from_user_id=from_id, to_user_id=to_id,
                method=method, status=ConnectionStatus.PENDING)
            db.session.add(row)
        elif row.status in (ConnectionStatus.REJECTED, ConnectionStatus.WITHDRAWN):
            row.status = ConnectionStatus.PENDING
            row.updated_at = datetime.utcnow()
        db.session.commit()
        return row

    @staticmethod
    def set_status(event_id, from_id, to_id, status):
        row = ConnectionRepository.get(event_id, from_id, to_id)
        if row is None:
            row = Connection(
                event_id=event_id, from_user_id=from_id, to_user_id=to_id,
                method='scan', status=status)
            db.session.add(row)
        else:
            row.status = status
            row.updated_at = datetime.utcnow()
        db.session.commit()
        return row

    @staticmethod
    def list_for_user(event_id, user_id):
        return db.session.query(Connection).filter(
            Connection.event_id == event_id,
            or_(Connection.from_user_id == user_id, Connection.to_user_id == user_id)
        ).order_by(Connection.updated_at.desc()).all()

    @staticmethod
    def create_report(event_id, reporter_id, reported_id, reason):
        r = ConnectionReport(
            event_id=event_id, reporter_user_id=reporter_id,
            reported_user_id=reported_id, reason=reason)
        db.session.add(r)
        db.session.commit()
        return r
