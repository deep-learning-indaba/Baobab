import os
import re
from datetime import datetime

from sqlalchemy import func

from app import db
from app.email_template.models import EmailLayout, EmailTemplate, EmailTemplateRevision


DEFAULTS_DIR = os.path.join(os.path.dirname(__file__), 'defaults')
LAYOUT_PATH = os.path.join(os.path.dirname(__file__), 'layout', 'base.html')

DEFAULT_BRAND_COLOUR = '#0f5238'
BRAND_COLOUR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class Source:
    EVENT = 'event'
    ORGANISATION = 'organisation'
    DEFAULT = 'default'


class ResolvedTemplate:
    def __init__(self, key, language, subject, body, source, template_id=None, revision_id=None,
                 updated_at=None, updated_by=None):
        self.key = key
        self.language = language
        self.subject = subject
        self.body = body
        self.source = source
        self.template_id = template_id
        self.revision_id = revision_id
        self.updated_at = updated_at
        self.updated_by = updated_by


_FRONT_MATTER = re.compile(r'\A---\n(.*?)\n---\n?', re.DOTALL)
_default_cache = {}


def _parse_default(text):
    match = _FRONT_MATTER.match(text)
    if not match:
        raise ValueError('Default email template is missing its front matter')
    meta = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            name, value = line.split(':', 1)
            meta[name.strip()] = value.strip()
    return meta.get('subject', ''), text[match.end():].rstrip('\n')


def load_default(key, language):
    """(subject, body) from defaults/<key>.<language>.md, or None."""
    cache_key = (key, language)
    if cache_key not in _default_cache:
        path = os.path.join(DEFAULTS_DIR, '{}.{}.md'.format(key, language))
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                _default_cache[cache_key] = _parse_default(f.read())
        else:
            _default_cache[cache_key] = None
    return _default_cache[cache_key]


def default_languages(key):
    return sorted(name.rsplit('.', 2)[1] for name in os.listdir(DEFAULTS_DIR)
                  if name.startswith(key + '.') and name.count('.') == 2 and name.endswith('.md')
                  and name.rsplit('.', 2)[0] == key)


def _fallback_languages(language, event):
    languages = [language]
    if event is not None:
        languages.append(event.primary_language)
    languages.append('en')
    return list(dict.fromkeys(l for l in languages if l))


def latest_revision_id(template_id):
    return (db.session.query(func.max(EmailTemplateRevision.id))
            .filter(EmailTemplateRevision.email_template_id == template_id)
            .scalar())


