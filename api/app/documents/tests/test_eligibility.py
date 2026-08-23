"""build_eligibility_context - the query layer under variant_selection's
_context objects. Exercises the real Offer/InvitedGuest/Attendance/FormResponse
tables rather than a hand-built EligibilityContext."""
from app.documents.tests.base import DocumentsTestCase
from app.documents.eligibility import build_eligibility_context


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
