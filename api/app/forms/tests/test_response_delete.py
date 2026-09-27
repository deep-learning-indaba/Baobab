"""Admin deletion of a form response."""
import json
from unittest.mock import patch

from app import db
from app.forms.models import (
    Form, FormTranslation, FormSection, FormQuestion,
    FormResponse, FormAnswer, FormResponseTag
)
from app.tags.models import Tag
from app.utils.testing import ApiTestCase


class FormResponseDeleteTest(ApiTestCase):

    def seed_static_data(self):
        # Ids are held as plain integers: ORM instances are detached once the
        # test issues requests, and re-reading attributes off them raises.
        event = self.add_event(key='DELETE2025')
        self.event_id = event.id
        admin = self.add_user('admin@example.com', 'Event', 'Admin', password='pw')
        self.admin_id = admin.id
        self.add_event_role('admin', self.admin_id, self.event_id)
        self.admin_headers = self.get_auth_header_for('admin@example.com', 'pw')

        viewer = self.add_user('viewer@example.com', 'Form', 'Viewer', password='pw')
        self.add_event_role('form-viewer', viewer.id, self.event_id)
        self.viewer_headers = self.get_auth_header_for('viewer@example.com', 'pw')

        other_event = self.add_event(key='OTHERDEL2025')
        self.other_event_id = other_event.id
        other_admin = self.add_user('other@example.com', 'Other', 'Admin', password='pw')
        self.add_event_role('admin', other_admin.id, self.other_event_id)
        self.other_admin_headers = self.get_auth_header_for('other@example.com', 'pw')

        applicant = self.add_user('applicant@example.com', 'Ada', 'Applicant', password='pw')
        self.applicant_id = applicant.id
        reviewer = self.add_user('reviewer@example.com', 'Rex', 'Reviewer', password='pw')
        self.reviewer_id = reviewer.id

        self.add_email_template(
            'form-response-deleted',
            template='Dear {firstname}, your {form_name} response is gone. Contact {event_email}.',
            subject='Deleted: {form_name}'
        )

        self.form_id = self._create_form('Application', form_type='application')
        self.response_id = self._add_response(self.form_id, self.applicant_id)

    def _create_form(self, name, form_type=None, linked_form_id=None, event_id=None):
        form = Form(
            event_id=event_id or self.event_id, created_by_user_id=self.admin_id,
            form_type=form_type, is_open=True, linked_form_id=linked_form_id
        )
        if form_type == 'review':
            form.stage = 1
        db.session.add(form)
        db.session.flush()
        db.session.add(FormTranslation(form_id=form.id, language='en', name=name))
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        question = FormQuestion(
            form_id=form.id, section_id=section.id, order=1,
            question_type='short-text', is_required=False
        )
        db.session.add(question)
        db.session.commit()
        self.question_id = question.id
        return form.id

    def _add_response(self, form_id, user_id, linked_response_id=None, parent_response_id=None):
        response = FormResponse(
            form_id=form_id, user_id=user_id,
            linked_response_id=linked_response_id, parent_response_id=parent_response_id
        )
        response.is_submitted = True
        db.session.add(response)
        db.session.flush()
        db.session.add(FormAnswer(response_id=response.id, question_id=self.question_id, value='An answer'))
        db.session.commit()
        return response.id

    def _delete(self, form_id, response_id, headers, event_id=None):
        return self.app.delete(
            f'/api/v1/forms/{form_id}/responses/{response_id}/admin'
            f'?event_id={event_id or self.event_id}',
            headers=headers
        )

    @patch('app.utils.emailer.send_mail')
    def test_admin_deletes_response_and_answers_and_emails_respondent(self, send_mail):
        self.seed_static_data()
        response = self._delete(self.form_id, self.response_id, self.admin_headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.data)['email_sent'])
        self.assertIsNone(db.session.query(FormResponse).get(self.response_id))
        self.assertEqual(
            db.session.query(FormAnswer).filter_by(response_id=self.response_id).count(), 0
        )

        send_mail.assert_called_once()
        kwargs = send_mail.call_args.kwargs
        self.assertEqual(kwargs['recipient'], 'applicant@example.com')
        self.assertEqual(kwargs['subject'], 'Deleted: Application')
        self.assertIn('Dear Ada, your Application response is gone.', kwargs['body_text'])

    @patch('app.utils.emailer.send_mail')
    def test_delete_removes_tags(self, send_mail):
        self.seed_static_data()
        tag = Tag(event_id=self.event_id, tag_type='RESPONSE')
        db.session.add(tag)
        db.session.flush()
        db.session.add(FormResponseTag(form_response_id=self.response_id, tag_id=tag.id))
        db.session.commit()

        response = self._delete(self.form_id, self.response_id, self.admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            db.session.query(FormResponseTag).filter_by(form_response_id=self.response_id).count(), 0
        )

    @patch('app.utils.emailer.send_mail')
    def test_delete_removes_reviews_but_only_unlinks_other_linked_responses(self, send_mail):
        self.seed_static_data()
        review_form_id = self._create_form('Review', form_type='review', linked_form_id=self.form_id)
        review_id = self._add_response(review_form_id, self.reviewer_id, linked_response_id=self.response_id)
        followup_form_id = self._create_form('Follow-up', linked_form_id=self.form_id)
        followup_id = self._add_response(followup_form_id, self.applicant_id, linked_response_id=self.response_id)
        child_id = self._add_response(self.form_id, self.applicant_id, parent_response_id=self.response_id)

        response = self._delete(self.form_id, self.response_id, self.admin_headers)
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(db.session.query(FormResponse).get(review_id))
        followup = db.session.query(FormResponse).get(followup_id)
        self.assertIsNotNone(followup)
        self.assertIsNone(followup.linked_response_id)
        child = db.session.query(FormResponse).get(child_id)
        self.assertIsNotNone(child)
        self.assertIsNone(child.parent_response_id)
        # Only the respondent is emailed - not the reviewer whose review went too.
        send_mail.assert_called_once()

    @patch('app.utils.emailer.send_mail', side_effect=Exception('SMTP down'))
    def test_email_failure_still_deletes_and_is_reported(self, send_mail):
        self.seed_static_data()
        response = self._delete(self.form_id, self.response_id, self.admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(json.loads(response.data)['email_sent'])
        self.assertIsNone(db.session.query(FormResponse).get(self.response_id))

    @patch('app.utils.emailer.send_mail')
    def test_review_responses_cannot_be_deleted(self, send_mail):
        self.seed_static_data()
        review_form_id = self._create_form('Review', form_type='review', linked_form_id=self.form_id)
        review_id = self._add_response(review_form_id, self.reviewer_id, linked_response_id=self.response_id)

        response = self._delete(review_form_id, review_id, self.admin_headers)
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(db.session.query(FormResponse).get(review_id))
        send_mail.assert_not_called()

    @patch('app.utils.emailer.send_mail')
    def test_viewer_cannot_delete(self, send_mail):
        self.seed_static_data()
        response = self._delete(self.form_id, self.response_id, self.viewer_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(db.session.query(FormResponse).get(self.response_id))
        send_mail.assert_not_called()

    @patch('app.utils.emailer.send_mail')
    def test_admin_of_another_event_cannot_delete(self, send_mail):
        self.seed_static_data()
        response = self._delete(
            self.form_id, self.response_id, self.other_admin_headers, event_id=self.other_event_id
        )
        self.assertEqual(response.status_code, 404)
        self.assertIsNotNone(db.session.query(FormResponse).get(self.response_id))
        send_mail.assert_not_called()

    @patch('app.utils.emailer.send_mail')
    def test_response_must_belong_to_form_in_url(self, send_mail):
        self.seed_static_data()
        other_form_id = self._create_form('Other')
        response = self._delete(other_form_id, self.response_id, self.admin_headers)
        self.assertEqual(response.status_code, 404)
        self.assertIsNotNone(db.session.query(FormResponse).get(self.response_id))
