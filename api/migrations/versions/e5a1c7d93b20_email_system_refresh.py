"""Email system refresh: Liquid templates, layouts, outbox history columns

Revision ID: e5a1c7d93b20
Revises: 9c3e6a1f40d7
Create Date: 2026-10-04 12:00:00.000000

Default templates move into code (app/email_template/defaults/). This keeps a
full copy of every existing email_template row in email_template_legacy, then
rebuilds email_template to hold only event-level overrides, converted from
str.format placeholders to Liquid. Keys that the code now sends as one merged
type (the four offer-* variants, etc.) are combined into a single template with
{% if %} branches that reproduce exactly which text each case used to get.

See docs/temp/EMAIL_SYSTEM_DESIGN.md section 10.
"""

# revision identifiers, used by Alembic.
revision = 'e5a1c7d93b20'
down_revision = '9c3e6a1f40d7'

import re
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------- conversion

_COMMON = {
    'salutation': 'recipient.salutation',
    'title': 'recipient.title',
    'firstname': 'recipient.firstname',
    'lastname': 'recipient.lastname',
    'event_name': 'event.name',
}

_ANSWERS_SECTIONS = ('{% for section in response.sections %}{{ section.name }}\n--------------------\n\n'
                     '{% for item in section.answers %}{{ item.question }}\n{{ item.answer }}\n\n'
                     '{% endfor %}{% endfor %}')
_REGISTRATION_ANSWERS = ('{% for item in registration.answers %}Question:{{ item.question }}\n'
                         'Answer:{{ item.answer }}\n{% endfor %}')
_GRANTS = '{% for grant in offer.grants %}\n• {{ grant.name }}: {{ grant.description }}{% endfor %}'
_NOTES = '{% for note in offer.notes %}\n• {{ note.name }}: {{ note.description }}{% endfor %}'
_EXPIRY = '{{ offer.expiry_date | date: "%Y-%m-%d" }}'
_DEADLINE = '{{ event.application_close | date: "%A %-d %B %Y" }}'

# Per legacy key: whole-URL patterns replaced first, then single placeholders.
# Every parameter each call site passed is covered, so any template that
# rendered before converts completely.
_URLS = {
    'offer': [('{host}/{event_key}/offer', '{{ offer.url }}'), ('{host}/offer', '{{ offer.url }}')],
    'offer-reset': [('{host}/{event_key}/offer', '{{ offer.url }}')],
    'offer-paid': [('{host}/{event_key}/registration', '{{ event.registration_url }}')],
    'guest': [('{host}/{event_key}/registration', '{{ guest.registration_url }}')],
    'new-guest': [('{host}/resetPassword?resetToken={reset_code}', '{{ account.set_password_url }}'),
                  ('{host}/{event_key}/registration', '{{ guest.registration_url }}'),
                  ('{host}/profile', '{{ account.profile_url }}')],
    'reviews': [('{baobab_host}/{event_key}/reviewlist', '{{ reviews.url }}')],
    'invoice': [('{system_url}/payment/{invoice_id}', '{{ invoice.payment_url }}')],
}

