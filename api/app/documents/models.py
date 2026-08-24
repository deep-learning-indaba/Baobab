from datetime import datetime

from app import db


class DocumentTemplate(db.Model):
    """A document an event offers, e.g. "Invitation Letter".

    Owns eligibility and delivery settings. What an attendee asks for by name;
    which underlying Google file they get is decided by DocumentTemplateVariant.
    """
    __tablename__ = 'document_template'

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)

    # Stable slug, unique per event. Used in URLs and by the import helper from
    # the legacy invitation_template rows.
    key = db.Column(db.String(100), nullable=False)

    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    # Whether attendees can request this themselves, or it is admin-generated
    # only (a certificate of attendance is usually the latter until the event
    # is over).
    self_service = db.Column(db.Boolean(), nullable=False, default=False)

    # Tag/predicate expression deciding who may receive this at all. See
    # app/documents/eligibility.py.
    eligibility_expression = db.Column(db.JSON(), nullable=True)

    # 'attachment' | 'link' | 'both' | 'none' ('none' = download only, no email)
    delivery_mode = db.Column(db.String(16), nullable=False, default='attachment')
    # Key into email_template; None falls back to a built-in generic template.
    email_template_key = db.Column(db.String(50), nullable=True)

    # Placeholder-aware, e.g. "{lastname}_{firstname}_Certificate.pdf"
    filename_pattern = db.Column(db.String(255), nullable=True)

    # When false (default), a placeholder that resolves to a source but has no
    # value for this person is a hard error rather than an empty gap in the PDF.
    allow_blank_values = db.Column(db.Boolean(), nullable=False, default=False)

    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])

    translations = db.relationship('DocumentTemplateTranslation', cascade='all, delete-orphan',
                                    back_populates='document_template')
    variants = db.relationship('DocumentTemplateVariant', cascade='all, delete-orphan',
                                order_by='desc(DocumentTemplateVariant.priority)',
                                back_populates='document_template')
    form_links = db.relationship('DocumentTemplateForm', cascade='all, delete-orphan',
                                  order_by='desc(DocumentTemplateForm.order)',
                                  back_populates='document_template')

    __table_args__ = (
        db.UniqueConstraint('event_id', 'key', name='uq_document_template_event_key'),
    )

    def __init__(self, event_id, created_by_user_id, key, self_service=False,
                 eligibility_expression=None, delivery_mode='attachment',
                 email_template_key=None, filename_pattern=None,
                 allow_blank_values=False, is_active=True):
        self.event_id = event_id
        self.created_by_user_id = created_by_user_id
        self.key = key
        self.self_service = self_service
        self.eligibility_expression = eligibility_expression
        self.delivery_mode = delivery_mode
        self.email_template_key = email_template_key
        self.filename_pattern = filename_pattern
        self.allow_blank_values = allow_blank_values
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def get_translation(self, language):
        for translation in self.translations:
            if translation.language == language:
                return translation
        return None

    def active_variants(self):
        return [v for v in self.variants if v.is_active]

    def ordered_form_links(self):
        """Linked forms, highest `order` first - the order placeholder resolution searches them in."""
        return sorted(self.form_links, key=lambda link: -link.order)


