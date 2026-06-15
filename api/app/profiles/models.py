from datetime import datetime

from app import db


class MemberProfile(db.Model):
    __tablename__ = 'member_profile'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False, unique=True)
    headline = db.Column(db.String(160), nullable=True)
    about = db.Column(db.String(2000), nullable=True)
    pronouns = db.Column(db.String(40), nullable=True)
    name_pronunciation = db.Column(db.String(120), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    country = db.Column(db.String(120), nullable=True)
    affiliation = db.Column(db.String(255), nullable=True)
    photo_url = db.Column(db.String(512), nullable=True)
    visibility = db.Column(db.String(20), nullable=False, default='community')
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('AppUser', foreign_keys=[user_id])
    links = db.relationship('MemberProfileLink', back_populates='profile', lazy='selectin')


class MemberProfileLink(db.Model):
    __tablename__ = 'member_profile_link'
    id = db.Column(db.Integer(), primary_key=True)
    profile_id = db.Column(db.Integer(), db.ForeignKey('member_profile.id'), nullable=False)
    link_type = db.Column(db.String(40), nullable=False)   # e.g. 'linkedin', 'twitter', 'scholar', 'website'
    url = db.Column(db.String(512), nullable=False)
    __table_args__ = (db.UniqueConstraint('profile_id', 'link_type', name='uq_profile_link_type'),)

    profile = db.relationship('MemberProfile', back_populates='links')


class MemberProfileInterest(db.Model):
    __tablename__ = 'member_profile_interest'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    tag_id = db.Column(db.Integer(), db.ForeignKey('tag.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'tag_id', name='uq_member_interest'),)
