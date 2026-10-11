"""Tests for Phase 1 generic forms migration: form_type/stage model fields,
helper functions, and the GET /api/v1/form-config endpoint."""
import json
from app import db
from app.forms.models import Form, FormResponse, FormTranslation
from app.forms import system as form_system
from app.forms.mixins import apply_form_type_defaults, validate_form_type_constraints
from app.utils.testing import ApiTestCase


class TestFormTypeModel(ApiTestCase):
    """Tests for form_type and stage fields on the Form model."""

    def seed_static_data(self):
        self.user = self.add_user('admin@test.com', 'Admin', 'User')
        self.event = self.add_event()
        self.add_event_role('admin', self.user.id, self.event.id)
        self.auth_headers = self.get_auth_header_for('admin@test.com')
        self.user = db.session.merge(self.user)
        self.event = db.session.merge(self.event)

    def test_form_type_defaults_to_none(self):
        """A form with no form_type has form_type=None."""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.commit()

        self.assertIsNone(form.form_type)
        self.assertIsNone(form.stage)

    def test_form_type_registration(self):
        """A registration form stores form_type='registration'."""
        self.seed_static_data()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='registration'
        )
        db.session.add(form)
        db.session.commit()

        saved = db.session.query(Form).filter_by(id=form.id).first()
        self.assertEqual(saved.form_type, 'registration')
        self.assertIsNone(saved.stage)

    def test_form_type_application(self):
        """A form with form_type='application' is stored correctly."""
        self.seed_static_data()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='application'
        )
        db.session.add(form)
        db.session.commit()

        saved = db.session.query(Form).filter_by(id=form.id).first()
        self.assertEqual(saved.form_type, 'application')

    def test_form_type_review_with_stage(self):
        """A review form stores form_type='review' and stage."""
        self.seed_static_data()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='review',
            stage=1
        )
        db.session.add(form)
        db.session.commit()

        saved = db.session.query(Form).filter_by(id=form.id).first()
        self.assertEqual(saved.form_type, 'review')
        self.assertEqual(saved.stage, 1)

    def test_form_type_in_api_response(self):
        """GET /api/v1/forms/{form_id} includes form_type and stage."""
        self.seed_static_data()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='registration'
        )
        db.session.add(form)
        db.session.commit()

        response = self.app.get(
            '/api/v1/forms/{}?language=en'.format(form.id),
            headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['form_type'], 'registration')
        self.assertIsNone(data['stage'])

    def test_stage_in_api_response(self):
        """GET /api/v1/forms/{form_id} includes stage for review forms."""
        self.seed_static_data()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='review',
            stage=2
        )
        db.session.add(form)
        db.session.commit()

        response = self.app.get(
            '/api/v1/forms/{}?language=en'.format(form.id),
            headers=self.auth_headers
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['form_type'], 'review')
        self.assertEqual(data['stage'], 2)