class DocumentTemplateTranslation(db.Model):
    __tablename__ = 'document_template_translation'
    __table_args__ = (
        db.UniqueConstraint('document_template_id', 'language',
                             name='uq_document_template_translation'),
    )

    id = db.Column(db.Integer(), primary_key=True)
    document_template_id = db.Column(db.Integer(),
                                      db.ForeignKey('document_template.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    # Shown to the attendee on the request page, e.g. "Your letter will be
    # addressed to the embassy named in your registration form."
    instructions = db.Column(db.Text(), nullable=True)

    document_template = db.relationship('DocumentTemplate', back_populates='translations')

    def __init__(self, document_template_id, language, name, description=None, instructions=None):
        self.document_template_id = document_template_id
        self.language = language
        self.name = name
        self.description = description
        self.instructions = instructions


class DocumentTemplateVariant(db.Model):
    """One actual Google Docs/Slides file behind a document template, plus the
    tag rule and language that select it."""
    __tablename__ = 'document_template_variant'

    id = db.Column(db.Integer(), primary_key=True)
    document_template_id = db.Column(db.Integer(),
                                      db.ForeignKey('document_template.id'), nullable=False)

    # Admin-facing label, e.g. "Travel + accommodation (FR)".
    name = db.Column(db.String(255), nullable=False)

    google_file_id = db.Column(db.String(255), nullable=False)
    # 'document' (Google Docs) | 'presentation' (Google Slides)
    google_file_type = db.Column(db.String(16), nullable=False)
    # Cached from Drive so the admin UI can show a human name without an API call.
    google_file_name = db.Column(db.String(500), nullable=True)

    # None = applies to any language. Otherwise selected when it matches the
    # requested language, letting one template hold an EN and an FR file
    # instead of cramming both into one document.
    language = db.Column(db.String(2), nullable=True)

    # Tag expression; None matches everyone (the catch-all).
    selection_expression = db.Column(db.JSON(), nullable=True)
    # Higher wins. Variants are tried in descending priority; first match used.
    priority = db.Column(db.Integer(), nullable=False, default=0)

    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    # Results of the last template scan. Cached so the admin UI is fast and so
    # generation can fail fast without a Drive round-trip.
    detected_placeholders = db.Column(db.JSON(), nullable=True)   # ["firstname", "gender", ...]
    access_status = db.Column(db.String(32), nullable=True)
    access_checked_at = db.Column(db.DateTime(), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    document_template = db.relationship('DocumentTemplate', back_populates='variants')

    def __init__(self, document_template_id, name, google_file_id, google_file_type,
                 google_file_name=None, language=None, selection_expression=None,
                 priority=0, is_active=True):
        self.document_template_id = document_template_id
        self.name = name
        self.google_file_id = google_file_id
        self.google_file_type = google_file_type
        self.google_file_name = google_file_name
        self.language = language
        self.selection_expression = selection_expression
        self.priority = priority
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class DocumentTemplateForm(db.Model):
    """A form linked to a document template, in the order its answers are searched."""
    __tablename__ = 'document_template_form'

    REQUIREMENT_NONE = 'none'
    REQUIREMENT_RECOMMENDED = 'recommended'
    REQUIREMENT_REQUIRED = 'required'

    id = db.Column(db.Integer(), primary_key=True)
    document_template_id = db.Column(db.Integer(),
                                      db.ForeignKey('document_template.id'), nullable=False)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)

    # Resolution order. Forms are searched in descending `order`, so the
    # highest-ordered form is tried first.
    order = db.Column(db.Integer(), nullable=False)

    # 'none' | 'recommended' | 'required' - see DocumentTemplateForm.REQUIREMENT_*
    requirement = db.Column(db.String(16), nullable=False, default=REQUIREMENT_NONE)

    document_template = db.relationship('DocumentTemplate', back_populates='form_links')
    form = db.relationship('Form', foreign_keys=[form_id])
    translations = db.relationship('DocumentTemplateFormTranslation', cascade='all, delete-orphan',
                                    back_populates='document_template_form')

    __table_args__ = (
        db.UniqueConstraint('document_template_id', 'form_id', name='uq_document_template_form'),
    )

    def __init__(self, document_template_id, form_id, order, requirement=REQUIREMENT_NONE):
        self.document_template_id = document_template_id
        self.form_id = form_id
        self.order = order
        self.requirement = requirement

    def get_translation(self, language):
        for translation in self.translations:
            if translation.language == language:
                return translation
        return None

    @property
    def is_required(self):
        return self.requirement == self.REQUIREMENT_REQUIRED

    @property
    def is_recommended(self):
        return self.requirement == self.REQUIREMENT_RECOMMENDED


class DocumentTemplateFormTranslation(db.Model):
    """What the user is told when they haven't completed a required/recommended
    linked form. Used for both 'required' and 'recommended' - the difference is
    whether the message accompanies a blocker or a nudge, not what it says."""
    __tablename__ = 'document_template_form_translation'
    __table_args__ = (
        db.UniqueConstraint('document_template_form_id', 'language',
                             name='uq_document_template_form_translation'),
    )

    id = db.Column(db.Integer(), primary_key=True)
    document_template_form_id = db.Column(
        db.Integer(), db.ForeignKey('document_template_form.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    prompt_message = db.Column(db.Text(), nullable=False)

    document_template_form = db.relationship('DocumentTemplateForm', back_populates='translations')

    def __init__(self, document_template_form_id, language, prompt_message):
        self.document_template_form_id = document_template_form_id
        self.language = language
        self.prompt_message = prompt_message


class UserEventData(db.Model):
    """Admin-assigned key/value data about one person at one event.

    Exists for facts no form asks for because an admin assigns them after the
    fact - room allocation, bursary amount, badge category. Placeholders read
    it like any other source.
    """
    __tablename__ = 'user_event_data'

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text(), nullable=True)

    updated_at = db.Column(db.DateTime(), nullable=False)
    updated_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    event = db.relationship('Event', foreign_keys=[event_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    updated_by = db.relationship('AppUser', foreign_keys=[updated_by_user_id])

    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', 'key', name='uq_user_event_data'),
        db.Index('idx_user_event_data_lookup', 'event_id', 'user_id'),
    )

    def __init__(self, event_id, user_id, key, value, updated_by_user_id):
        self.event_id = event_id
        self.user_id = user_id
        self.key = key
        self.value = value
        self.updated_by_user_id = updated_by_user_id
        self.updated_at = datetime.now()


class GeneratedDocumentStatus:
    PENDING = 'pending'
    GENERATING = 'generating'
    GENERATED = 'generated'
    FAILED = 'failed'


class GeneratedDocument(db.Model):
    """A record of one produced PDF: who, which variant, what values, where the file is."""
    __tablename__ = 'generated_document'

    id = db.Column(db.Integer(), primary_key=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)
    document_template_id = db.Column(db.Integer(),
                                      db.ForeignKey('document_template.id'), nullable=False)
    variant_id = db.Column(db.Integer(),
                            db.ForeignKey('document_template_variant.id'), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    requested_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)

    status = db.Column(db.String(16), nullable=False, default=GeneratedDocumentStatus.PENDING)

    storage_blob_name = db.Column(db.String(255), nullable=True)
    filename = db.Column(db.String(255), nullable=True)

    # Every placeholder and the value substituted, with the source it came from.
    # What makes "why does Amina's letter say the wrong hostel?" answerable
    # months later, when the underlying answer has since been edited.
    placeholder_snapshot = db.Column(db.JSON(), nullable=True)

    error_code = db.Column(db.String(64), nullable=True)
    error_detail = db.Column(db.Text(), nullable=True)

    created_at = db.Column(db.DateTime(), nullable=False)
    generated_at = db.Column(db.DateTime(), nullable=True)

    event = db.relationship('Event', foreign_keys=[event_id])
    document_template = db.relationship('DocumentTemplate', foreign_keys=[document_template_id])
    variant = db.relationship('DocumentTemplateVariant', foreign_keys=[variant_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    requested_by = db.relationship('AppUser', foreign_keys=[requested_by_user_id])

    __table_args__ = (
        db.Index('idx_generated_document_lookup', 'document_template_id', 'user_id'),
    )

    def __init__(self, event_id, document_template_id, user_id, requested_by_user_id,
                 variant_id=None, status=GeneratedDocumentStatus.PENDING):
        self.event_id = event_id
        self.document_template_id = document_template_id
        self.user_id = user_id
        self.requested_by_user_id = requested_by_user_id
        self.variant_id = variant_id
        self.status = status
        self.created_at = datetime.now()

    def mark_generated(self, storage_blob_name, filename, placeholder_snapshot):
        self.status = GeneratedDocumentStatus.GENERATED
        self.storage_blob_name = storage_blob_name
        self.filename = filename
        self.placeholder_snapshot = placeholder_snapshot
        self.generated_at = datetime.now()

    def mark_failed(self, error_code, error_detail=None):
        self.status = GeneratedDocumentStatus.FAILED
        self.error_code = error_code
        self.error_detail = error_detail
