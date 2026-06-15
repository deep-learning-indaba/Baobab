from app import db
from app.profiles.models import MemberProfile, MemberProfileLink, MemberProfileInterest
from app.tags.models import Tag, TagTranslation
from app.users.models import UserConsent
from app.attendance.repository import AttendanceRepository


class ProfileRepository:
    @staticmethod
    def get_or_create(user_id):
        p = db.session.query(MemberProfile).filter_by(user_id=user_id).first()
        if p is None:
            p = MemberProfile(user_id=user_id)
            db.session.add(p)
            db.session.commit()
        return p

    @staticmethod
    def get(user_id):
        return db.session.query(MemberProfile).filter_by(user_id=user_id).first()

    @staticmethod
    def set_interests(user_id, tag_ids):
        db.session.query(MemberProfileInterest).filter_by(user_id=user_id).delete()
        for tid in set(tag_ids):
            db.session.add(MemberProfileInterest(user_id=user_id, tag_id=tid))
        db.session.commit()

    @staticmethod
    def set_links(profile, links):
        allowed = {'linkedin', 'twitter', 'scholar', 'website'}
        db.session.query(MemberProfileLink).filter_by(profile_id=profile.id).delete()
        for link_type, url in (links or {}).items():
            if link_type in allowed and url:
                db.session.add(MemberProfileLink(
                    profile_id=profile.id, link_type=link_type, url=url))
        db.session.commit()

    @staticmethod
    def get_interests_for_user(user_id):
        rows = (db.session.query(MemberProfileInterest, Tag, TagTranslation)
                .join(Tag, Tag.id == MemberProfileInterest.tag_id)
                .outerjoin(
                    TagTranslation,
                    (TagTranslation.tag_id == Tag.id) & (TagTranslation.language == 'en')
                )
                .filter(MemberProfileInterest.user_id == user_id)
                .all())
        return [
            {'id': tag.id, 'name': tr.name if tr else str(tag.id)}
            for _, tag, tr in rows
        ]

    @staticmethod
    def list_community(event_id):
        guests = AttendanceRepository.get_all_guests_for_event(event_id)
        user_ids = [row[0].id for row in guests]
        profiles = db.session.query(MemberProfile).filter(
            MemberProfile.user_id.in_(user_ids)).all()
        by_uid = {p.user_id: p for p in profiles}
        result = []
        for row in guests:
            user = row[0]
            profile = by_uid.get(user.id)
            if profile is None or profile.visibility != 'hidden':
                result.append((user, profile))
        return result


class ConsentRepository:
    @staticmethod
    def get_latest(user_id, consent_type, event_id=None):
        q = db.session.query(UserConsent).filter_by(
            user_id=user_id, consent_type=consent_type)
        if event_id is not None:
            q = q.filter_by(event_id=event_id)
        return q.order_by(UserConsent.timestamp.desc()).first()

    @staticmethod
    def get_all_latest(user_id, event_id=None):
        q = db.session.query(UserConsent).filter_by(user_id=user_id)
        if event_id is not None:
            q = q.filter_by(event_id=event_id)
        rows = q.order_by(UserConsent.timestamp.desc()).all()
        seen = {}
        for row in rows:
            if row.consent_type not in seen:
                seen[row.consent_type] = row
        return list(seen.values())

    @staticmethod
    def append(user_id, event_id, consent_type, consent_version, granted):
        row = UserConsent()
        row.user_id = user_id
        row.event_id = event_id
        row.consent_type = consent_type
        row.consent_version = consent_version
        row.granted = granted
        db.session.add(row)
        db.session.commit()
        return row