class TestFormTypeDefaults(ApiTestCase):
    """Tests for apply_form_type_defaults helper and POST /api/v1/forms."""

    def seed_static_data(self):
        self.user = self.add_user('admin@test.com', 'Admin', 'User')
        self.event = self.add_event()
        self.add_event_role('admin', self.user.id, self.event.id)
        self.auth_headers = self.get_auth_header_for('admin@test.com')
        self.user = db.session.merge(self.user)
        self.event = db.session.merge(self.event)

    def test_registration_defaults_applied(self):
        """Creating a registration form applies correct defaults."""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        apply_form_type_defaults(form, 'registration')

        self.assertFalse(form.multiple_responses)
        self.assertTrue(form.allow_edits)
        self.assertIsNotNone(form.visibility_expression)
        self.assertEqual(form.visibility_expression['operator'], 'OR')
        conditions = form.visibility_expression['conditions']
        tags = [c['tag'] for c in conditions]
        self.assertIn('selected_attendee', tags)
        self.assertIn('invited_guest', tags)

    def test_application_defaults_applied(self):
        """Creating an application form applies correct defaults."""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        apply_form_type_defaults(form, 'application')

        self.assertFalse(form.multiple_responses)
        self.assertTrue(form.allow_edits)
        self.assertIsNotNone(form.settings)
        self.assertTrue(form.settings['page_per_section'])

    def test_review_defaults_applied(self):
        """Creating a review form applies correct defaults."""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        apply_form_type_defaults(form, 'review', stage=1)

        self.assertTrue(form.multiple_responses)
        self.assertTrue(form.allow_edits)
        self.assertIsNotNone(form.settings)
        self.assertIn('num_reviews_required', form.settings)
        self.assertEqual(form.settings['num_reviews_required'], 3)
        self.assertEqual(form.stage, 1)

    def test_post_registration_form_applies_defaults(self):
        """POST /api/v1/forms with form_type=registration applies defaults."""
        self.seed_static_data()
        payload = {
            'event_id': self.event.id,
            'form_type': 'registration',
            'is_open': False
        }

        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps(payload),
            headers=self.auth_headers,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        form_id = data['id']

        form = db.session.query(Form).filter_by(id=form_id).first()
        self.assertEqual(form.form_type, 'registration')
        self.assertFalse(form.multiple_responses)
        self.assertIsNotNone(form.visibility_expression)

    def test_post_application_form_applies_defaults(self):
        """POST /api/v1/forms with form_type=application applies defaults."""
        self.seed_static_data()
        payload = {
            'event_id': self.event.id,
            'form_type': 'application'
        }

        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps(payload),
            headers=self.auth_headers,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        form = db.session.query(Form).filter_by(id=data['id']).first()
        self.assertEqual(form.form_type, 'application')
        self.assertIsNotNone(form.settings)
        self.assertTrue(form.settings['page_per_section'])

    def test_post_review_form_rejected_without_application_form(self):
        """POST review form is rejected if no new-style application form exists."""
        self.seed_static_data()
        payload = {
            'event_id': self.event.id,
            'form_type': 'review',
            'stage': 1
        }

        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps(payload),
            headers=self.auth_headers,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_post_review_form_succeeds_with_application_form(self):
        """POST review form succeeds when a new-style application form exists."""
        self.seed_static_data()
        # Create application form first
        app_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='application'
        )
        db.session.add(app_form)
        db.session.commit()

        payload = {
            'event_id': self.event.id,
            'form_type': 'review',
            'stage': 1
        }

        response = self.app.post(
            '/api/v1/forms',
            data=json.dumps(payload),
            headers=self.auth_headers,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        form = db.session.query(Form).filter_by(id=data['id']).first()
        self.assertEqual(form.form_type, 'review')
        self.assertEqual(form.stage, 1)
        self.assertTrue(form.multiple_responses)


class TestFormHelpers(ApiTestCase):
    """Tests for the form system selection helpers and form type constraints."""

    def seed_static_data(self, uses_new_forms=True):
        self.user = self.add_user('admin@test.com', 'Admin', 'User')
        self.event = self.add_event(uses_new_forms=uses_new_forms)

    def _form(self, form_type, **kwargs):
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, form_type=form_type, **kwargs)
        db.session.add(form)
        db.session.commit()
        return form

    def test_typed_form_none_when_absent(self):
        self.seed_static_data()
        self.assertIsNone(form_system.get_registration_form(self.event.id))
        self.assertIsNone(form_system.get_application_form(self.event.id))

    def test_typed_form_found_on_new_system_event(self):
        self.seed_static_data()
        form = self._form('registration')
        self.assertEqual(form_system.get_registration_form(self.event.id).id, form.id)
        self.assertIsNone(form_system.get_application_form(self.event.id))

    def test_typed_form_ignored_on_legacy_event(self):
        self.seed_static_data(uses_new_forms=False)
        self._form('registration')
        self.assertFalse(form_system.event_uses_new_forms(self.event.id))
        self.assertIsNone(form_system.get_registration_form(self.event.id))

    def test_review_forms_in_stage_order(self):
        self.seed_static_data()
        self._form('review', stage=2)
        self._form('review', stage=1)
        self.assertEqual([f.stage for f in form_system.get_review_forms(self.event.id)], [1, 2])

    def test_active_review_form_is_the_active_stage(self):
        self.seed_static_data()
        stage1 = self._form('review', stage=1, is_active=True)
        self._form('review', stage=2, is_active=False)
        self.assertEqual(form_system.get_active_review_form(self.event.id).id, stage1.id)

    def test_active_review_form_falls_back_to_latest_stage(self):
        self.seed_static_data()
        self._form('review', stage=1, is_active=False)
        stage2 = self._form('review', stage=2, is_active=False)
        self.assertEqual(form_system.get_active_review_form(self.event.id).id, stage2.id)

    def test_validate_review_form_constraints_fails_without_app_form(self):
        """Validate review form constraint fails when no application form."""
        self.seed_static_data()
        error = validate_form_type_constraints(self.event.id, 'review')
        self.assertIsNotNone(error)

    def test_validate_review_form_constraints_passes_with_app_form(self):
        """Validate review form constraint passes when application form exists."""
        self.seed_static_data()
        app_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.user.id,
            form_type='application'
        )
        db.session.add(app_form)
        db.session.commit()

        error = validate_form_type_constraints(self.event.id, 'review')
        self.assertIsNone(error)

    def test_validate_application_form_no_constraint(self):
        """Application form creation has no constraints."""
        self.seed_static_data()
        error = validate_form_type_constraints(self.event.id, 'application')
        self.assertIsNone(error)

    def test_validate_registration_form_no_constraint(self):
        """Registration form creation has no constraints."""
        self.seed_static_data()
        error = validate_form_type_constraints(self.event.id, 'registration')
        self.assertIsNone(error)


