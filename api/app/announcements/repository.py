from datetime import datetime

from app import db
from app.announcements.models import Announcement, AnnouncementTranslation, AnnouncementReceipt


class AnnouncementRepository:

    @staticmethod
    def list_active(event_id, now=None):
        now = now or datetime.utcnow()
        return (db.session.query(Announcement)
                .filter(
                    Announcement.event_id == event_id,
                    Announcement.sent_at.isnot(None),
                    (Announcement.expiry_at.is_(None) | (Announcement.expiry_at > now))
                )
                .order_by(Announcement.sent_at.desc())
                .all())

    @staticmethod
    def list_all_for_event(event_id):
        return (db.session.query(Announcement)
                .filter(Announcement.event_id == event_id, Announcement.sent_at.isnot(None))
                .order_by(Announcement.sent_at.desc())
                .all())

    @staticmethod
    def get_by_id(announcement_id):
        return db.session.query(Announcement).get(announcement_id)

    @staticmethod
    def create(event_id, user_id, expiry_at, translations):
        ann = Announcement(
            event_id=event_id,
            created_by_user_id=user_id,
            sent_at=datetime.utcnow(),
            expiry_at=expiry_at,
        )
        db.session.add(ann)
        db.session.flush()

        for lang, title, body in translations:
            t = AnnouncementTranslation(
                announcement_id=ann.id,
                language=lang,
                title=title,
                body_markdown=body,
            )
            db.session.add(t)

        db.session.commit()
        return ann

    @staticmethod
    def delete(announcement):
        db.session.delete(announcement)
        db.session.commit()

    # --- Receipt helpers ---

    @staticmethod
    def get_receipt(announcement_id, user_id):
        return (db.session.query(AnnouncementReceipt)
                .filter_by(announcement_id=announcement_id, user_id=user_id)
                .first())

    @staticmethod
    def create_receipt(announcement_id, user_id, delivered_at=None, channel='inbox', opened_at=None):
        receipt = AnnouncementReceipt(
            announcement_id=announcement_id,
            user_id=user_id,
            delivered_at=delivered_at or datetime.utcnow(),
            opened_at=opened_at,
            channel=channel,
        )
        db.session.add(receipt)
        return receipt

    @staticmethod
    def backfill_receipts_for_user(event_id, user_id):
        """Lazily create auto-read receipts for a late check-in user."""
        now = datetime.utcnow()
        sent = (db.session.query(Announcement)
                .filter(Announcement.event_id == event_id, Announcement.sent_at.isnot(None))
                .all())
        for ann in sent:
            existing = (db.session.query(AnnouncementReceipt)
                        .filter_by(announcement_id=ann.id, user_id=user_id)
                        .first())
            if not existing:
                db.session.add(AnnouncementReceipt(
                    announcement_id=ann.id,
                    user_id=user_id,
                    delivered_at=now,
                    opened_at=now,
                    channel='inbox',
                ))
        db.session.commit()

    @staticmethod
    def get_receipts_for_user(event_id, user_id):
        return (db.session.query(AnnouncementReceipt)
                .join(Announcement, Announcement.id == AnnouncementReceipt.announcement_id)
                .filter(Announcement.event_id == event_id, AnnouncementReceipt.user_id == user_id)
                .all())

    @staticmethod
    def count_delivered(announcement_id):
        return (db.session.query(AnnouncementReceipt)
                .filter_by(announcement_id=announcement_id)
                .count())

    @staticmethod
    def count_opened(announcement_id):
        return (db.session.query(AnnouncementReceipt)
                .filter(
                    AnnouncementReceipt.announcement_id == announcement_id,
                    AnnouncementReceipt.opened_at.isnot(None),
                )
                .count())