class EmailTemplateRepository:

    @staticmethod
    def get_override(key, organisation_id, event_id, language):
        query = db.session.query(EmailTemplate).filter_by(key=key, language=language)
        if event_id is None:
            query = query.filter(EmailTemplate.event_id.is_(None),
                                 EmailTemplate.organisation_id == organisation_id)
        else:
            query = query.filter(EmailTemplate.event_id == event_id)
        return query.first()

    @staticmethod
    def overrides_for(key, organisation_id, event_id=None):
        """Overrides of a key at the organisation level and (if given) one event."""
        query = db.session.query(EmailTemplate).filter(EmailTemplate.key == key)
        levels = [db.and_(EmailTemplate.organisation_id == organisation_id, EmailTemplate.event_id.is_(None))]
        if event_id is not None:
            levels.append(EmailTemplate.event_id == event_id)
        return query.filter(db.or_(*levels)).all()

    @staticmethod
    def resolve(email_type, organisation_id, event, language, below=None):
        """The template to send for this type/organisation/event/language.

        Tried in order, for the language and then the event's primary language
        and English: event override, organisation override, code default.
        `below` skips levels at and above it - what the editor shows as
        "inherited" for an override that is being edited or reset.
        """
        levels = [Source.EVENT, Source.ORGANISATION, Source.DEFAULT]
        if below is not None:
            levels = levels[levels.index(below) + 1:]
        if event is None or not email_type.is_event_scoped:
            levels = [level for level in levels if level != Source.EVENT]
            event_for_language = event
        else:
            event_for_language = event

        for language_option in _fallback_languages(language, event_for_language):
            for level in levels:
                if level == Source.DEFAULT:
                    default = load_default(email_type.default_key, language_option)
                    if default is not None:
                        return ResolvedTemplate(email_type.key, language_option, default[0], default[1],
                                                Source.DEFAULT)
                    continue
                event_id = event.id if level == Source.EVENT else None
                override = EmailTemplateRepository.get_override(
                    email_type.key, organisation_id, event_id, language_option)
                if override is not None:
                    return ResolvedTemplate(
                        email_type.key, language_option, override.subject, override.body, level,
                        template_id=override.id, revision_id=latest_revision_id(override.id),
                        updated_at=override.updated_at,
                        updated_by=override.updated_by.full_name if override.updated_by else None)
        return None

    @staticmethod
    def save(key, organisation_id, event_id, language, subject, body, user_id):
        template = EmailTemplateRepository.get_override(key, organisation_id, event_id, language)
        if template is None:
            template = EmailTemplate(key, organisation_id, language, subject, body, event_id=event_id,
                                     updated_by_user_id=user_id)
            db.session.add(template)
        else:
            template.subject = subject
            template.body = body
            template.updated_by_user_id = user_id
            template.updated_at = datetime.utcnow()
        db.session.flush()
        db.session.add(EmailTemplateRevision.of(template, user_id))
        db.session.commit()
        return template

    @staticmethod
    def delete(key, organisation_id, event_id, language):
        template = EmailTemplateRepository.get_override(key, organisation_id, event_id, language)
        if template is None:
            return False
        db.session.delete(template)
        db.session.commit()
        return True

    @staticmethod
    def revisions(key, organisation_id, event_id, language, limit=50):
        query = db.session.query(EmailTemplateRevision).filter_by(
            key=key, organisation_id=organisation_id, language=language)
        query = (query.filter(EmailTemplateRevision.event_id.is_(None)) if event_id is None
                 else query.filter(EmailTemplateRevision.event_id == event_id))
        return query.order_by(EmailTemplateRevision.id.desc()).limit(limit).all()


class ResolvedLayout:
    def __init__(self, logo_url=None, brand_colour=DEFAULT_BRAND_COLOUR, header_markdown=None,
                 footer_markdown=None):
        self.logo_url = logo_url
        self.brand_colour = brand_colour
        self.header_markdown = header_markdown
        self.footer_markdown = footer_markdown


class EmailLayoutRepository:

    @staticmethod
    def get(organisation_id, event_id, language):
        query = db.session.query(EmailLayout).filter_by(organisation_id=organisation_id, language=language)
        query = (query.filter(EmailLayout.event_id.is_(None)) if event_id is None
                 else query.filter(EmailLayout.event_id == event_id))
        return query.first()

    @staticmethod
    def resolve(organisation_id, event, language, below=None):
        """Each field from the first layout that sets it: event, then
        organisation, in the requested language and then the fallbacks.
        `below='event'` gives what an event layout inherits."""
        rows = []
        for language_option in _fallback_languages(language, event):
            if event is not None and below is None:
                rows.append(EmailLayoutRepository.get(organisation_id, event.id, language_option))
            if below != Source.ORGANISATION:
                rows.append(EmailLayoutRepository.get(organisation_id, None, language_option))
        rows = [row for row in rows if row is not None]

        resolved = ResolvedLayout()
        for field in EmailLayout.EDITABLE_FIELDS:
            for row in rows:
                value = getattr(row, field)
                if value:
                    setattr(resolved, field, value)
                    break
        return resolved

    @staticmethod
    def save(organisation_id, event_id, language, values, user_id):
        layout = EmailLayoutRepository.get(organisation_id, event_id, language)
        if layout is None:
            layout = EmailLayout(organisation_id=organisation_id, event_id=event_id, language=language)
            db.session.add(layout)
        for field in EmailLayout.EDITABLE_FIELDS:
            if field in values:
                setattr(layout, field, values[field] or None)
        layout.updated_by_user_id = user_id
        layout.updated_at = datetime.utcnow()
        db.session.commit()
        return layout


def load_layout_source():
    if 'layout' not in _default_cache:
        with open(LAYOUT_PATH, encoding='utf-8') as f:
            _default_cache['layout'] = f.read()
    return _default_cache['layout']
