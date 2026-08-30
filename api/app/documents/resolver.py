"""Resolves {placeholder} occurrences found in a document template to values for
one recipient.

See docs/temp/DOCUMENT_GENERATION_DESIGN.md section 5 for the full design. The
one rule worth restating here because it is easy to get backwards: a linked
form is searched for a *value*, not merely for a matching question. A form
that defines the key but leaves it unanswered for this person (a hidden
section, a skipped question, a draft never submitted) is skipped in favour of
the next linked form - see _AnswerIndex.lookup and its docstring.
"""
import re
from datetime import datetime, date

from app import db
from app.forms.models import (
    FormResponse, FormAnswer, FormQuestion, MULTI_VALUE_SEPARATOR, answer_is_blank,
)
from app.documents.models import DocumentTemplateForm, UserEventData
from app.documents.derived_placeholders import load_derived_placeholders, resolve_value as resolve_derived_value


# Matches either a literal doubled brace ({{ or }}) or a single {...} placeholder
# occurrence. Doubled braces are checked first so `{{firstname}}` in a document
# renders as the literal text "{firstname}" rather than being treated as nested.
PLACEHOLDER_RE = re.compile(r'\{\{|\}\}|\{([^{}]+)\}')

RESERVED_NAMESPACES = ('profile', 'data', 'form', 'event', 'system')

_FR_MONTHS = {
    'January': 'janvier', 'February': 'février', 'March': 'mars', 'April': 'avril',
    'May': 'mai', 'June': 'juin', 'July': 'juillet', 'August': 'août',
    'September': 'septembre', 'October': 'octobre', 'November': 'novembre',
    'December': 'décembre',
}
_FR_DAYS = {
    'Monday': 'lundi', 'Tuesday': 'mardi', 'Wednesday': 'mercredi', 'Thursday': 'jeudi',
    'Friday': 'vendredi', 'Saturday': 'samedi', 'Sunday': 'dimanche',
}


class PlaceholderError:
    NOT_RESOLVABLE = 'PLACEHOLDER_NOT_RESOLVABLE'
    VALUE_MISSING = 'PLACEHOLDER_VALUE_MISSING'

    def __init__(self, code, key, message):
        self.code = code
        self.key = key
        self.message = message

    def to_dict(self):
        return {'code': self.code, 'key': self.key, 'message': self.message}


class ResolutionResult:
    """The output of resolving every placeholder occurrence for one user.

    `values` maps the exact placeholder occurrence as found in the document
    (e.g. "date_of_birth|date:%d %B %Y") to its rendered substitution text - what
    generator.py needs for replaceAllText. `snapshot` maps the bare key to the
    resolved value and the source it came from, for GeneratedDocument audit and
    for the admin preview.
    """

    def __init__(self):
        self.values = {}
        self.snapshot = {}
        self.errors = []

    @property
    def ok(self):
        return not self.errors


def extract_placeholder_occurrences(text):
    """Every distinct `{key|filters}` occurrence in `text`, as the raw content
    inside the braces (not including the braces themselves). Doubled braces
    ({{, }}) are the literal-brace escape and are not occurrences."""
    occurrences = set()
    for match in PLACEHOLDER_RE.finditer(text or ''):
        if match.group(0) in ('{{', '}}'):
            continue
        if match.group(1):
            occurrences.add(match.group(1))
    return occurrences


def parse_placeholder(raw):
    """Split a raw occurrence ("gender", "data.hostel", "dob|date:%d %B %Y")
    into (namespace_or_None, key, [(filter_name, arg_or_None), ...])."""
    parts = raw.split('|')
    key_part = parts[0].strip()
    filters = []
    for part in parts[1:]:
        name, _, arg = part.partition(':')
        filters.append((name.strip().lower(), arg if arg != '' else None))

    namespace = None
    key = key_part
    if '.' in key_part:
        prefix, _, rest = key_part.partition('.')
        if prefix.strip().lower() in RESERVED_NAMESPACES:
            namespace = prefix.strip().lower()
            key = rest

    return namespace, key.strip().lower(), filters


