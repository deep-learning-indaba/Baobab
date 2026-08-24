from app import db
from app.documents.tests.base import DocumentsTestCase
from app.documents.resolver import PlaceholderResolver, extract_placeholder_occurrences, parse_placeholder


class TestExtractPlaceholderOccurrences(DocumentsTestCase):

    def test_simple_placeholder(self):
        self.assertEqual(extract_placeholder_occurrences('Dear {firstname},'), {'firstname'})

    def test_multiple_distinct_placeholders(self):
        self.assertEqual(
            extract_placeholder_occurrences('{firstname} {lastname} {firstname}'),
            {'firstname', 'lastname'},
        )

    def test_doubled_braces_are_a_literal_escape_not_an_occurrence(self):
        self.assertEqual(extract_placeholder_occurrences('{{not a placeholder}}'), set())

    def test_filters_are_part_of_the_occurrence(self):
        occurrences = extract_placeholder_occurrences('{date_of_birth|date:%d %B %Y}')
        self.assertEqual(occurrences, {'date_of_birth|date:%d %B %Y'})

    def test_no_placeholders(self):
        self.assertEqual(extract_placeholder_occurrences('Plain text.'), set())


class TestParsePlaceholder(DocumentsTestCase):

    def test_plain_key(self):
        self.assertEqual(parse_placeholder('firstname'), (None, 'firstname', []))

    def test_namespaced_key(self):
        self.assertEqual(parse_placeholder('data.hostel'), ('data', 'hostel', []))

    def test_key_with_filter(self):
        namespace, key, filters = parse_placeholder('date_of_birth|date:%d %B %Y')
        self.assertIsNone(namespace)
        self.assertEqual(key, 'date_of_birth')
        self.assertEqual(filters, [('date', '%d %B %Y')])

    def test_key_is_case_insensitive(self):
        self.assertEqual(parse_placeholder('FirstName'), (None, 'firstname', []))

    def test_chained_filters(self):
        _namespace, _key, filters = parse_placeholder('lastname|upper|default:Unknown')
        self.assertEqual(filters, [('upper', None), ('default', 'Unknown')])


class TestResolverNamespaces(DocumentsTestCase):

    def test_profile_key_resolves(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'firstname'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['firstname'], self.user.firstname)

    def test_explicit_profile_namespace_bypasses_precedence(self):
        form = self.make_form()
        question = self.make_question(form, 'firstname')  # same key as the profile field
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'profile.firstname'})
        self.link_form(document_template, form, order=10)
        self.submit_response(form, self.user, {question: 'FormAnswerName'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        # Without the explicit namespace, the form (as the higher-precedence
        # source) would win. {profile.firstname} skips straight past it.
        self.assertEqual(result.values['profile.firstname'], self.user.firstname)

    def test_explicit_data_namespace_is_always_a_valid_source_even_when_unset(self):
        document_template = self.make_document_template(allow_blank_values=True)
        self.make_variant(document_template, placeholders={'data.hostel'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        # user_event_data is treated as inherently sparse - an explicit {data.x}
        # is never a setup error, only ever a per-person blank.
        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['data.hostel'], '')

    def test_data_namespace_resolves_when_set(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'data.hostel'})
        self.set_user_data(self.event, self.user, 'hostel', 'Bantry Bay Lodge')

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['data.hostel'], 'Bantry Bay Lodge')

    def test_event_namespace(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'event.key'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.values['event.key'], self.event.key)

    def test_system_current_year(self):
        from datetime import datetime
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'current_year'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.values['current_year'], str(datetime.now().year))

    def test_unknown_key_is_not_resolvable(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'made_up_key'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, 'PLACEHOLDER_NOT_RESOLVABLE')

    def test_unknown_explicit_profile_field_is_not_resolvable(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'profile.made_up'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors[0].code, 'PLACEHOLDER_NOT_RESOLVABLE')


class TestResolverFilters(DocumentsTestCase):

    def test_date_filter_formats_iso_date(self):
        form = self.make_form()
        question = self.make_question(form, 'arrival_date', question_type='date')
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'arrival_date|date:%d %B %Y'})
        self.link_form(document_template, form, order=10)
        self.submit_response(form, self.user, {question: '2026-09-14'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['arrival_date|date:%d %B %Y'], '14 September 2026')

    def test_date_filter_french_month_name(self):
        form = self.make_form()
        question = self.make_question(form, 'arrival_date', question_type='date')
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'arrival_date|date:%d %B %Y'})
        self.link_form(document_template, form, order=10)
        self.submit_response(form, self.user, {question: '2026-09-14'})

        resolver = PlaceholderResolver(document_template, self.event, language='fr')
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['arrival_date|date:%d %B %Y'], '14 septembre 2026')

    def test_upper_filter(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'lastname|upper'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.values['lastname|upper'], self.user.lastname.upper())

    def test_default_filter_suppresses_missing_value_error(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'data.hostel|default:Not yet allocated'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['data.hostel|default:Not yet allocated'], 'Not yet allocated')


class TestResolverAnswerFormatting(DocumentsTestCase):

    def test_multi_value_answer_joined_with_comma(self):
        from app.forms.models import MULTI_VALUE_SEPARATOR
        form = self.make_form()
        question = self.make_question(form, 'dietary', question_type='checkboxes')
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'dietary'})
        self.link_form(document_template, form, order=10)
        stored_value = MULTI_VALUE_SEPARATOR.join(['vegetarian', 'halal'])
        self.submit_response(form, self.user, {question: stored_value})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['dietary'], 'vegetarian, halal')

    def test_option_value_substituted_with_label(self):
        form = self.make_form()
        question = self.make_question(
            form, 'category', question_type='dropdown',
            options=[{'value': 'opt_1', 'label': 'Postdoctoral researcher'}],
        )
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'category'})
        self.link_form(document_template, form, order=10)
        self.submit_response(form, self.user, {question: 'opt_1'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['category'], 'Postdoctoral researcher')


class TestResolverAllowBlankValues(DocumentsTestCase):

    def test_blank_value_is_hard_error_by_default(self):
        document_template = self.make_document_template(allow_blank_values=False)
        self.make_variant(document_template, placeholders={'data.hostel'})
        self.set_user_data(self.event, self.user, 'hostel', '')

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, 'PLACEHOLDER_VALUE_MISSING')

    def test_blank_value_allowed_when_flag_set(self):
        document_template = self.make_document_template(allow_blank_values=True)
        self.make_variant(document_template, placeholders={'data.hostel'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['data.hostel'], '')


class TestResolveText(DocumentsTestCase):

    def test_resolves_filename_pattern(self):
        document_template = self.make_document_template(filename_pattern='{lastname}_{firstname}.pdf')
        resolver = PlaceholderResolver(document_template, self.event)

        rendered = resolver.resolve_text(self.user, document_template.filename_pattern)

        self.assertEqual(rendered, f'{self.user.lastname}_{self.user.firstname}.pdf')

    def test_missing_value_renders_empty_rather_than_raising(self):
        document_template = self.make_document_template(filename_pattern='{data.hostel}_{firstname}.pdf')
        resolver = PlaceholderResolver(document_template, self.event)

        rendered = resolver.resolve_text(self.user, document_template.filename_pattern)

        self.assertEqual(rendered, f'_{self.user.firstname}.pdf')
