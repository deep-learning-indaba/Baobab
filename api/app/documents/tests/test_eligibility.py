"""build_eligibility_context - the query layer under variant_selection's
_context objects. Exercises the real Offer/InvitedGuest/Attendance/FormResponse
tables rather than a hand-built EligibilityContext."""
from app.documents.tests.base import DocumentsTestCase
from app.documents.eligibility import build_eligibility_context, EligibilityContext
from app.forms.visibility import VisibilityEvaluator


class TestBuildEligibilityContext(DocumentsTestCase):

    def test_offer_tag_appears_in_tag_ids_and_names(self):
        tag = self.make_tag(self.event, name='Accommodation')
        self.give_offer_tag(self.event, self.user, tag)

        context = build_eligibility_context(self.user.id, self.event.id)

        self.assertIn(tag.id, context.tag_ids)
        self.assertIn('Accommodation', context.tag_names)
        self.assertIn('selected_attendee', context.tag_names)

    def test_invited_guest_tag_appears_in_tag_ids_and_names(self):
        tag = self.make_tag(self.event, name='Travel')
        self.give_guest_tag(self.event, self.user, tag)

        context = build_eligibility_context(self.user.id, self.event.id)

        self.assertIn(tag.id, context.tag_ids)
        self.assertIn('Travel', context.tag_names)
        self.assertIn('invited_guest', context.tag_names)

    def test_no_tags_for_unconnected_user(self):
        context = build_eligibility_context(self.user.id, self.event.id)
        self.assertEqual(context.tag_ids, set())

    def test_attended_true_only_when_confirmed(self):
        context_before = build_eligibility_context(self.user.id, self.event.id)
        self.assertFalse(context_before.attended)

        self.mark_attended(self.event, self.user)
        context_after = build_eligibility_context(self.user.id, self.event.id)
        self.assertTrue(context_after.attended)

    def test_submitted_form_ids_includes_only_submitted_non_withdrawn(self):
        submitted_form = self.make_form(name='Submitted')
        draft_form = self.make_form(name='Draft')
        withdrawn_form = self.make_form(name='Withdrawn')

        self.submit_response(submitted_form, self.user, {})
        self.submit_response(draft_form, self.user, {}, submitted=False)
        withdrawn_response = self.submit_response(withdrawn_form, self.user, {})
        withdrawn_response.is_withdrawn = True
        from app import db
        db.session.commit()

        context = build_eligibility_context(self.user.id, self.event.id)

        self.assertIn(submitted_form.id, context.submitted_form_ids)
        self.assertNotIn(draft_form.id, context.submitted_form_ids)
        self.assertNotIn(withdrawn_form.id, context.submitted_form_ids)


class TestAnswerComparisonLeaf(DocumentsTestCase):
    """`{"key": ..., "operator": ..., "value"/"values": ...}` - design section 7.5,
    shared by eligibility, variant selection and derived placeholder rules."""

    def _context(self, answers):
        return EligibilityContext(set(), set(), False, set(), answer_resolver=answers.get)

    def test_equals(self):
        context = self._context({'bringing_poster': 'yes'})
        expr = {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'}
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))
        self.assertFalse(VisibilityEvaluator.evaluate(
            {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'no'}, set(), context))

    def test_equals_is_case_and_whitespace_insensitive(self):
        context = self._context({'gender': ' Female '})
        expr = {'key': 'gender', 'operator': 'EQUALS', 'value': 'female'}
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))

    def test_not_equals(self):
        context = self._context({'bringing_poster': 'no'})
        expr = {'key': 'bringing_poster', 'operator': 'NOT_EQUALS', 'value': 'yes'}
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))

    def test_in(self):
        context = self._context({'hostel': 'Blue House'})
        expr = {'key': 'hostel', 'operator': 'IN', 'values': ['Red House', 'Blue House']}
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))

    def test_not_in(self):
        context = self._context({'hostel': 'Green House'})
        expr = {'key': 'hostel', 'operator': 'NOT_IN', 'values': ['Red House', 'Blue House']}
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))

    def test_is_empty_and_is_not_empty(self):
        context = self._context({'poster_title': ''})
        self.assertTrue(VisibilityEvaluator.evaluate(
            {'key': 'poster_title', 'operator': 'IS_EMPTY'}, set(), context))
        self.assertFalse(VisibilityEvaluator.evaluate(
            {'key': 'poster_title', 'operator': 'IS_NOT_EMPTY'}, set(), context))

    def test_missing_key_is_treated_as_blank(self):
        context = self._context({})
        self.assertTrue(VisibilityEvaluator.evaluate(
            {'key': 'never_answered', 'operator': 'IS_EMPTY'}, set(), context))
        self.assertFalse(VisibilityEvaluator.evaluate(
            {'key': 'never_answered', 'operator': 'EQUALS', 'value': 'yes'}, set(), context))

    def test_no_context_evaluates_false_not_raise(self):
        expr = {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'}
        self.assertFalse(VisibilityEvaluator.evaluate(expr, set(), None))

    def test_context_without_answer_resolver_evaluates_false(self):
        # A plain EligibilityContext built with no answer_resolver (or a form
        # visibility_expression, which never passes a context at all) must
        # not raise just because a rule includes this leaf.
        context = build_eligibility_context(self.user_id, self.event_id)
        expr = {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'}
        self.assertFalse(VisibilityEvaluator.evaluate(expr, set(), context))

    def test_combines_with_and(self):
        context = self._context({'bringing_poster': 'yes', 'poster_title': 'A Title'})
        expr = {
            'operator': 'AND',
            'conditions': [
                {'key': 'bringing_poster', 'operator': 'EQUALS', 'value': 'yes'},
                {'key': 'poster_title', 'operator': 'IS_NOT_EMPTY'},
            ],
        }
        self.assertTrue(VisibilityEvaluator.evaluate(expr, set(), context))
