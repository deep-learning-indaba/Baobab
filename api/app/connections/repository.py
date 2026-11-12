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
    def create_report(event_id, reporter_id, reported_id, reason, category='person', reported_photo_url=None):
        r = ConnectionReport(
            event_id=event_id, reporter_user_id=reporter_id,
            reported_user_id=reported_id, reason=reason,
            category=category, reported_photo_url=reported_photo_url)
        db.session.add(r)
        db.session.commit()
        return r

    @staticmethod
    def get_open_report(event_id, reporter_id, reported_id, category):
        return db.session.query(ConnectionReport).filter_by(
            event_id=event_id, reporter_user_id=reporter_id,
            reported_user_id=reported_id, category=category, status='open').first()

    @staticmethod
    def list_open_reports(event_id):
        return db.session.query(ConnectionReport).filter_by(
            event_id=event_id, status='open').order_by(
            ConnectionReport.created_at.asc(), ConnectionReport.id.asc()).all()

    @staticmethod
    def get_report(event_id, report_id):
        return db.session.query(ConnectionReport).filter_by(
            id=report_id, event_id=event_id).first()

    @staticmethod
    def dismiss_report(report, resolver_id):
        if report.status == 'open':
            report.status = 'dismissed'
            report.resolved_by_user_id = resolver_id
            report.resolved_at = datetime.utcnow()
            db.session.commit()
        return report

    @staticmethod
    def action_photo_reports(event_id, reported_id, resolver_id, extra_report=None):
        """Mark every open photo report for the user (plus extra_report) as actioned.

        Returns the ids of the reports that were actioned.
        """
        rows = db.session.query(ConnectionReport).filter_by(
            event_id=event_id, reported_user_id=reported_id,
            category='photo', status='open').all()
        if extra_report is not None and extra_report.status == 'open' and extra_report not in rows:
            rows.append(extra_report)
        now = datetime.utcnow()
        for r in rows:
            r.status = 'actioned'
            r.resolved_by_user_id = resolver_id
            r.resolved_at = now
        db.session.commit()
        return sorted(r.id for r in rows)
