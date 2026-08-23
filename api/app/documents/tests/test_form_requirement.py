"""requirement='required'/'recommended'/'none' on a linked form - design
section 5.2.4. The key property under test: a recommended form must never
block, error, or affect eligibility - only inform."""
from app.documents.tests.base import DocumentsTestCase
from app.documents.resolver import evaluate_form_requirements
from app.documents.models import DocumentTemplateForm


class TestFormRequirement(DocumentsTestCase):

    def test_none_requirement_produces_no_blocker_or_prompt(self):
        form = self.make_form(name='Registration Form')
        document_template = self.make_document_template()
        self.link_form(document_template, form, order=10, requirement=DocumentTemplateForm.REQUIREMENT_NONE)

        blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(blockers, [])
        self.assertEqual(prompts, [])

    def test_required_not_submitted_blocks(self):
        form = self.make_form(name='Registration Form')
        document_template = self.make_document_template()
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_REQUIRED,
                        prompt_message='Complete the Registration form first.')

        blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(len(blockers), 1)
        self.assertEqual(prompts, [])
        self.assertEqual(blockers[0]['form_name'], 'Registration Form')
        self.assertEqual(blockers[0]['message'], 'Complete the Registration form first.')

    def test_required_submitted_does_not_block(self):
        form = self.make_form()
        document_template = self.make_document_template()
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_REQUIRED)
        self.submit_response(form, self.user, {})

        blockers, _prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(blockers, [])

    def test_recommended_not_submitted_prompts_but_never_blocks(self):
        form = self.make_form(name='Post-Event Survey')
        document_template = self.make_document_template()
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED,
                        prompt_message='Please take two minutes to complete the survey.')

        blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(blockers, [])
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]['form_name'], 'Post-Event Survey')
        self.assertEqual(prompts[0]['message'], 'Please take two minutes to complete the survey.')

    def test_recommended_submitted_produces_no_prompt(self):
        form = self.make_form()
        document_template = self.make_document_template()
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED)
        self.submit_response(form, self.user, {})

        _blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(prompts, [])

    def test_recommended_answers_still_participate_in_resolution(self):
        """Linking a form purely for the nudge doesn't stop its answers being
        readable - it's still a linked form, just one that never gates
        generation. See design section 5.2.4."""
        form = self.make_form()
        question = self.make_question(form, 'dietary')
        document_template = self.make_document_template()
        self.make_variant(document_template, placeholders={'dietary'})
        self.link_form(document_template, form, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED)
        self.submit_response(form, self.user, {question: 'vegan'})

        from app.documents.resolver import PlaceholderResolver
        resolver = PlaceholderResolver(document_template, self.event)
        result = resolver.resolve(self.user)

        self.assertEqual(result.values['dietary'], 'vegan')

    def test_mixed_required_and_recommended_links(self):
        registration = self.make_form(name='Registration Form')
        survey = self.make_form(name='Post-Event Survey')
        document_template = self.make_document_template()
        self.link_form(document_template, registration, order=20,
                        requirement=DocumentTemplateForm.REQUIREMENT_REQUIRED,
                        prompt_message='Registration required.')
        self.link_form(document_template, survey, order=10,
                        requirement=DocumentTemplateForm.REQUIREMENT_RECOMMENDED,
                        prompt_message='Survey recommended.')

        blockers, prompts = evaluate_form_requirements(document_template, self.user)

        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0]['form_name'], 'Registration Form')
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]['form_name'], 'Post-Event Survey')

    def test_no_linked_forms_produces_nothing(self):
        document_template = self.make_document_template()
        blockers, prompts = evaluate_form_requirements(document_template, self.user)
        self.assertEqual(blockers, [])
        self.assertEqual(prompts, [])