_PARAMS = {
    'application-submitted': {'event_description': 'event.description',
                              'question_answer_summary': ('raw', _ANSWERS_SECTIONS)},
    'withdrawal': {'organisation_name': 'organisation.name'},
    'form-response-deleted': {'form_name': 'form.name', 'event_email': 'event.email_from'},
    # The call site never passed `event`, so this template could only fail; map
    # it to what it plainly meant.
    'application-not-submitted': {'event': 'event.name', 'organisation_name': 'organisation.name',
                                  'deadline': ('raw', _DEADLINE)},
    'application-not-started': {'event': 'event.name', 'organisation_name': 'organisation.name',
                                'system_name': 'organisation.system_name', 'deadline': ('raw', _DEADLINE)},
    'reference-request': {'candidate': 'candidate.name', 'candidate_firstname': 'candidate.firstname',
                          'nominator': 'nominator.name', 'event_url': 'event.website_url',
                          'application_close_date': 'reference.deadline', 'link': 'reference.url'},
    'reviews-assigned': {'num_reviews': 'reviews.count', 'baobab_host': 'organisation.system_url',
                         'system_name': 'organisation.system_name', 'event_key': 'event.key'},
    'outcome-rejected': {'host': 'organisation.system_url'},
    'outcome-waitlist': {'host': 'organisation.system_url'},
    'offer': {'host': 'organisation.system_url', 'expiry_date': ('raw', _EXPIRY),
              'event_email_from': 'event.email_from', 'grants': ('raw', _GRANTS), 'notes': ('raw', _NOTES),
              'payment_amount': 'offer.fee.amount', 'payment_currency': 'offer.fee.currency',
              'event_key': 'event.key'},
    'offer-paid': {'host': 'organisation.system_url', 'event_key': 'event.key'},
    'offer-reset': {'host': 'organisation.system_url', 'event_key': 'event.key',
                    'event_email_from': 'event.email_from', 'expiry_date': ('raw', _EXPIRY)},
    'invoice': {'system_url': 'organisation.system_url', 'invoice_id': 'invoice.number',
                'due_date': ('raw', '{{ invoice.due_date | date: "%d %B %Y" }}')},
    'registration-received': {'summary': ('raw', _REGISTRATION_ANSWERS)},
    'guest-registration-confirmation': {'summary': ('raw', _REGISTRATION_ANSWERS)},
    'guest-invitation': {'role': 'guest.role', 'system_name': 'organisation.system_name',
                         'host': 'organisation.system_url', 'event_key': 'event.key'},
    'new-guest': {'role': 'guest.role', 'system_name': 'organisation.system_name',
                  'host': 'organisation.system_url', 'event_key': 'event.key'},
    'guest-removal': {'event_email': 'event.email_from', 'role': 'guest.role'},
    'indemnity-signed': {'indemnity_form': 'indemnity.text'},
    'generated-document': {'document_name': 'document.name'},
}

_URL_GROUP = {'offer': 'offer', 'offer-reset': 'offer-reset', 'offer-paid': 'offer-paid',
              'guest-invitation': 'guest', 'new-guest': 'new-guest', 'reviews-assigned': 'reviews',
              'invoice': 'invoice'}

_PLACEHOLDER = re.compile(r'\{\{|\}\}|\{([A-Za-z_][A-Za-z0-9_]*)\}')


def _to_liquid(text, new_key, warnings, label):
    # URL patterns first, protected from the single-placeholder pass.
    protected = []
    for legacy, replacement in _URLS.get(_URL_GROUP.get(new_key), []):
        while legacy in text:
            protected.append(replacement)
            text = text.replace(legacy, '\x00{}\x00'.format(len(protected) - 1), 1)

    params = dict(_COMMON, **_PARAMS.get(new_key, {}))

    def substitute(match):
        token = match.group(0)
        if token == '{{':
            return '{{ "{" }}'
        if token == '}}':
            return '{{ "}" }}'
        name = match.group(1)
        target = params.get(name)
        if target is None:
            warnings.append('{}: unknown placeholder {{{}}} left as text'.format(label, name))
            return '{{ "{" }}' + name + '{{ "}" }}'
        if isinstance(target, tuple):
            return target[1]
        return '{{ ' + target + ' }}'

    # A str.format template can't contain a literal "{%" (it would have failed
    # to format), so no legacy text can accidentally open a Liquid tag.
    text = _PLACEHOLDER.sub(substitute, text)
    for index, replacement in enumerate(protected):
        text = text.replace('\x00{}\x00'.format(index), replacement)
    return text


# new key -> (condition tree, legacy keys used as leaves)
# A tree is either a legacy key, or (condition, if_true, if_false).
_MERGES = {
    'offer': ('offer.payment_required',
              ('offer.grants.size > 0', 'offer-fee-grants', 'offer-fee'),
              ('offer.grants.size > 0', 'offer-nofee-grants', 'offer-nofee')),
    'guest-invitation': ('event.is_registration_open', 'guest-invitation-with-registration', 'guest-invitation'),
    'new-guest': ('event.is_registration_open', 'new-guest-registration', 'new-guest-no-registration'),
    'registration-received': ('registration.confirmed', 'registration-with-confirmation',
                              'registration-pending-confirmation'),
    'reference-request': ('nominator', 'reference-request', 'reference-request-self-nomination'),
}