def _apply_filters(value, filters, language):
    for name, arg in filters:
        if value is None:
            value = ''
        if name == 'date':
            value = _format_date(value, arg or '%d %B %Y', language)
        elif name == 'upper':
            value = value.upper()
        elif name == 'lower':
            value = value.lower()
        elif name == 'title':
            value = value.title()
        elif name == 'default':
            if value == '' or value is None:
                value = arg or ''
        # Unknown filters are ignored rather than raising: a typo'd filter
        # name should not turn a working placeholder into a hard failure at
        # generation time. It is flagged on the placeholder screen instead.
    return value


def _format_date(value, fmt, language):
    if isinstance(value, (datetime, date)):
        parsed = value
    else:
        text = str(value).strip()
        parsed = None
        for candidate_fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'):
            try:
                parsed = datetime.strptime(text, candidate_fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError:
                return value if isinstance(value, str) else str(value)

    rendered = parsed.strftime(fmt)
    if language == 'fr':
        for en, fr in _FR_MONTHS.items():
            rendered = rendered.replace(en, fr)
        for en, fr in _FR_DAYS.items():
            rendered = rendered.replace(en, fr)
    return rendered


def _humanize_answer(question, raw_value, language):
    """Turn a stored FormAnswer.value into display text: multi-value answers
    are joined with ", " instead of the storage separator, and choice answers
    show the option label rather than the stored option value."""
    values = [v.strip() for v in raw_value.split(MULTI_VALUE_SEPARATOR)] if raw_value else []
    if not values:
        return ''

    translation = question.get_translation(language) or question.get_translation('en')
    options_by_value = {}
    if translation and translation.options:
        options_by_value = {opt['value']: opt.get('label', opt['value']) for opt in translation.options}

    labelled = [options_by_value.get(v, v) for v in values]
    return ', '.join(labelled)


class _AnswerIndex:
    """Per-user index of {(form_id, key): (question, raw_value)} for every
    linked form, built with two queries regardless of how many forms are
    linked - the cost that matters when this runs once per bulk recipient.
    """

    def __init__(self, user_id, form_links):
        self.form_links = form_links
        form_ids = [link.form_id for link in form_links]

        self._latest_response_by_form = {}
        if form_ids:
            responses = (
                db.session.query(FormResponse)
                .filter(
                    FormResponse.user_id == user_id,
                    FormResponse.form_id.in_(form_ids),
                    FormResponse.is_submitted == True,   # noqa: E712
                    FormResponse.is_withdrawn == False,  # noqa: E712
                )
                .order_by(FormResponse.form_id, FormResponse.id.desc())
                .all()
            )
            for response in responses:
                # Ordered by id desc, so the first response seen per form is
                # the most recent submitted one.
                self._latest_response_by_form.setdefault(response.form_id, response)

        self._answers_by_response = {}
        response_ids = [r.id for r in self._latest_response_by_form.values()]
        if response_ids:
            rows = (
                db.session.query(FormAnswer, FormQuestion)
                .join(FormQuestion, FormAnswer.question_id == FormQuestion.id)
                .filter(
                    FormAnswer.response_id.in_(response_ids),
                    FormAnswer.is_active == True,   # noqa: E712
                    FormQuestion.is_active == True,  # noqa: E712
                    FormQuestion.key.isnot(None),
                )
                .all()
            )
            for answer, question in rows:
                key = question.key.strip().lower()
                if not key:
                    continue
                self._answers_by_response.setdefault(answer.response_id, {})[key] = (question, answer.value)

    def has_submitted_response(self, form_id):
        return form_id in self._latest_response_by_form

    def lookup(self, key):
        """The first linked form (highest `order` first) where this user has a
        non-blank answer to a question keyed `key`.

        Deliberately does NOT stop at the first form that merely *defines* the
        key. A form can define a question with this key and still have no
        answer for a given person - most commonly because the question sits in
        a section made conditionally invisible to them (e.g. a demographics
        section shown only to invited guests, hidden from applicants who
        already gave the same information on the application form). Stopping
        at "defined" rather than "answered" would bind every such placeholder
        to whichever form happens to be linked with the highest priority,
        breaking it for exactly the people that form doesn't ask.

        Returns (value, source_descriptor) or (None, None).
        """
        for link in self.form_links:
            response = self._latest_response_by_form.get(link.form_id)
            if not response:
                continue
            answer_entry = self._answers_by_response.get(response.id, {}).get(key)
            if not answer_entry:
                continue
            question, raw_value = answer_entry
            if answer_is_blank(question.type, raw_value):
                continue
            return question, raw_value, link
        return None, None, None


class PlaceholderResolver:
    """Resolves placeholder occurrences for a document template against one
    recipient at a time. Bind once per template, call resolve(user) per
    recipient - the answer index and reserved-key sets are computed once."""

    PROFILE_KEYS = (
        'firstname', 'lastname', 'fullname', 'title', 'email', 'nationality',
        'residence', 'affiliation', 'department', 'gender', 'date_of_birth',
        'primary_language', 'user_category',
    )

    EVENT_KEYS = ('name', 'start_date', 'end_date', 'key', 'organisation_name', 'organisation.name')
    SYSTEM_KEYS = ('today', 'current_year')

    def __init__(self, document_template, event, language='en'):
        self.document_template = document_template
        self.event = event
        self.language = language
        self.form_links = document_template.ordered_form_links()

        # Event-scoped, not template-scoped - see DerivedPlaceholder's
        # docstring. Loaded once here rather than per recipient.
        self._derived_placeholders = load_derived_placeholders(event.id)

        # Event-wide, not per-user: whether *some* attendee has this
        # user_event_data key is what makes a key "defined" for the purposes of
        # the setup-time PLACEHOLDER_NOT_RESOLVABLE check. A key twelve people
        # out of three hundred have (e.g. `hostel`) is a legitimate, if sparse,
        # source - the other 328 are a per-person VALUE_MISSING, not evidence
        # the placeholder is misconfigured.
        self._user_event_data_keys_in_use = {
            row.key for row in db.session.query(UserEventData.key)
            .filter_by(event_id=event.id).distinct().all()
        }

        # Every key some linked form defines, independent of any one
        # recipient - unlike _AnswerIndex (which is necessarily per-user,
        # since it also holds answers), whether a form *defines* a key only
        # depends on which forms are linked, so this is computed once here
        # rather than once per recipient in a bulk run.
        self._form_defined_keys = set()
        self._linked_form_keys = {}  # form_id -> set of keys that form defines
        form_ids = [link.form_id for link in self.form_links]
        if form_ids:
            for form_id, form_key in db.session.query(
                FormQuestion.form_id, FormQuestion.key
            ).filter(
                FormQuestion.form_id.in_(form_ids),
                FormQuestion.is_active == True,  # noqa: E712
                FormQuestion.key.isnot(None),
            ).all():
                if form_key and form_key.strip():
                    normalised = form_key.strip().lower()
                    self._form_defined_keys.add(normalised)
                    self._linked_form_keys.setdefault(form_id, set()).add(normalised)

    def _profile_value(self, user, key):
        if key == 'firstname':
            return user.firstname
        if key == 'lastname':
            return user.lastname
        if key == 'fullname':
            return user.full_name
        if key == 'title':
            return user.user_title
        if key == 'email':
            return user.email
        if key == 'nationality':
            return user.nationality_country.name if user.nationality_country else None
        if key == 'residence':
            return user.residence_country.name if user.residence_country else None
        if key == 'affiliation':
            return user.affiliation
        if key == 'department':
            return user.department
        if key == 'gender':
            return user.user_gender
        if key == 'date_of_birth':
            return user.user_dateOfBirth
        if key == 'primary_language':
            return user.user_primaryLanguage
        if key == 'user_category':
            return user.user_category.name if user.user_category else None
        return None

    def _event_value(self, key):
        if key == 'name':
            if self.event.has_specific_translation(self.language):
                return self.event.get_name(self.language)
            return self.event.get_name('en')
        if key == 'start_date':
            return self.event.start_date
        if key == 'end_date':
            return self.event.end_date
        if key == 'key':
            return self.event.key
        if key == 'organisation_name' or key == 'organisation.name':
            return self.event.organisation.name if self.event.organisation else None
        return None

    def _system_value(self, key):
        if key == 'today':
            return datetime.now()
        if key == 'current_year':
            return str(datetime.now().year)
        return None

    def _user_event_data(self, user_id, key):
        row = db.session.query(UserEventData).filter_by(
            event_id=self.event.id, user_id=user_id, key=key
        ).first()
        return row.value if row else None

    def resolve(self, user, variant=None, answer_index=None):
        """Resolve placeholder occurrences against `user`.

        With `variant` given, resolves only the placeholders that variant's
        file actually contains - what generation needs. Without it, resolves
        the union across every active variant - what the admin placeholder
        screen (section 9.5) needs, since coverage there is reported per
        template, not per variant.

        `answer_index`, if the caller already built one (generator.py builds
        one to evaluate eligibility before resolving placeholders), is reused
        rather than re-querying - a bulk run must not pay for the same two
        queries twice per recipient.

        Returns a ResolutionResult. Errors do not raise: both a missing
        definition and a missing value are collected so the caller can report
        every problem in one pass rather than one round-trip per placeholder.
        """
        result = ResolutionResult()
        answer_index = answer_index or _AnswerIndex(user.id, self.form_links)

        occurrences = set()
        variants = [variant] if variant is not None else self.document_template.active_variants()
        for v in variants:
            for occurrence in (v.detected_placeholders or []):
                occurrences.add(occurrence)

        for raw in occurrences:
            namespace, key, filters = parse_placeholder(raw)
            value, source, skipped = self._resolve_key(user, answer_index, namespace, key, result=result)

            if source is None:
                result.errors.append(PlaceholderError(
                    PlaceholderError.NOT_RESOLVABLE, key,
                    f'No derived placeholder, linked form, user data, profile field, '
                    f'event field or system value defines "{key}".'
                ))
                continue

            if value is None or value == '':
                has_default = any(name == 'default' for name, _arg in filters)
                if has_default:
                    # |default:<text> supplies its own fallback and suppresses
                    # the missing-value error outright - it does not merely
                    # behave like allow_blank_values, since it's a per-placeholder
                    # opt-in rather than a template-wide "any blank is fine".
                    rendered = _apply_filters('', filters, self.language)
                    result.values[raw] = rendered
                    result.snapshot[key] = {'value': rendered, 'source': source, 'skipped': skipped}
                elif self.document_template.allow_blank_values:
                    result.values[raw] = ''
                    result.snapshot[key] = {'value': '', 'source': source, 'skipped': skipped}
                else:
                    # `skipped` already names every source that was tried,
                    # including the one `_resolve_key` ultimately reported as
                    # the "natural home" for the key - don't list it twice.
                    tried = ', '.join(skipped) if skipped else source
                    result.errors.append(PlaceholderError(
                        PlaceholderError.VALUE_MISSING, key,
                        f'No value found for "{key}" for this person (checked: {tried}).'
                    ))
                continue

            rendered = value if isinstance(value, str) else str(value)
            rendered = _apply_filters(rendered, filters, self.language)
            result.values[raw] = rendered
            result.snapshot[key] = {'value': rendered, 'source': source, 'skipped': skipped}

        return result

    def resolve_text(self, user, text):
        """Render arbitrary Baobab-owned text (a filename pattern, not a
        document body) by substituting every {key|filters} occurrence found in
        it for `user`.

        Unlike resolve(), a key with no value renders as an empty string
        rather than raising: a blank segment in a generated filename is a
        cosmetic annoyance, not a reason to refuse a document that otherwise
        generated successfully.
        """
        if not text:
            return text
        answer_index = _AnswerIndex(user.id, self.form_links)
        rendered_text = text
        for raw in extract_placeholder_occurrences(text):
            namespace, key, filters = parse_placeholder(raw)
            value, _source, _skipped = self._resolve_key(user, answer_index, namespace, key)
            rendered_value = '' if value in (None, '') else _apply_filters(str(value), filters, self.language)
            rendered_text = rendered_text.replace('{' + raw + '}', rendered_value)
        return rendered_text.replace('{{', '{').replace('}}', '}')

    def answer_value(self, user, answer_index, key):
        """The raw resolved value for `key` (no filters applied), skipping
        derived placeholders.

        Backs the `key`/`operator` leaf in eligibility, variant-selection and
        derived-placeholder-rule expressions (app/forms/visibility.py). Never
        derived-placeholder-aware: design section 5.7.5 scopes recursion to
        rule *text*, not conditions, so a condition can't participate in a
        cycle no matter how it's written - see derived_placeholders.resolve_value.
        """
        return self._resolve_key(user, answer_index, None, key, include_derived=False)[0]

    def _render_fragment(self, user, answer_index, text, chain, result):
        """Render {key|filters} interpolation inside one derived-placeholder
        rule's winning text. Recurses back into _resolve_key for every
        occurrence found, so nested derived placeholders and every ordinary
        source resolve exactly as they would inside the document itself.

        `result`, when given (only from resolve(), never resolve_text() or a
        condition lookup), collects NOT_RESOLVABLE/VALUE_MISSING errors for
        keys referenced here, so a misspelled key inside a rule surfaces on
        the placeholder screen instead of appearing as a stray literal in the
        PDF. Without it, a blank simply renders empty - the same "cosmetic,
        not an error" behaviour resolve_text() already has for filenames.
        """
        if not text:
            return text
        rendered_text = text
        for raw in extract_placeholder_occurrences(text):
            namespace, key, filters = parse_placeholder(raw)
            value, source, skipped = self._resolve_key(
                user, answer_index, namespace, key, chain=chain, result=result)

            if source is None:
                if result is not None:
                    result.errors.append(PlaceholderError(
                        PlaceholderError.NOT_RESOLVABLE, key,
                        f'No source defines "{key}", referenced inside a derived '
                        f'placeholder rule.'
                    ))
                rendered_value = ''
            elif value is None or value == '':
                has_default = any(name == 'default' for name, _arg in filters)
                if has_default:
                    rendered_value = _apply_filters('', filters, self.language)
                elif result is None or self.document_template.allow_blank_values:
                    rendered_value = ''
                else:
                    tried = ', '.join(skipped) if skipped else source
                    result.errors.append(PlaceholderError(
                        PlaceholderError.VALUE_MISSING, key,
                        f'No value found for "{key}" for this person (checked: {tried}), '
                        f'referenced inside a derived placeholder rule.'
                    ))
                    rendered_value = ''
            else:
                rendered_value = _apply_filters(
                    value if isinstance(value, str) else str(value), filters, self.language)

            if result is not None and source is not None:
                result.snapshot.setdefault(key, {'value': rendered_value, 'source': source, 'skipped': skipped})

            rendered_text = rendered_text.replace('{' + raw + '}', rendered_value)
        return rendered_text.replace('{{', '{').replace('}}', '}')

    def describe_placeholders(self):
        """Every distinct placeholder occurrence across the template's active
        variants, with whether it resolves and (for the form/None namespaces)
        the ordered chain of linked forms that would be tried.

        Independent of any one recipient - this is the setup-time view the
        admin placeholder screen (design section 9.5) is built from, not a
        per-person resolution. Per-person coverage counts are computed
        separately by the caller, since they require iterating recipients.
        """
        occurrences = set()
        for variant in self.document_template.active_variants():
            occurrences |= set(variant.detected_placeholders or [])

        # A derived placeholder's rule text may reference other keys; expand
        # those into the table too; design section 9.5 - a rule interpolating
        # a misspelled {poster_titel} should show up here rather than as a
        # stray literal in someone's letter.
        expanded = set(occurrences)
        seen_derived = set()
        frontier = [parse_placeholder(raw)[1] for raw in occurrences]
        while frontier:
            key = frontier.pop()
            if key in seen_derived:
                continue
            seen_derived.add(key)
            derived = self._derived_placeholders.get(key)
            if derived is None:
                continue
            for rule in derived.rules:
                for translation in rule.translations:
                    for raw in extract_placeholder_occurrences(translation.text):
                        if raw not in expanded:
                            expanded.add(raw)
                            frontier.append(parse_placeholder(raw)[1])

        descriptions = []
        for raw in sorted(expanded):
            namespace, key, _filters = parse_placeholder(raw)
            is_derived = namespace is None and key in self._derived_placeholders
            if is_derived:
                rule_count = len(self._derived_placeholders[key].rules)
                chain = [f'derived — {rule_count} rule{"s" if rule_count != 1 else ""}']
            elif namespace in (None, 'form'):
                chain = [self._form_source_label(link) for link in self.form_links
                         if key in self._linked_form_keys.get(link.form_id, set())]
            else:
                chain = []
            descriptions.append({
                'raw': raw,
                'namespace': namespace,
                'key': key,
                'defined': self._is_defined_anywhere(key),
                'is_derived': is_derived,
                'chain': chain,
            })
        return descriptions

    def _form_source_label(self, link):
        translation = link.form.get_translation(self.language) or link.form.get_translation('en')
        return f'linked form "{translation.name if translation else link.form_id}"'

    def _try_form(self, user, answer_index, key):
        question, raw_value, link = answer_index.lookup(key)
        if question is None:
            return None, None
        return _humanize_answer(question, raw_value, self.language), self._form_source_label(link)

    def _try_data(self, user, key):
        value = self._user_event_data(user.id, key)
        return (value, 'user data') if value else (None, None)

    def _try_profile(self, user, key):
        if key not in self.PROFILE_KEYS:
            return None, None
        value = self._profile_value(user, key)
        return (value, 'user profile') if value not in (None, '') else (None, None)

    def _try_event(self, key):
        value = self._event_value(key)
        return (value, 'event') if value not in (None, '') else (None, None)

    def _try_system(self, key):
        value = self._system_value(key)
        return (value, 'system') if value not in (None, '') else (None, None)

    def _is_defined_anywhere(self, key):
        """Whether *some* source could, for *some* person, supply this key.

        Distinguishes a setup error (nothing defines the key at all) from a
        data error (defined, but empty for this particular person) - see
        PlaceholderError.NOT_RESOLVABLE vs VALUE_MISSING. Independent of any
        one recipient, so it can also drive the admin placeholder screen
        (section 9.5), which has no single person in mind.
        """
        return (key in self._derived_placeholders
                or key in self._form_defined_keys
                or key in self.PROFILE_KEYS
                or key in self.EVENT_KEYS
                or key in self.SYSTEM_KEYS
                or key in self._user_event_data_keys_in_use)

    def _resolve_key(self, user, answer_index, namespace, key,
                      include_derived=True, chain=(), result=None):
        """Returns (value, source_label_or_None, skipped_source_labels).

        `source_label` is None only when nothing anywhere defines `key` - the
        caller turns that into PLACEHOLDER_NOT_RESOLVABLE. Any other case
        (including a value of None/'' with a real source label) is this
        person's data being incomplete, not a configuration problem.

        `include_derived`/`chain`/`result` only matter for the unnamed
        precedence walk below - an explicit namespace already bypasses
        derived placeholders entirely, same as every other source.
        """
        # An explicit namespace bypasses the precedence walk entirely and
        # answers only from that one source - see the {profile.x}/{data.x}
        # override in section 5.1 of the design.
        if namespace == 'form':
            value, source = self._try_form(user, answer_index, key)
            if source:
                return value, source, []
            return None, ('linked forms' if key in self._form_defined_keys else None), []

        if namespace == 'data':
            # user_event_data is an intentionally sparse, admin-curated store:
            # an explicit {data.x} is always "defined" by virtue of being asked
            # for by name, even before any row exists for anyone.
            value, source = self._try_data(user, key)
            return value, (source or 'user data'), []

        if namespace == 'profile':
            if key not in self.PROFILE_KEYS:
                return None, None, []
            value, source = self._try_profile(user, key)
            return value, (source or 'user profile'), []

        if namespace == 'event':
            if key not in self.EVENT_KEYS:
                return None, None, []
            value, source = self._try_event(key)
            return value, (source or 'event'), []

        if namespace == 'system':
            if key not in self.SYSTEM_KEYS:
                return None, None, []
            value, source = self._try_system(key)
            return value, (source or 'system'), []

        # No explicit namespace: derived placeholders are step 0 of the
        # precedence walk (design section 5.2) - checked first because
        # defining one is a deliberate act. A derived placeholder that
        # doesn't fire for this person (no condition matched and no
        # "otherwise") isn't a value, so the walk continues exactly as if
        # that source had come back empty - same fallthrough as every other
        # source below.
        if include_derived and key in self._derived_placeholders:
            value, matched = resolve_derived_value(
                key, self._derived_placeholders, user, self.event, self.language,
                condition_answer_fn=lambda k: self.answer_value(user, answer_index, k),
                render_text_fn=lambda text, nested_chain: self._render_fragment(
                    user, answer_index, text, nested_chain, result),
                chain=chain,
            )
            if matched:
                return value, 'derived placeholder rules', []

        # No explicit namespace: walk the full precedence order, remembering
        # each source tried so a VALUE_MISSING error can name all of them.
        skipped = []
        for try_fn, label in (
            (lambda: self._try_form(user, answer_index, key), 'linked forms'),
            (lambda: self._try_data(user, key), 'user data'),
            (lambda: self._try_profile(user, key), 'user profile'),
            (lambda: self._try_event(key), 'event'),
            (lambda: self._try_system(key), 'system'),
        ):
            value, source = try_fn()
            if source:
                return value, source, skipped
            skipped.append(label)

        if self._is_defined_anywhere(key):
            # Defined somewhere, but every source came back empty for this
            # person - report it against whichever source is the "natural"
            # home for the key, so the error reads sensibly.
            if key in self._derived_placeholders:
                return None, 'derived placeholder rules', skipped
            if key in self._form_defined_keys:
                return None, 'linked forms', skipped
            if key in self.PROFILE_KEYS:
                return None, 'user profile', skipped
            return None, 'user data', skipped

        return None, None, skipped


def evaluate_form_requirements(document_template, user, language='en'):
    """Which linked forms this person hasn't submitted, split into the two
    forms that requirement takes (section 5.2.4 of the design):

    - blockers: `requirement='required'` forms with no submitted response.
      Generation must be refused while any of these are non-empty.
    - prompts: `requirement='recommended'` forms with no submitted response.
      Never blocks anything - purely informational, shown as a nudge.

    This is checked once, independently of which placeholders the template
    uses: it means "has this person submitted the form", never "did they
    answer this particular question on it" - that distinction is what lets a
    conditionally-hidden question (the applicant/guest case in
    PlaceholderResolver) coexist with a hard requirement on the form itself.
    """
    blockers = []
    prompts = []

    if not document_template.form_links:
        return blockers, prompts

    form_ids = [link.form_id for link in document_template.form_links
                if link.requirement != DocumentTemplateForm.REQUIREMENT_NONE]
    submitted_form_ids = set()
    if form_ids:
        submitted_form_ids = {
            row.form_id for row in db.session.query(FormResponse.form_id).filter(
                FormResponse.user_id == user.id,
                FormResponse.form_id.in_(form_ids),
                FormResponse.is_submitted == True,   # noqa: E712
                FormResponse.is_withdrawn == False,  # noqa: E712
            ).all()
        }

    for link in document_template.form_links:
        if link.requirement == DocumentTemplateForm.REQUIREMENT_NONE:
            continue
        if link.form_id in submitted_form_ids:
            continue

        translation = link.get_translation(language) or link.get_translation('en')
        form_translation = link.form.get_translation(language) or link.form.get_translation('en')
        entry = {
            'form_id': link.form_id,
            'form_name': form_translation.name if form_translation else None,
            'message': translation.prompt_message if translation else None,
        }
        if link.requirement == DocumentTemplateForm.REQUIREMENT_REQUIRED:
            blockers.append(entry)
        else:
            prompts.append(entry)

    return blockers, prompts
