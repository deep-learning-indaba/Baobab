"""The core rule this whole design turns on (see design section 5.2): a
placeholder is bound to the first linked form where the user *answered* the
question, not the first form that merely *defines* it.

The Indaba case this reproduces: both the registration form and the
application form ask for `gender`, but the registration form's demographics
section is tag-hidden from applicants (they already gave it at application
time). Binding `{gender}` to "the first form with a matching key" would work
for invited guests and silently fail for every applicant.
"""
from app import db
from app.documents.tests.base import DocumentsTestCase
from app.documents.resolver import PlaceholderResolver
from app.documents.models import DocumentTemplateForm


class TestResolverFallthrough(DocumentsTestCase):

    def _build_indaba_template(self):
        registration_form = self.make_form(form_type='registration')
        application_form = self.make_form(form_type='application')

        self.registration_gender_q = self.make_question(registration_form, 'gender')
        self.application_gender_q = self.make_question(application_form, 'gender')

        document_template = self.make_document_template(key='invitation-letter')
        self.make_variant(document_template, placeholders={'gender', 'firstname'})

        # Registration form searched first (higher order) - guests answer it
        # there; applicants fall through to the application form.
        self.link_form(document_template, registration_form, order=20)
        self.link_form(document_template, application_form, order=10)

        return document_template, registration_form, application_form

    def _resolve_gender(self, document_template):
        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)
        return result

    def test_invited_guest_resolves_from_registration_form(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        self.submit_response(registration_form, self.user, {self.registration_gender_q: 'female'})

        result = self._resolve_gender(document_template)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.snapshot['gender']['value'], 'female')
        self.assertIn('Registration', result.snapshot['gender']['source'])

    def test_applicant_with_hidden_registration_section_falls_through_to_application_form(self):
        """The registration form's demographics section would be tag-hidden
        from an applicant in the real app; here that's simulated directly by
        never submitting a `gender` answer on it - a submitted response with
        no answer to the question is exactly what a hidden section produces.
        """
        document_template, registration_form, application_form = self._build_indaba_template()

        # Applicant has a submitted registration response (they did register)
        # but the gender question was never shown to them, so no answer for it.
        self.submit_response(registration_form, self.user, {})
        self.submit_response(application_form, self.user, {self.application_gender_q: 'female'})

        result = self._resolve_gender(document_template)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.snapshot['gender']['value'], 'female')
        self.assertIn('Application', result.snapshot['gender']['source'])

    def test_blank_answer_falls_through_rather_than_masking_next_form(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        self.submit_response(registration_form, self.user, {self.registration_gender_q: '   '})
        self.submit_response(application_form, self.user, {self.application_gender_q: 'female'})

        result = self._resolve_gender(document_template)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.snapshot['gender']['value'], 'female')

    def test_unticked_single_checkbox_counts_as_no_answer(self):
        document_template = self.make_document_template(key='consent-letter')
        self.make_variant(document_template, placeholders={'agreed'})
        form = self.make_form()
        question = self.make_question(form, 'agreed', question_type='single-checkbox')
        self.link_form(document_template, form, order=10)

        self.set_user_data(self.event, self.user, 'agreed', 'yes-from-admin')
        self.submit_response(form, self.user, {question: 'false'})

        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.errors, [])
        # The unticked checkbox is blank, so resolution falls through past the
        # form entirely to user_event_data.
        self.assertEqual(result.snapshot['agreed']['value'], 'yes-from-admin')

    def test_draft_response_is_skipped_in_favour_of_submitted_form(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        # Draft (never submitted) registration response with an answer present -
        # must not be used, since the applicant hasn't actually confirmed it.
        self.submit_response(registration_form, self.user,
                              {self.registration_gender_q: 'female'}, submitted=False)
        self.submit_response(application_form, self.user, {self.application_gender_q: 'male'})

        result = self._resolve_gender(document_template)

        self.assertEqual(result.snapshot['gender']['value'], 'male')

    def test_both_forms_answered_higher_order_wins(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        self.submit_response(registration_form, self.user, {self.registration_gender_q: 'non-binary'})
        self.submit_response(application_form, self.user, {self.application_gender_q: 'female'})

        result = self._resolve_gender(document_template)

        self.assertEqual(result.snapshot['gender']['value'], 'non-binary')

    def test_no_form_answer_falls_through_to_user_event_data_then_profile(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        self.submit_response(registration_form, self.user, {})
        self.submit_response(application_form, self.user, {})

        # Nothing in user_event_data either - falls all the way to the
        # profile's own `gender` field.
        self.user.user_gender = 'female'
        db.session.commit()

        result = self._resolve_gender(document_template)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.snapshot['gender']['value'], 'female')
        self.assertEqual(result.snapshot['gender']['source'], 'user profile')

    def test_nothing_anywhere_reports_value_missing_naming_every_source_tried(self):
        document_template, registration_form, application_form = self._build_indaba_template()
        self.submit_response(registration_form, self.user, {})
        self.submit_response(application_form, self.user, {})
        # No user_event_data row, and profile gender left as the model default (None).

        result = self._resolve_gender(document_template)

        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.code, 'PLACEHOLDER_VALUE_MISSING')
        self.assertIn('linked form', error.message)
        self.assertIn('user data', error.message)
        self.assertIn('user profile', error.message)

    def test_required_form_satisfied_by_submission_that_leaves_key_unanswered(self):
        """`requirement='required'` means "submitted the form", never "answered
        this particular question" - the applicant case above depends on that
        distinction holding even when the form is a hard requirement."""
        document_template, registration_form, application_form = self._build_indaba_template()
        document_template.form_links[0].requirement = DocumentTemplateForm.REQUIREMENT_REQUIRED
        db.session.commit()

        self.submit_response(registration_form, self.user, {})  # submitted, gender unanswered
        self.submit_response(application_form, self.user, {self.application_gender_q: 'female'})

        from app.documents.resolver import evaluate_form_requirements
        blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(blockers, [])