# Kept under their own key (possibly renamed), no merging.
_RENAMES = {
    'withdrawal': 'withdrawal', 'form-response-deleted': 'form-response-deleted',
    'application-not-submitted': 'application-not-submitted', 'application-not-started': 'application-not-started',
    'reviews-assigned': 'reviews-assigned', 'outcome-rejected': 'outcome-rejected',
    'outcome-waitlist': 'outcome-waitlist', 'offer-paid': 'offer-paid', 'offer-reset': 'offer-reset',
    'invoice': 'invoice', 'registration-confirmed': 'registration-confirmed',
    'guest-registration-confirmation': 'guest-registration-confirmation', 'guest-removal': 'guest-removal',
    'attendance-confirmation': 'attendance-confirmation', 'indemnity-signed': 'indemnity-signed',
    'invitation-letter': 'invitation-letter', 'generated-document': 'generated-document',
}


def _leaves(tree):
    if isinstance(tree, str):
        return [tree]
    return _leaves(tree[1]) + _leaves(tree[2])


def _build(tree, texts):
    """A Liquid if/else tree over `texts` (legacy key -> converted text),
    collapsing branches whose texts are identical."""
    if isinstance(tree, str):
        return texts[tree]
    condition, if_true, if_false = tree
    yes = _build(if_true, texts)
    no = _build(if_false, texts)
    if yes == no:
        return yes
    return '{% if ' + condition + ' %}' + yes + '{% else %}' + no + '{% endif %}'


def _convert(rows, event_types, document_keys, warnings):
    """[(key, event_id, language, subject, body)] for the converted overrides."""
    global_rows = {(r['key'], r['language']): r for r in rows if r['event_id'] is None}
    by_event = {}
    for r in rows:
        if r['event_id'] is not None:
            by_event.setdefault((r['event_id'], r['language']), {})[r['key']] = r

    converted = []
    for (event_id, language), overrides in sorted(by_event.items()):
        label = 'event {} ({})'.format(event_id, language)
        handled = set()

        # application-submitted: a CALL event only ever used the -call variant.
        # event_type is stored as the enum's name, e.g. 'CALL'.
        variant = ('confirmation-response-call' if (event_types.get(event_id) or '').lower() == 'call'
                   else 'confirmation-response')
        for legacy in ('confirmation-response', 'confirmation-response-call'):
            handled.add(legacy)
            if legacy in overrides and legacy != variant:
                warnings.append('{}: dropped override of "{}", which this event type never sent '
                                '(kept in email_template_legacy)'.format(label, legacy))
        if variant in overrides:
            r = overrides[variant]
            converted.append(('application-submitted', event_id, language,
                              _to_liquid(r['subject'], 'application-submitted', warnings, label),
                              _to_liquid(r['template'], 'application-submitted', warnings, label)))

        for new_key, tree in _MERGES.items():
            legacy_keys = _leaves(tree)
            handled.update(legacy_keys)
            if not any(k in overrides for k in legacy_keys):
                continue
            subjects, bodies = {}, {}
            for legacy in legacy_keys:
                source = overrides.get(legacy) or global_rows.get((legacy, language)) or global_rows.get((legacy, 'en'))
                if source is None:
                    break
                subjects[legacy] = _to_liquid(source['subject'], new_key, warnings, label)
                bodies[legacy] = _to_liquid(source['template'], new_key, warnings, label)
            else:
                converted.append((new_key, event_id, language,
                                  _build(tree, subjects), _build(tree, bodies)))
                continue
            warnings.append('{}: {} not converted - no text for every case it covers; '
                            'the code default applies'.format(label, new_key))

        for legacy, r in overrides.items():
            if legacy in handled:
                continue
            new_key = _RENAMES.get(legacy)
            params_key = new_key
            if new_key is None and legacy in document_keys.get(event_id, set()):
                new_key, params_key = legacy, 'generated-document'
            if new_key is None:
                warnings.append('{}: dropped override of unused key "{}" (kept in email_template_legacy)'
                                .format(label, legacy))
                continue
            converted.append((new_key, event_id, language,
                              _to_liquid(r['subject'], params_key, warnings, label),
                              _to_liquid(r['template'], params_key, warnings, label)))
    return converted


