from datetime import datetime

from app import db


class EmailTemplate(db.Model):
    """An organisation's or event's override of an email type's default template.

    Defaults live in code (app/email_template/defaults/); a row here exists only
    where someone has customised one. event_id NULL means the override applies
    to the whole organisation.
    """

    __tablename__ = 'email_template'
    __table_args__ = (
        # Two partial indexes rather than one constraint: NULLs never collide in
        # a unique constraint, so (key, organisation, NULL, language) would
        # otherwise allow any number of organisation-level rows.
        db.Index('uq_email_template_event', 'key', 'event_id', 'language', unique=True,
                 postgresql_where=db.text('event_id IS NOT NULL'),
                 sqlite_where=db.text('event_id IS NOT NULL')),
        db.Index('uq_email_template_organisation', 'key', 'organisation_id', 'language', unique=True,
                 postgresql_where=db.text('event_id IS NULL'),
                 sqlite_where=db.text('event_id IS NULL')),
    )

    id = db.Column(db.Integer(), primary_key=True)
    key = db.Column(db.String(50), nullable=False)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    subject = db.Column(db.String(), nullable=False)
    # Markdown with Liquid tags.
    body = db.Column(db.Text(), nullable=False)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    updated_at = db.Column(db.DateTime(), nullable=True)

    event = db.relationship('Event', foreign_keys=[event_id])
    updated_by = db.relationship('AppUser', foreign_keys=[updated_by_user_id])

    def __init__(self, key, organisation_id, language, subject, body, event_id=None,
                 updated_by_user_id=None):
        self.key = key
        self.organisation_id = organisation_id
        self.event_id = event_id
        self.language = language
        self.subject = subject
        self.body = body
        self.updated_by_user_id = updated_by_user_id
        self.updated_at = datetime.utcnow()


class EmailTemplateRevision(db.Model):
    """Every saved version of an override, newest last. Messages record which
    revision produced them, so history shows the wording someone actually got."""

    __tablename__ = 'email_template_revision'

    id = db.Column(db.Integer(), primary_key=True)
    # Not a foreign key: an override deleted by "reset to default" keeps its
    # history, which messages sent from it still point at.
    email_template_id = db.Column(db.Integer(), nullable=False, index=True)
    key = db.Column(db.String(50), nullable=False)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    subject = db.Column(db.String(), nullable=False)
    body = db.Column(db.Text(), nullable=False)
    saved_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    saved_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)

    saved_by = db.relationship('AppUser', foreign_keys=[saved_by_user_id])

    @classmethod
    def of(cls, template, saved_by_user_id):
        return cls(
            email_template_id=template.id, key=template.key,
            organisation_id=template.organisation_id, event_id=template.event_id,
            language=template.language, subject=template.subject, body=template.body,
            saved_by_user_id=saved_by_user_id, saved_at=datetime.utcnow(),
        )


class EmailLayout(db.Model):
    """Branding around every email body, for an organisation or one of its events.

    Each field left NULL inherits: event -> organisation -> system default. The
    HTML skeleton itself is not editable (app/email_template/layout/base.html).
    """

    __tablename__ = 'email_layout'
    __table_args__ = (
        db.Index('uq_email_layout_event', 'event_id', 'language', unique=True,
                 postgresql_where=db.text('event_id IS NOT NULL'),
                 sqlite_where=db.text('event_id IS NOT NULL')),
        db.Index('uq_email_layout_organisation', 'organisation_id', 'language', unique=True,
                 postgresql_where=db.text('event_id IS NULL'),
                 sqlite_where=db.text('event_id IS NULL')),
    )

    EDITABLE_FIELDS = ('logo_url', 'brand_colour', 'header_markdown', 'footer_markdown')

    id = db.Column(db.Integer(), primary_key=True)
    organisation_id = db.Column(db.Integer(), db.ForeignKey('organisation.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=True)
    language = db.Column(db.String(2), nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    brand_colour = db.Column(db.String(7), nullable=True)
    # Markdown with Liquid; can use organisation and (for an event layout) event.
    header_markdown = db.Column(db.Text(), nullable=True)
    footer_markdown = db.Column(db.Text(), nullable=True)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=True)
    updated_at = db.Column(db.DateTime(), nullable=True)