class TestEventFormConfigAPI(ApiTestCase):
    """Tests for GET /api/v1/form-config?event_id={event_id}."""

    def seed_static_data(self):
        self.admin = self.add_user('admin@test.com', 'Admin', 'User')
        self.regular_user = self.add_user('user@test.com', 'Regular', 'User')
        self.event = self.add_event()
        self.add_event_role('admin', self.admin.id, self.event.id)
        self.admin_headers = self.get_auth_header_for('admin@test.com')
        self.user_headers = self.get_auth_header_for('user@test.com')
        self.admin = db.session.merge(self.admin)
        self.regular_user = db.session.merge(self.regular_user)
        self.event = db.session.merge(self.event)

    def _use_new_forms(self):
        self.event.uses_new_forms = True
        db.session.commit()

    def _get_form_config(self, event_id=None, headers=None):
        eid = event_id if event_id is not None else self.event.id
        hdrs = headers if headers is not None else self.admin_headers
        return self.app.get(
            '/api/v1/form-config?event_id={}'.format(eid),
            headers=hdrs
        )

    def test_requires_authentication(self):
        """GET /api/v1/form-config returns 403 without auth."""
        self.seed_static_data()
        response = self.app.get(
            '/api/v1/form-config?event_id={}'.format(self.event.id)
        )
        self.assertEqual(response.status_code, 403)

    def test_requires_event_admin(self):
        """GET /api/v1/form-config returns 403 for non-admin user."""
        self.seed_static_data()
        response = self._get_form_config(headers=self.user_headers)
        self.assertEqual(response.status_code, 403)

    def test_all_old_system_when_no_typed_forms(self):
        """Returns old system for all types when no typed forms exist."""
        self.seed_static_data()
        response = self._get_form_config()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['application']['system'], 'old')
        self.assertEqual(data['review']['system'], 'old')
        self.assertEqual(data['registration']['system'], 'old')
        self.assertEqual(data['generic_forms'], [])

    def test_registration_shows_new_when_typed_form_exists(self):
        """Returns new system for registration when Form(form_type='registration') exists."""
        self.seed_static_data()
        self._use_new_forms()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='registration',
            is_open=True
        )
        db.session.add(form)
        db.session.commit()

        response = self._get_form_config()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        reg = data['registration']
        self.assertEqual(reg['system'], 'new')
        self.assertEqual(reg['form_id'], form.id)
        self.assertTrue(reg['is_open'])
        self.assertEqual(reg['response_count'], 0)

    def test_application_shows_new_when_typed_form_exists(self):
        """Returns new system for application when Form(form_type='application') exists."""
        self.seed_static_data()
        self._use_new_forms()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='application',
            is_open=True
        )
        db.session.add(form)
        db.session.commit()

        response = self._get_form_config()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        app_data = data['application']
        self.assertEqual(app_data['system'], 'new')
        self.assertEqual(app_data['form_id'], form.id)

    def test_review_shows_new_with_stages(self):
        """Returns new system for review with stage data when review forms exist."""
        self.seed_static_data()
        self._use_new_forms()
        app_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='application'
        )
        db.session.add(app_form)
        db.session.flush()

        review_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='review',
            stage=1,
            settings={'num_reviews_required': 5}
        )
        db.session.add(review_form)
        db.session.commit()

        response = self._get_form_config()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        rev = data['review']
        self.assertEqual(rev['system'], 'new')
        self.assertEqual(len(rev['stages']), 1)
        self.assertEqual(rev['stages'][0]['stage'], 1)
        self.assertEqual(rev['stages'][0]['num_reviews_required'], 5)

    def test_response_count_reflects_submitted_responses(self):
        """response_count is the count of submitted responses for the form."""
        self.seed_static_data()
        self._use_new_forms()
        form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='registration'
        )
        db.session.add(form)
        db.session.flush()

        # Add 2 submitted and 1 unsubmitted response
        for i in range(2):
            r = FormResponse(form_id=form.id, user_id=self.admin.id)
            r.is_submitted = True
            db.session.add(r)
        unsubmitted = FormResponse(form_id=form.id, user_id=self.admin.id)
        db.session.add(unsubmitted)
        db.session.commit()

        response = self._get_form_config()

        data = json.loads(response.data)
        self.assertEqual(data['registration']['response_count'], 2)

    def test_generic_forms_listed(self):
        """Generic forms (form_type=None) are listed in generic_forms."""
        self.seed_static_data()
        generic = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id
        )
        db.session.add(generic)
        db.session.commit()

        # Add a translation so it has a name
        trans = FormTranslation(
            form_id=generic.id,
            language='en',
            name='Feedback Survey',
            description=''
        )
        db.session.add(trans)
        db.session.commit()

        response = self._get_form_config()

        data = json.loads(response.data)
        self.assertEqual(len(data['generic_forms']), 1)
        self.assertEqual(data['generic_forms'][0]['id'], generic.id)
        self.assertEqual(data['generic_forms'][0]['name'], 'Feedback Survey')

    def test_old_system_with_legacy_registration_form(self):
        """Old system shows legacy_form_id when a legacy RegistrationForm exists."""
        self.seed_static_data()
        legacy_reg = self.create_registration_form(event_id=self.event.id)

        response = self._get_form_config()

        data = json.loads(response.data)
        reg = data['registration']
        self.assertEqual(reg['system'], 'old')
        self.assertEqual(reg['legacy_form_id'], legacy_reg.id)

    def test_old_system_with_legacy_application_form(self):
        """Old system shows legacy_form_id when a legacy ApplicationForm exists."""
        self.seed_static_data()
        legacy_app = self.create_application_form(event_id=self.event.id)

        response = self._get_form_config()

        data = json.loads(response.data)
        app_data = data['application']
        self.assertEqual(app_data['system'], 'old')
        self.assertEqual(app_data['legacy_form_id'], legacy_app.id)
