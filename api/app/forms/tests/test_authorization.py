"""Authorization tests for the generic form endpoints.

The form definition endpoints were previously only @auth_required, so any
authenticated user could list, rewrite, close or delete any form in the system.
The admin response endpoints took a caller-supplied event_id and never checked
that the form actually belonged to that event, so an admin of one event could
read another event's applicant data.

These tests pin both behaviours down.
"""
import json

from app import db
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation, FormResponse, FormAnswer
)
from app.utils.testing import ApiTestCase


class FormAuthorizationTest(ApiTestCase):

    def seed_static_data(self):
        # Ids are held as plain integers: the ORM instances get detached once the
        # test issues requests through the app, and re-reading an attribute off a
        # detached instance raises.
        event = self.add_event(key='OWNER2025')
        self.event_id = event.id
        admin = self.add_user('admin@example.com', 'Owner', 'Admin', password='pw')
        self.admin_id = admin.id
        self.add_event_role('admin', self.admin_id, self.event_id)
        self.admin_headers = self.get_auth_header_for('admin@example.com', 'pw')

        # An unrelated event with its own admin
        other_event = self.add_event(key='OTHER2025')
        self.other_event_id = other_event.id
        other_admin = self.add_user('other@example.com', 'Other', 'Admin', password='pw')
        self.add_event_role('admin', other_admin.id, self.other_event_id)
        self.other_admin_headers = self.get_auth_header_for('other@example.com', 'pw')

        # A plain registered user with no roles at all
        applicant = self.add_user('applicant@example.com', 'Plain', 'User', password='pw')
        self.applicant_id = applicant.id
        self.applicant_headers = self.get_auth_header_for('applicant@example.com', 'pw')

        self.form_id = self._create_form(self.event_id)

    def _create_form(self, event_id):
        form = Form(event_id=event_id, created_by_user_id=self.admin_id, is_open=True)
        db.session.add(form)
        db.session.flush()

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

        self.section_id = section.id
        self.question_id = question.id
        return form.id

    # ------------------------------------------------------------------
    # Form definition endpoints must require event admin rights
    # ------------------------------------------------------------------

    def test_form_list_requires_event_admin(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms?event_id={self.event_id}', headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_form_list_rejects_admin_of_another_event(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms?event_id={self.event_id}', headers=self.other_admin_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_form_list_scoped_to_requested_event(self):
        self.seed_static_data()
        self._create_form(self.other_event_id)
        response = self.app.get(
            f'/api/v1/forms?event_id={self.event_id}', headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(all(f['event_id'] == self.event_id for f in data))

    def test_get_form_definition_requires_event_admin(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}', headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_get_form_definition_rejects_admin_of_another_event(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}', headers=self.other_admin_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_update_form_requires_event_admin(self):
        self.seed_static_data()
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}',
            data=json.dumps({'is_open': False, 'name': {'en': 'Hijacked'}}),
            headers=self.applicant_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.query(Form).get(self.form_id).is_open)

    def test_delete_form_requires_event_admin(self):
        self.seed_static_data()
        response = self.app.delete(
            f'/api/v1/forms/{self.form_id}', headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.query(Form).get(self.form_id).is_active)

    def test_update_structure_requires_event_admin(self):
        self.seed_static_data()
        payload = {
            'sections': [{
                'order': 1,
                'name': {'en': 'Injected'},
                'questions': [{
                    'order': 1, 'type': 'short-text',
                    'headline': {'en': 'Injected question'}
                }]
            }]
        }
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}/structure',
            data=json.dumps(payload),
            headers=self.applicant_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(db.session.query(FormQuestion).get(self.question_id).is_active)

    def test_update_structure_rejects_admin_of_another_event(self):
        self.seed_static_data()
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}/structure',
            data=json.dumps({'sections': []}),
            headers=self.other_admin_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_create_form_requires_event_admin(self):
        self.seed_static_data()
        response = self.app.post(
            f'/api/v1/forms?event_id={self.event_id}',
            data=json.dumps({'event_id': self.event_id}),
            headers=self.applicant_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_create_form_cannot_target_another_event(self):
        """Creating a form for an event the caller does not administer is refused."""
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps({'event_id': self.other_event_id}),
            headers=self.admin_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_create_form_uses_the_authorized_event(self):
        """A created form always belongs to the event whose rights were checked."""
        self.seed_static_data()
        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps({'event_id': self.event_id}),
            headers=self.admin_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        created = db.session.query(Form).get(json.loads(response.data)['id'])
        self.assertEqual(created.event_id, self.event_id)

    def test_cannot_link_form_across_events(self):
        self.seed_static_data()
        foreign_form_id = self._create_form(self.other_event_id)
        response = self.app.put(
            f'/api/v1/forms/{self.form_id}',
            data=json.dumps({'linked_form_id': foreign_form_id}),
            headers=self.admin_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------
    # Structure GET stays open to respondents, but only for active forms
    # ------------------------------------------------------------------

    def test_applicant_can_read_structure_of_active_form(self):
        self.seed_static_data()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/structure', headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 200)

    def test_applicant_cannot_read_structure_of_inactive_form(self):
        self.seed_static_data()
        db.session.query(Form).get(self.form_id).is_active = False
        db.session.commit()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/structure', headers=self.applicant_headers
        )
        self.assertEqual(response.status_code, 404)

    def test_applicant_cannot_request_inactive_questions(self):
        """include_inactive is an admin audit flag, not something respondents get."""
        self.seed_static_data()
        db.session.query(FormQuestion).get(self.question_id).is_active = False
        db.session.commit()

        as_applicant = self.app.get(
            f'/api/v1/forms/{self.form_id}/structure?include_inactive=true',
            headers=self.applicant_headers
        )
        self.assertEqual(as_applicant.status_code, 200)
        applicant_questions = [
            q for s in json.loads(as_applicant.data)['sections'] for q in s['questions']
        ]
        self.assertEqual(applicant_questions, [])

        as_admin = self.app.get(
            f'/api/v1/forms/{self.form_id}/structure?include_inactive=true',
            headers=self.admin_headers
        )
        admin_questions = [
            q for s in json.loads(as_admin.data)['sections'] for q in s['questions']
        ]
        self.assertEqual(len(admin_questions), 1)

    # ------------------------------------------------------------------
    # Admin response endpoints must verify the form belongs to the event
    # ------------------------------------------------------------------

    def _add_response(self):
        response = FormResponse(form_id=self.form_id, user_id=self.applicant_id)
        db.session.add(response)
        db.session.flush()
        db.session.add(FormAnswer(
            response_id=response.id, question_id=self.question_id, value='Confidential'
        ))
        db.session.commit()
        return response.id

    def test_response_list_admin_rejects_other_events_form(self):
        self.seed_static_data()
        self._add_response()
        # Passing their own event_id must not grant access to this event's form.
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/admin?event_id={self.other_event_id}',
            headers=self.other_admin_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_response_detail_admin_rejects_other_events_form(self):
        self.seed_static_data()
        response_id = self._add_response()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/{response_id}/admin'
            f'?event_id={self.other_event_id}',
            headers=self.other_admin_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_response_status_patch_rejects_other_events_form(self):
        self.seed_static_data()
        response_id = self._add_response()
        response = self.app.patch(
            f'/api/v1/forms/{self.form_id}/responses/{response_id}/admin-status'
            f'?event_id={self.other_event_id}',
            data=json.dumps({'is_submitted': True}),
            headers=self.other_admin_headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(db.session.query(FormResponse).get(response_id).is_submitted)

    def test_owning_admin_can_read_responses(self):
        self.seed_static_data()
        self._add_response()
        response = self.app.get(
            f'/api/v1/forms/{self.form_id}/responses/admin?event_id={self.event_id}',
            headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['pagination']['total'], 1)