# ---------------------------------------------------------------------------- migration

def upgrade():
    bind = op.get_bind()

    # --- keep everything as it was
    op.execute('CREATE TABLE email_template_legacy AS SELECT * FROM email_template')

    rows = [dict(r) for r in bind.execute(sa.text(
        'SELECT id, key, event_id, language, subject, template FROM email_template ORDER BY id'))]
    events = {r.id: (r.organisation_id, r.event_type) for r in bind.execute(sa.text(
        'SELECT id, organisation_id, event_type FROM event'))}
    document_keys = {}
    for r in bind.execute(sa.text(
            "SELECT event_id, email_template_key FROM document_template "
            "WHERE email_template_key IS NOT NULL AND email_template_key <> ''")):
        document_keys.setdefault(r.event_id, set()).add(r.email_template_key)

    warnings = []
    converted = _convert(rows, {k: v[1] for k, v in events.items()}, document_keys, warnings)
    for warning in warnings:
        print('email migration: ' + warning)

    # --- reshape email_template
    op.execute('DELETE FROM email_template')
    op.drop_constraint('uq_email_template_key_event_id', 'email_template', type_='unique')
    op.alter_column('email_template', 'template', new_column_name='body', type_=sa.Text(),
                    existing_nullable=False)
    op.add_column('email_template', sa.Column('organisation_id', sa.Integer(), nullable=False))
    op.add_column('email_template', sa.Column('updated_by_user_id', sa.Integer(), nullable=True))
    op.add_column('email_template', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_email_template_organisation', 'email_template', 'organisation',
                          ['organisation_id'], ['id'])
    op.create_foreign_key('fk_email_template_updated_by', 'email_template', 'app_user',
                          ['updated_by_user_id'], ['id'])
    op.create_index('uq_email_template_event', 'email_template', ['key', 'event_id', 'language'],
                    unique=True, postgresql_where=sa.text('event_id IS NOT NULL'))
    op.create_index('uq_email_template_organisation', 'email_template',
                    ['key', 'organisation_id', 'language'], unique=True,
                    postgresql_where=sa.text('event_id IS NULL'))

    op.create_table(
        'email_template_revision',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_template_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('organisation_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('saved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('saved_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['saved_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_template_revision_email_template_id', 'email_template_revision',
                    ['email_template_id'])

    op.create_table(
        'email_layout',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organisation_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('brand_colour', sa.String(length=7), nullable=True),
        sa.Column('header_markdown', sa.Text(), nullable=True),
        sa.Column('footer_markdown', sa.Text(), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisation.id']),
        sa.ForeignKeyConstraint(['event_id'], ['event.id']),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('uq_email_layout_event', 'email_layout', ['event_id', 'language'], unique=True,
                    postgresql_where=sa.text('event_id IS NOT NULL'))
    op.create_index('uq_email_layout_organisation', 'email_layout', ['organisation_id', 'language'],
                    unique=True, postgresql_where=sa.text('event_id IS NULL'))

    now = datetime.utcnow()
    for key, event_id, language, subject, body in converted:
        organisation_id = events[event_id][0]
        template_id = bind.execute(sa.text(
            'INSERT INTO email_template (key, organisation_id, event_id, language, subject, body, updated_at) '
            'VALUES (:key, :org, :event, :lang, :subject, :body, :now) RETURNING id'),
            {'key': key, 'org': organisation_id, 'event': event_id, 'lang': language,
             'subject': subject, 'body': body, 'now': now}).scalar()
        bind.execute(sa.text(
            'INSERT INTO email_template_revision (email_template_id, key, organisation_id, event_id, language, '
            'subject, body, saved_at) VALUES (:id, :key, :org, :event, :lang, :subject, :body, :now)'),
            {'id': template_id, 'key': key, 'org': organisation_id, 'event': event_id, 'lang': language,
             'subject': subject, 'body': body, 'now': now})

    # --- outbox
    op.add_column('outbox_message', sa.Column('reply_to', sa.String(length=255), nullable=True))
    op.add_column('outbox_message', sa.Column('template_key', sa.String(length=50), nullable=True))
    op.add_column('outbox_message', sa.Column('template_revision_id', sa.Integer(), nullable=True))
    op.add_column('outbox_message', sa.Column('language', sa.String(length=2), nullable=True))
    op.add_column('outbox_message', sa.Column('sensitive', sa.Boolean(), nullable=False,
                                              server_default=sa.false()))
    op.add_column('outbox_message', sa.Column('body_purged_at', sa.DateTime(), nullable=True))
    op.add_column('outbox_message', sa.Column('idempotency_key', sa.String(length=255), nullable=True))

    # The old (source, channel, user) constraint guaranteed these are unique.
    op.execute("""
        UPDATE outbox_message
        SET idempotency_key = source_type || ':' || source_id || ':' || channel || ':' || user_id
        WHERE source_type = 'announcement' AND source_id IS NOT NULL AND user_id IS NOT NULL
    """)
    op.execute("""
        UPDATE outbox_message m
        SET idempotency_key = 'document:' || m.source_id
        WHERE m.source_type = 'document' AND m.source_id IS NOT NULL
          AND m.id = (SELECT min(id) FROM outbox_message f
                      WHERE f.source_type = 'document' AND f.source_id = m.source_id)
    """)
    op.execute("UPDATE outbox_message SET template_key = 'generated-document' "
               "WHERE source_type = 'document' AND channel = 'email'")

    op.drop_constraint('uq_outbox_source_channel_user', 'outbox_message', type_='unique')
    op.create_unique_constraint('uq_outbox_message_idempotency_key', 'outbox_message', ['idempotency_key'])
    op.create_index('ix_outbox_event_user_created', 'outbox_message', ['event_id', 'user_id', 'created_at'])
    op.create_index('ix_outbox_recipient', 'outbox_message', ['recipient'])


def downgrade():
    op.drop_index('ix_outbox_recipient', table_name='outbox_message')
    op.drop_index('ix_outbox_event_user_created', table_name='outbox_message')
    op.drop_constraint('uq_outbox_message_idempotency_key', 'outbox_message', type_='unique')
    # Rows queued after the upgrade may repeat a (source, channel, user); keep the
    # earliest so the old constraint can be restored.
    op.execute("""
        DELETE FROM outbox_message a USING outbox_message b
        WHERE a.source_type = b.source_type AND a.source_id = b.source_id AND a.channel = b.channel
          AND a.user_id = b.user_id AND a.id > b.id
    """)
    op.create_unique_constraint('uq_outbox_source_channel_user', 'outbox_message',
                                ['source_type', 'source_id', 'channel', 'user_id'])
    for column in ('idempotency_key', 'body_purged_at', 'sensitive', 'language', 'template_revision_id',
                   'template_key', 'reply_to'):
        op.drop_column('outbox_message', column)

    op.drop_index('uq_email_layout_organisation', table_name='email_layout')
    op.drop_index('uq_email_layout_event', table_name='email_layout')
    op.drop_table('email_layout')
    op.drop_index('ix_email_template_revision_email_template_id', table_name='email_template_revision')
    op.drop_table('email_template_revision')

    op.execute('DELETE FROM email_template')
    op.drop_index('uq_email_template_organisation', table_name='email_template')
    op.drop_index('uq_email_template_event', table_name='email_template')
    op.drop_constraint('fk_email_template_updated_by', 'email_template', type_='foreignkey')
    op.drop_constraint('fk_email_template_organisation', 'email_template', type_='foreignkey')
    op.drop_column('email_template', 'updated_at')
    op.drop_column('email_template', 'updated_by_user_id')
    op.drop_column('email_template', 'organisation_id')
    op.alter_column('email_template', 'body', new_column_name='template', type_=sa.String(),
                    existing_nullable=False)
    op.execute('INSERT INTO email_template (id, key, event_id, language, template, subject) '
               'SELECT id, key, event_id, language, template, subject FROM email_template_legacy')
    op.create_unique_constraint('uq_email_template_key_event_id', 'email_template',
                                ['key', 'event_id', 'language'])
    op.execute("SELECT setval('email_template_id_seq', (SELECT max(id) FROM email_template))")
    op.drop_table('email_template_legacy')
