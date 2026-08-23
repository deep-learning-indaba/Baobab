"""Variant selection - design section 7.3. Covers the four travel x
accommodation combinations from section 7.4 explicitly, since that's the
concrete case the admin builder must be able to express."""
from app.documents.tests.base import DocumentsTestCase
from app.documents.eligibility import EligibilityContext
from app.documents.variant_selection import select_variant, is_eligible, NoMatchingVariant


def _context(tag_ids=None, tag_names=None, attended=False, submitted_form_ids=None):
    return EligibilityContext(
        tag_names=tag_names or set(),
        tag_ids=tag_ids or set(),
        attended=attended,
        submitted_form_ids=submitted_form_ids or set(),
    )


class TestVariantPriorityAndCatchAll(DocumentsTestCase):

    def test_catch_all_variant_matches_when_nothing_else_does(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'firstname'}, name='catch-all',
                           selection_expression=None, priority=0)

        selected = select_variant(document_template, _context())

        self.assertEqual(selected.name, 'catch-all')

    def test_higher_priority_wins_when_both_match(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'a'}, name='low', priority=0, selection_expression=None)
        self.make_variant(document_template, {'a'}, name='high', priority=10,
                           selection_expression={'tag_id': 1})

        selected = select_variant(document_template, _context(tag_ids={1}))

        self.assertEqual(selected.name, 'high')

    def test_no_matching_variant_raises(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'a'}, name='specific',
                           selection_expression={'tag_id': 1})

        with self.assertRaises(NoMatchingVariant):
            select_variant(document_template, _context(tag_ids=set()))

    def test_inactive_variant_is_never_selected(self):
        document_template = self.make_document_template()
        v = self.make_variant(document_template, {'a'}, name='inactive', selection_expression=None)
        v.is_active = False
        from app import db
        db.session.commit()

        with self.assertRaises(NoMatchingVariant):
            select_variant(document_template, _context())


class TestVariantLanguage(DocumentsTestCase):

    def test_language_pinned_variant_preferred_over_language_agnostic(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'a'}, name='agnostic', language=None, selection_expression=None)
        self.make_variant(document_template, {'a'}, name='french', language='fr', selection_expression=None)

        selected = select_variant(document_template, _context(), language='fr')

        self.assertEqual(selected.name, 'french')

    def test_falls_back_to_language_agnostic_when_no_pinned_variant_matches(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'a'}, name='agnostic', language=None, selection_expression=None)
        self.make_variant(document_template, {'a'}, name='english', language='en', selection_expression=None)

        selected = select_variant(document_template, _context(), language='fr')

        self.assertEqual(selected.name, 'agnostic')

    def test_pinned_variant_in_different_language_is_never_picked_over_agnostic(self):
        document_template = self.make_document_template()
        self.make_variant(document_template, {'a'}, name='english_only', language='en', selection_expression=None)

        with self.assertRaises(NoMatchingVariant):
            # No agnostic variant and no 'de' variant - must not silently fall
            # back to the English-pinned one.
            select_variant(document_template, _context(), language='de')


class TestTravelAccommodationCombinations(DocumentsTestCase):
    """The four combinations from design section 7.4, reproduced exactly."""

    def setUp(self):
        super().setUp()
        self.travel_tag_id = 1
        self.accom_tag_id = 2
        self.document_template = self.make_document_template(key='invitation-letter')

        both_expr = {'operator': 'AND', 'conditions': [
            {'tag_id': self.travel_tag_id}, {'tag_id': self.accom_tag_id}]}
        travel_only_expr = {'operator': 'AND', 'conditions': [
            {'tag_id': self.travel_tag_id},
            {'operator': 'NOT', 'conditions': [{'tag_id': self.accom_tag_id}]}]}
        accom_only_expr = {'operator': 'AND', 'conditions': [
            {'tag_id': self.accom_tag_id},
            {'operator': 'NOT', 'conditions': [{'tag_id': self.travel_tag_id}]}]}

        self.make_variant(self.document_template, {'a'}, name='both', priority=30,
                           selection_expression=both_expr)
        self.make_variant(self.document_template, {'a'}, name='travel_only', priority=20,
                           selection_expression=travel_only_expr)
        self.make_variant(self.document_template, {'a'}, name='accom_only', priority=10,
                           selection_expression=accom_only_expr)
        self.make_variant(self.document_template, {'a'}, name='neither', priority=0,
                           selection_expression=None)

    def test_both_travel_and_accommodation(self):
        selected = select_variant(self.document_template,
                                   _context(tag_ids={self.travel_tag_id, self.accom_tag_id}))
        self.assertEqual(selected.name, 'both')

    def test_travel_only(self):
        selected = select_variant(self.document_template, _context(tag_ids={self.travel_tag_id}))
        self.assertEqual(selected.name, 'travel_only')

    def test_accommodation_only(self):
        selected = select_variant(self.document_template, _context(tag_ids={self.accom_tag_id}))
        self.assertEqual(selected.name, 'accom_only')

    def test_neither_travel_nor_accommodation(self):
        """The case the legacy three-boolean InvitationTemplate scheme cannot
        express at all - an attendee with no award matches no combination of
        send_for_travel_award_only / send_for_accommodation_award_only /
        send_for_both_travel_accommodation."""
        selected = select_variant(self.document_template, _context(tag_ids=set()))
        self.assertEqual(selected.name, 'neither')


class TestEligibility(DocumentsTestCase):

    def test_null_expression_matches_everyone(self):
        document_template = self.make_document_template(eligibility_expression=None)
        self.assertTrue(is_eligible(document_template, _context()))

    def test_tag_id_expression(self):
        document_template = self.make_document_template(eligibility_expression={'tag_id': 5})
        self.assertTrue(is_eligible(document_template, _context(tag_ids={5})))
        self.assertFalse(is_eligible(document_template, _context(tag_ids={6})))

    def test_attended_expression(self):
        document_template = self.make_document_template(eligibility_expression={'attended': True})
        self.assertTrue(is_eligible(document_template, _context(attended=True)))
        self.assertFalse(is_eligible(document_template, _context(attended=False)))

    def test_form_submitted_expression(self):
        document_template = self.make_document_template(eligibility_expression={'form_submitted': 7})
        self.assertTrue(is_eligible(document_template, _context(submitted_form_ids={7})))
        self.assertFalse(is_eligible(document_template, _context(submitted_form_ids={8})))

    def test_and_or_not_combination(self):
        expr = {
            'operator': 'OR',
            'conditions': [
                {'tag_id': 1},
                {'operator': 'AND', 'conditions': [
                    {'attended': True},
                    {'operator': 'NOT', 'conditions': [{'tag_id': 2}]},
                ]},
            ],
        }
        document_template = self.make_document_template(eligibility_expression=expr)
        self.assertTrue(is_eligible(document_template, _context(tag_ids={1})))
        self.assertTrue(is_eligible(document_template, _context(attended=True, tag_ids=set())))
        self.assertFalse(is_eligible(document_template, _context(attended=True, tag_ids={2})))
        self.assertFalse(is_eligible(document_template, _context(attended=False, tag_ids=set())))
