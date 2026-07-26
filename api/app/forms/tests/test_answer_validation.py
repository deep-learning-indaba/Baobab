"""Tests for answer validation and the response lifecycle.

Covers the specific holes that let invalid responses through:
  - an unticked required checkbox stored as the string 'false' passed the
    required check on both client and server
  - configurable numeric bounds and word limits were never enforced anywhere
  - editing a submitted response silently un-submitted it
  - answers could be written against another form's questions
"""
import json

from app import db
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation, FormResponse, FormAnswer,
    ValidationError, answer_is_blank, count_words
)
from app.utils.testing import ApiTestCase


class AnswerValidationTest(ApiTestCase):

    def seed_static_data(self):
        event = self.add_event(key='VALIDATE2025')
        self.event_id = event.id
        admin = self.add_user('admin@example.com', 'Admin', 'User', password='pw')
        self.admin_id = admin.id
        self.add_event_role('admin', self.admin_id, self.event_id)
        applicant = self.add_user('applicant@example.com', 'App', 'Licant', password='pw')
        self.applicant_id = applicant.id
        self.headers = self.get_auth_header_for('applicant@example.com', 'pw')

    def _build_form(self, questions, is_open=True, allow_edits=True):
        """questions: list of dicts with type/is_required/settings/headline."""
        form = Form(
            event_id=self.event_id, created_by_user_id=self.admin_id,
            is_open=is_open, allow_edits=allow_edits
        )
        db.session.add(form)
        db.session.flush()

        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        db.session.add(FormSectionTranslation(
            form_section_id=section.id, language='en', name='Section'
        ))

        question_ids = []
        for index, spec in enumerate(questions, start=1):
            question = FormQuestion(
                form_id=form.id, section_id=section.id, order=index,
                question_type=spec['type'],
                is_required=spec.get('is_required', False),
                settings=spec.get('settings')
            )
            db.session.add(question)
            db.session.flush()
            db.session.add(FormQuestionTranslation(
                form_question_id=question.id, language='en',
                headline=spec.get('headline', f'Question {index}'),
                validation_regex=spec.get('validation_regex'),
                options=spec.get('options')
            ))
            question_ids.append(question.id)

        db.session.commit()
        return form.id, question_ids

    def _create_response(self, form_id, answers):
        return self.app.post(
            f'/api/v1/forms/{form_id}/response',
            data=json.dumps({'language': 'en', 'answers': answers}),
            headers=self.headers,
            content_type='application/json'
        )

    def _submit(self, form_id, response_id):
        return self.app.post(
            f'/api/v1/forms/{form_id}/responses/{response_id}/submit',
            data=json.dumps({}), headers=self.headers, content_type='application/json'
        )

    def _errors(self, response):
        return {e['question_id']: e['error'] for e in json.loads(response.data)['details']}

    # ------------------------------------------------------------------
    # Blank-answer semantics
    # ------------------------------------------------------------------

    def test_answer_is_blank_treats_unticked_checkbox_as_empty(self):
        self.assertTrue(answer_is_blank('single-checkbox', 'false'))
        self.assertTrue(answer_is_blank('single-checkbox', 'False'))
        self.assertTrue(answer_is_blank('single-checkbox', ''))
        self.assertFalse(answer_is_blank('single-checkbox', 'true'))
        # 'false' is a perfectly good text answer for any other type
        self.assertFalse(answer_is_blank('short-text', 'false'))

    def test_count_words(self):
        self.assertEqual(count_words(''), 0)
        self.assertEqual(count_words('Hello, my name is Bob.'), 5)
        self.assertEqual(count_words('  spaced   out  words '), 3)

    def test_required_checkbox_cannot_be_submitted_unticked(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'single-checkbox', 'is_required': True, 'headline': 'I agree'}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'false'}])
        self.assertEqual(created.status_code, 201)
        response_id = json.loads(created.data)['id']

        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(self._errors(submitted)[question_id], ValidationError.REQUIRED.value)
        self.assertFalse(db.session.query(FormResponse).get(response_id).is_submitted)

    def test_required_checkbox_accepted_when_ticked(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'single-checkbox', 'is_required': True, 'headline': 'I agree'}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'true'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    # ------------------------------------------------------------------
    # Numeric bounds
    # ------------------------------------------------------------------

    def test_numeric_bounds_enforced(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'numeric', 'settings': {'min_value': 0, 'max_value': 10}}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': '9999'}])
        response_id = json.loads(created.data)['id']

        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(
            self._errors(submitted)[question_id], ValidationError.ABOVE_MAX_VALUE.value
        )

    def test_numeric_below_minimum_rejected(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'numeric', 'settings': {'min_value': 5}}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': '1'}])
        response_id = json.loads(created.data)['id']
        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(
            self._errors(submitted)[question_id], ValidationError.BELOW_MIN_VALUE.value
        )

    def test_numeric_within_bounds_accepted(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'numeric', 'settings': {'min_value': 0, 'max_value': 10}}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': '7'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    # ------------------------------------------------------------------
    # Word limits (replacing the old generated word-limit regex)
    # ------------------------------------------------------------------

    def test_word_limits_enforced(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'long-text', 'settings': {'min_words': 3, 'max_words': 10}}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'Too short'}])
        response_id = json.loads(created.data)['id']
        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(
            self._errors(submitted)[question_id], ValidationError.TOO_FEW_WORDS.value
        )

    def test_prose_with_punctuation_and_accents_accepted(self):
        """The old regex-based word limit rejected any real prose."""
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'long-text', 'settings': {'min_words': 3, 'max_words': 10}}
        ])
        created = self._create_response(form_id, [
            {'question_id': question_id, 'value': "Bonjour, je m'appelle Amara — je suis née à Dakar."}
        ])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    def test_too_many_words_rejected(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'long-text', 'settings': {'max_words': 3}}
        ])
        created = self._create_response(form_id, [
            {'question_id': question_id, 'value': 'one two three four five'}
        ])
        response_id = json.loads(created.data)['id']
        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(
            self._errors(submitted)[question_id], ValidationError.TOO_MANY_WORDS.value
        )

    # ------------------------------------------------------------------
    # Regex semantics
    # ------------------------------------------------------------------

    def test_regex_must_match_the_whole_answer(self):
        """re.fullmatch, so an unanchored pattern isn't satisfied by a substring."""
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'short-text', 'validation_regex': '[0-9]{4}'}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'abc1234'}])
        response_id = json.loads(created.data)['id']
        submitted = self._submit(form_id, response_id)
        self.assertEqual(submitted.status_code, 400)
        self.assertEqual(
            self._errors(submitted)[question_id],
            ValidationError.VALIDATION_REGEX_FAILED.value
        )

    def test_regex_accepts_full_match(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([
            {'type': 'short-text', 'validation_regex': '[0-9]{4}'}
        ])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': '1234'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    # ------------------------------------------------------------------
    # Display-only questions
    # ------------------------------------------------------------------

    def test_display_only_question_never_blocks_submission(self):
        self.seed_static_data()
        form_id, question_ids = self._build_form([
            {'type': 'sub-heading', 'is_required': True, 'headline': 'A heading'},
            {'type': 'short-text', 'is_required': False},
        ])
        created = self._create_response(form_id, [])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    # ------------------------------------------------------------------
    # Response lifecycle
    # ------------------------------------------------------------------

    def test_editing_a_submitted_response_keeps_it_submitted(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([{'type': 'short-text'}])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'First'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

        updated = self.app.put(
            f'/api/v1/forms/{form_id}/response',
            data=json.dumps({
                'response_id': response_id,
                'answers': [{'question_id': question_id, 'value': 'Edited'}]
            }),
            headers=self.headers, content_type='application/json'
        )
        self.assertEqual(updated.status_code, 200)

        stored = db.session.query(FormResponse).get(response_id)
        self.assertTrue(stored.is_submitted, 'editing must not silently un-submit')
        self.assertIsNotNone(stored.submitted_timestamp)

    def test_cannot_edit_submitted_response_when_edits_disallowed(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([{'type': 'short-text'}], allow_edits=False)
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'First'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

        updated = self.app.put(
            f'/api/v1/forms/{form_id}/response',
            data=json.dumps({
                'response_id': response_id,
                'answers': [{'question_id': question_id, 'value': 'Edited'}]
            }),
            headers=self.headers, content_type='application/json'
        )
        self.assertEqual(updated.status_code, 400)

    def test_cannot_submit_to_a_closed_form(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([{'type': 'short-text'}])
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'x'}])
        response_id = json.loads(created.data)['id']

        db.session.query(Form).get(form_id).is_open = False
        db.session.commit()

        # APPLICATIONS_CLOSED is a 403
        self.assertEqual(self._submit(form_id, response_id).status_code, 403)
        self.assertFalse(db.session.query(FormResponse).get(response_id).is_submitted)

    def test_answers_must_belong_to_the_form(self):
        self.seed_static_data()
        form_id, _ = self._build_form([{'type': 'short-text'}])
        other_form_id, [foreign_question_id] = self._build_form([{'type': 'short-text'}])

        created = self._create_response(
            form_id, [{'question_id': foreign_question_id, 'value': 'smuggled'}]
        )
        self.assertEqual(created.status_code, 400)
        self.assertEqual(
            db.session.query(FormAnswer).filter_by(question_id=foreign_question_id).count(), 0
        )

    def test_update_rejects_answers_from_another_form(self):
        self.seed_static_data()
        form_id, [question_id] = self._build_form([{'type': 'short-text'}])
        _, [foreign_question_id] = self._build_form([{'type': 'short-text'}])

        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'ok'}])
        response_id = json.loads(created.data)['id']

        updated = self.app.put(
            f'/api/v1/forms/{form_id}/response',
            data=json.dumps({
                'response_id': response_id,
                'answers': [{'question_id': foreign_question_id, 'value': 'smuggled'}]
            }),
            headers=self.headers, content_type='application/json'
        )
        self.assertEqual(updated.status_code, 400)

    # ------------------------------------------------------------------
    # Structure updates can now clear fields
    # ------------------------------------------------------------------

    def test_switching_away_from_a_choice_type_clears_its_options(self):
        """Stale options used to reject every free-text answer as invalid."""
        self.seed_static_data()
        admin_headers = self.get_auth_header_for('admin@example.com', 'pw')
        form_id, [question_id] = self._build_form([{
            'type': 'combobox',
            'options': [{'value': 'a', 'label': 'Alpha'}]
        }])

        payload = {
            'sections': [{
                'id': db.session.query(FormQuestion).get(question_id).section_id,
                'order': 1,
                'name': {'en': 'Section'},
                'questions': [{
                    'id': question_id,
                    'order': 1,
                    'type': 'short-text',
                    'is_required': False,
                    'headline': {'en': 'Now free text'},
                    'options': {'en': []}
                }]
            }]
        }
        updated = self.app.put(
            f'/api/v1/forms/{form_id}/structure',
            data=json.dumps(payload), headers=admin_headers,
            content_type='application/json'
        )
        self.assertEqual(updated.status_code, 200)

        translation = db.session.query(FormQuestionTranslation).filter_by(
            form_question_id=question_id, language='en'
        ).first()
        self.assertFalse(translation.options)

        # And a free-text answer now submits cleanly
        created = self._create_response(form_id, [{'question_id': question_id, 'value': 'anything'}])
        response_id = json.loads(created.data)['id']
        self.assertEqual(self._submit(form_id, response_id).status_code, 200)

    def test_section_and_question_keys_can_be_cleared(self):
        self.seed_static_data()
        admin_headers = self.get_auth_header_for('admin@example.com', 'pw')
        form_id, [question_id] = self._build_form([{'type': 'short-text'}])
        question = db.session.query(FormQuestion).get(question_id)
        section_id = question.section_id
        question.key = 'old_key'
        db.session.query(FormSection).get(section_id).key = 'old_section_key'
        db.session.commit()

        payload = {
            'sections': [{
                'id': section_id, 'order': 1, 'name': {'en': 'Section'}, 'key': None,
                'questions': [{
                    'id': question_id, 'order': 1, 'type': 'short-text',
                    'is_required': False, 'headline': {'en': 'Q'}, 'key': None
                }]
            }]
        }
        updated = self.app.put(
            f'/api/v1/forms/{form_id}/structure',
            data=json.dumps(payload), headers=admin_headers,
            content_type='application/json'
        )
        self.assertEqual(updated.status_code, 200)
        self.assertIsNone(db.session.query(FormSection).get(section_id).key)
        self.assertIsNone(db.session.query(FormQuestion).get(question_id).key)

    def test_tag_expression_round_trips(self):
        """Section and question tag rules were previously never persisted."""
        self.seed_static_data()
        admin_headers = self.get_auth_header_for('admin@example.com', 'pw')
        form_id, [question_id] = self._build_form([{'type': 'short-text'}])
        section_id = db.session.query(FormQuestion).get(question_id).section_id

        expression = {'operator': 'OR', 'conditions': [{'tag': 'invited_guest'}]}
        payload = {
            'sections': [{
                'id': section_id, 'order': 1, 'name': {'en': 'Section'},
                'tag_expression': expression,
                'questions': [{
                    'id': question_id, 'order': 1, 'type': 'short-text',
                    'is_required': False, 'headline': {'en': 'Q'},
                    'tag_expression': {'tag': 'selected_attendee'}
                }]
            }]
        }
        updated = self.app.put(
            f'/api/v1/forms/{form_id}/structure',
            data=json.dumps(payload), headers=admin_headers,
            content_type='application/json'
        )
        self.assertEqual(updated.status_code, 200)

        self.assertEqual(db.session.query(FormSection).get(section_id).tag_expression, expression)
        self.assertEqual(
            db.session.query(FormQuestion).get(question_id).tag_expression,
            {'tag': 'selected_attendee'}
        )

        # And the serialized structure hands them back to the editor
        fetched = self.app.get(
            f'/api/v1/forms/{form_id}/structure', headers=admin_headers
        )
        data = json.loads(fetched.data)
        self.assertEqual(data['sections'][0]['tag_expression'], expression)
        self.assertEqual(
            data['sections'][0]['questions'][0]['tag_expression'],
            {'tag': 'selected_attendee'}
        )
