"""The form-viewer role: read and export an event's form responses, but never
change the forms themselves."""
import json

from app import db
from app.forms.models import (
    Form, FormTranslation, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation, FormResponse, FormAnswer
)
from app.utils.testing import ApiTestCase


class FormViewerTest(ApiTestCase):

    def seed_static_data(self):
        # Ids are held as plain integers: ORM instances are detached once the
        # test issues requests, and re-reading attributes off them raises.
        event = self.add_event(key='VIEWER2025')
        self.event_id = event.id
        admin = self.add_user('admin@example.com', 'Event', 'Admin', password='pw')
        self.admin_id = admin.id
        self.add_event_role('admin', self.admin_id, self.event_id)
        self.admin_headers = self.get_auth_header_for('admin@example.com', 'pw')

        viewer = self.add_user('viewer@example.com', 'Form', 'Viewer', password='pw')
        self.add_event_role('form-viewer', viewer.id, self.event_id)
        self.viewer_headers = self.get_auth_header_for('viewer@example.com', 'pw')

        other_event = self.add_event(key='OTHERVIEW2025')
        self.other_event_id = other_event.id
        other_viewer = self.add_user('otherviewer@example.com', 'Other', 'Viewer', password='pw')
        self.add_event_role('form-viewer', other_viewer.id, self.other_event_id)
        self.other_viewer_headers = self.get_auth_header_for('otherviewer@example.com', 'pw')

        applicant = self.add_user('applicant@example.com', 'Plain', 'User', password='pw')
        self.applicant_id = applicant.id
        self.applicant_headers = self.get_auth_header_for('applicant@example.com', 'pw')

        self.form_id = self._create_form(self.event_id, 'Feedback')
        self.response_id = self._add_response(self.form_id)

    def _create_form(self, event_id, name, form_type=None, is_active=True):
        form = Form(
            event_id=event_id, created_by_user_id=self.admin_id,
            form_type=form_type, is_open=True, is_active=is_active
        )
        db.session.add(form)
        db.session.flush()
        db.session.add(FormTranslation(form_id=form.id, language='en', name=name))

        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        db.session.add(FormSectionTranslation(
            form_section_id=section.id, language='en', name='Section One'
        ))

        question = FormQuestion(
            form_id=form.id, section_id=section.id, order=1,
            question_type='short-text', is_required=False
        )
        db.session.add(question)
        db.session.flush()
        db.session.add(FormQuestionTranslation(
            form_question_id=question.id, language='en', headline='Your name'
        ))
        db.session.commit()
        self.question_id = question.id
        return form.id

    def _add_response(self, form_id, is_submitted=True):
        response = FormResponse(form_id=form_id, user_id=self.applicant_id)
        response.is_submitted = is_submitted
        db.session.add(response)
        db.session.flush()
        db.session.add(FormAnswer(
            response_id=response.id, question_id=self.question_id, value='Confidential'
        ))
        db.session.commit()
        return response.id

    # ------------------------------------------------------------------
    # Read-only response endpoints admit viewers
    # ------------------------------------------------------------------

    def test_viewer_can_list_responses(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/admin?event_id={self.event_id}',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['pagination']['total'], 1)

    def test_viewer_can_read_response_detail(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/{self.response_id}/admin'
            f'?event_id={self.event_id}',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['answers'][0]['value'], 'Confidential')

    def test_viewer_can_read_stats(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/stats?event_id={self.event_id}',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['submitted'], 1)

    def test_viewer_can_export_csv(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/export?event_id={self.event_id}&format=csv',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Confidential', response.data.decode('utf-8'))

    def test_viewer_can_read_structure_of_inactive_form_with_inactive_questions(self):
        self.seed_static_data()
        form = db.session.query(Form).get(self.form_id)
        form.is_active = False
        db.session.query(FormQuestion).get(self.question_id).is_active = False
        db.session.commit()

        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/structure?include_inactive=true',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        questions = [q for s in json.loads(response.data)['sections'] for q in s['questions']]
        self.assertEqual(len(questions), 1)

    def test_viewer_of_another_event_cannot_read_responses(self):
        self.seed_static_data()
        # Neither by naming this event...
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/admin?event_id={self.event_id}',
            headers=self.other_viewer_headers
        )
        self.assertEqual(response.status_code, 403)
        # ...nor by passing their own event_id.
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/{self.response_id}/admin'
            f'?event_id={self.other_event_id}',
            headers=self.other_viewer_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_plain_user_cannot_read_responses(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/admin?event_id={self.event_id}',
            headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------
    # Everything that edits forms or responses stays admin-only
    # ------------------------------------------------------------------

    def test_viewer_cannot_read_form_config(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/form-config?event_id={self.event_id}', headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_list_form_definitions(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms?event_id={self.event_id}', headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_update_form(self):
        self.seed_static_data()
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}',
            data=json.dumps({'is_open': False}),
            headers=self.viewer_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.query(Form).get(self.form_id).is_open)

    def test_viewer_cannot_update_structure(self):
        self.seed_static_data()
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}/structure',
            data=json.dumps({'sections': []}),
            headers=self.viewer_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_delete_form(self):
        self.seed_static_data()
        response = self.app.delete(f'/api/v1/forms/{self.form_id}', headers=self.viewer_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(db.session.query(Form).get(self.form_id))

    def test_viewer_cannot_change_response_status(self):
        self.seed_static_data()
        response = self.app.patch(
            f'/api/v1/forms/{self.form_id}/responses/{self.response_id}/admin-status'
            f'?event_id={self.event_id}',
            data=json.dumps({'is_submitted': False}),
            headers=self.viewer_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.query(FormResponse).get(self.response_id).is_submitted)

    # ------------------------------------------------------------------
    # Responses summary
    # ------------------------------------------------------------------

    def test_summary_lists_event_forms_with_counts(self):
        self.seed_static_data()
        app_form_id = self._create_form(self.event_id, 'Application', form_type='application')
        self._add_response(app_form_id, is_submitted=True)
        self._add_response(app_form_id, is_submitted=False)
        self._create_form(self.other_event_id, 'Elsewhere')

        response = self.app.get(
            f'/api/v1/form-responses-summary?event_id={self.event_id}',
            headers=self.viewer_headers
        )
        self.assertEqual(response.status_code, 200)
        forms = json.loads(response.data)['forms']
        # Typed forms sort ahead of generic ones; other events' forms are absent.
        self.assertEqual([f['name'] for f in forms], ['Application', 'Feedback'])
        self.assertEqual(forms[0]['form_type'], 'application')
        self.assertEqual(forms[0]['response_count'], 2)
        self.assertEqual(forms[0]['submitted_count'], 1)
        self.assertEqual(forms[1]['response_count'], 1)
        self.assertNotIn('settings', forms[0])

    def test_summary_available_to_admin(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/form-responses-summary?event_id={self.event_id}',
            headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 200)

    def test_summary_rejects_plain_user_and_other_event_viewer(self):
        self.seed_static_data()
        for headers in (self.applicant_headers, self.other_viewer_headers):
            response = self.app.get(
                f'/api/v1/form-responses-summary?event_id={self.event_id}', headers=headers
            )
            self.assertEqual(response.status_code, 403)
