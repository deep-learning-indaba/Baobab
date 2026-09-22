from app.documents.tests.base import DocumentsTestCase
from app.documents.resolver import PlaceholderResolver
from app.documents.derived_placeholders import find_cycle


class TestDerivedPlaceholderResolution(DocumentsTestCase):
    """The poster-sentence example from design section 5.7.3."""

    def setUp(self):
        super().setUp()
        self.form = self.make_form(name='Application Form')
        self.poster_q = self.make_question(self.form, 'bringing_poster')
        self.title_q = self.make_question(self.form, 'poster_title')

        self.document_template = self.make_document_template()
        self.link_form(self.document_template, self.form, order=10)
        self.make_variant(self.document_template, placeholders={'poster_sentence'})

        self.derived = self.make_derived_placeholder(key='poster_sentence')
        self.add_derived_rule(
            self.derived, order=1,
            condition_expression={
                'operator': 'AND',
                'conditions': [
                    {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'},
                    {'key': 'poster_title', 'operator': 'IS_NOT_EMPTY'},
                ],
            },
            texts={'en': '{firstname} will be presenting a poster titled "{poster_title}".'},
        )
        self.add_derived_rule(
            self.derived, order=2,
            condition_expression={'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'},
            texts={'en': '{firstname} will be presenting a poster.'},
        )
        self.add_derived_rule(self.derived, order=3, condition_expression=None, texts={'en': ''})

    def test_first_matching_rule_wins_with_interpolation(self):
        self.submit_response(self.form, self.user, {
            self.poster_q: 'yes', self.title_q: 'Low-resource ASR for Wolof',
        })
        resolver = PlaceholderResolver(self.document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(
            result.values['poster_sentence'],
            f'{self.user_firstname} will be presenting a poster titled "Low-resource ASR for Wolof".',
        )
        self.assertEqual(result.snapshot['poster_sentence']['source'], 'derived placeholder rules')

    def test_second_rule_fires_when_title_missing(self):
        self.submit_response(self.form, self.user, {self.poster_q: 'yes'})
        resolver = PlaceholderResolver(self.document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.values['poster_sentence'], f'{self.user_firstname} will be presenting a poster.')

    def test_otherwise_rule_yields_explicit_empty_text_not_an_error(self):
        self.submit_response(self.form, self.user, {self.poster_q: 'no'})
        resolver = PlaceholderResolver(self.document_template, self.event)

        result = resolver.resolve(self.user)

        # allow_blank_values defaults False, but the otherwise rule is an
        # explicit answer rather than a gap - allow_blank_values must be on
        # for the template to actually accept the empty substitution, same
        # as any other source's blank value.
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, 'PLACEHOLDER_VALUE_MISSING')

    def test_otherwise_rule_empty_text_accepted_when_blanks_allowed(self):
        self.document_template.allow_blank_values = True
        self.submit_response(self.form, self.user, {self.poster_q: 'no'})
        resolver = PlaceholderResolver(self.document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['poster_sentence'], '')

    def test_no_otherwise_falls_through_to_next_source_when_no_rule_matches(self):
        """A derived placeholder with no catch-all rule and no matching
        condition isn't a value - resolution keeps walking down the
        precedence order exactly as if this source had come back empty."""
        derived = self.make_derived_placeholder(key='no_catch_all')
        self.add_derived_rule(
            derived, order=1,
            condition_expression={'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'},
            texts={'en': 'Presenting.'},
        )
        self.set_user_data(self.event, self.user, 'no_catch_all', 'fallback value')
        document_template = self.make_document_template(key='other-template')
        self.link_form(document_template, self.form, order=10)
        self.make_variant(document_template, placeholders={'no_catch_all'})
        self.submit_response(self.form, self.user, {self.poster_q: 'no'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.values['no_catch_all'], 'fallback value')
        self.assertEqual(result.snapshot['no_catch_all']['source'], 'user data')


class TestDerivedPlaceholderNesting(DocumentsTestCase):

    def test_rule_text_may_reference_another_derived_placeholder(self):
        greeting = self.make_derived_placeholder(key='greeting')
        self.add_derived_rule(greeting, order=1, condition_expression=None, texts={'en': 'Dear {firstname}'})

        letter = self.make_derived_placeholder(key='letter_opening')
        self.add_derived_rule(letter, order=1, condition_expression=None,
                               texts={'en': '{greeting}, welcome to {event.name}.'})

        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'letter_opening'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        self.assertIn(f'Dear {self.user_firstname}, welcome to', result.values['letter_opening'])

    def test_misspelled_key_inside_rule_text_is_reported_as_an_error(self):
        derived = self.make_derived_placeholder(key='poster_sentence')
        self.add_derived_rule(derived, order=1, condition_expression=None,
                               texts={'en': 'Title: {poster_titel}'})

        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'poster_sentence'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, 'PLACEHOLDER_NOT_RESOLVABLE')
        self.assertEqual(result.errors[0].key, 'poster_titel')

    def test_runtime_cycle_guard_does_not_raise(self):
        """Setup-time validation (find_cycle) is the primary defence; this
        checks the resolver's own circuit breaker in case a cycle slips
        through some other path."""
        a = self.make_derived_placeholder(key='a')
        self.add_derived_rule(a, order=1, condition_expression=None, texts={'en': 'A refers to {b}'})
        b = self.make_derived_placeholder(key='b')
        self.add_derived_rule(b, order=1, condition_expression=None, texts={'en': 'B refers to {a}'})

        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'a'})
        resolver = PlaceholderResolver(document_template, self.event)

        result = resolver.resolve(self.user)  # must not raise (RecursionError)

        self.assertTrue(result.values['a'])


class TestFindCycle(DocumentsTestCase):

    def test_no_cycle_among_independent_placeholders(self):
        a = self.make_derived_placeholder(key='a')
        self.add_derived_rule(a, order=1, condition_expression=None, texts={'en': 'plain text'})
        b = self.make_derived_placeholder(key='b')
        self.add_derived_rule(b, order=1, condition_expression=None, texts={'en': 'refers to {a}'})

        self.assertIsNone(find_cycle(self.event_id))

    def test_direct_cycle_detected(self):
        a = self.make_derived_placeholder(key='a')
        self.add_derived_rule(a, order=1, condition_expression=None, texts={'en': 'refers to {b}'})
        b = self.make_derived_placeholder(key='b')
        self.add_derived_rule(b, order=1, condition_expression=None, texts={'en': 'refers to {a}'})

        cycle = find_cycle(self.event_id)

        self.assertIsNotNone(cycle)
        self.assertIn('a', cycle)
        self.assertIn('b', cycle)

    def test_self_reference_detected(self):
        a = self.make_derived_placeholder(key='a')
        self.add_derived_rule(a, order=1, condition_expression=None, texts={'en': 'refers to {a}'})

        cycle = find_cycle(self.event_id)

        self.assertEqual(cycle, ['a', 'a'])

    def test_pending_edit_checked_before_save(self):
        """The admin UI validates a not-yet-committed edit by passing the
        proposed texts for the key being saved."""
        a = self.make_derived_placeholder(key='a')
        self.add_derived_rule(a, order=1, condition_expression=None, texts={'en': 'plain text'})

        cycle = find_cycle(self.event_id, changed_key='a', changed_rule_texts=['refers to {a}'])

        self.assertEqual(cycle, ['a', 'a'])
