"""Event.uses_new_forms and the application / review / registration flows it
switches onto the generic form system."""
import json
from datetime import datetime

from app import db
from app.events.models import Event, EventRole
from app.events.status import get_event_status
from app.forms import system as form_system
from app.forms.mixins import apply_form_type_defaults
from app.forms.models import (
    Form, FormAnswer, FormQuestion, FormResponse, FormSection, FormTranslation,
    FormQuestionTranslation,
)
from app.outbox.models import OutboxMessage
from app.utils.testing import ApiTestCase


class NewFormSystemTestCase(ApiTestCase):
    """Builds an event on the new form system with an application form (one
    'review-identifier' question and a 'travel_grant' question), a stage-1
    review form with one weighted score question, and a registration form."""

    uses_new_forms = True

    def setUp(self):
        super().setUp()
        self.admin = self.add_user('admin@test.com', 'Admin', 'User')
        self.reviewer = self.add_user('reviewer@test.com', 'Rev', 'Iewer')
        self.applicant = self.add_user('applicant@test.com', 'App', 'Licant')
        self.applicant2 = self.add_user('applicant2@test.com', 'Second', 'Applicant')
        self.event = self.add_event(key='NEWFORMS', uses_new_forms=self.uses_new_forms)
        self.add_event_role('admin', self.admin.id, self.event.id)
        self.add_event_role('reviewer', self.reviewer.id, self.event.id)
        for key in ('application-submitted', 'withdrawal', 'registration-received',
                    'registration-confirmed', 'reviews-assigned', 'offer-paid'):
            self.add_email_template(key, subject=key)

        self.app_form = self._form('application', 'Application')
        app_section = self._section(self.app_form)
        self.identifier_q = self._question(self.app_form, app_section, 'short-text', 'Project title',
                                           key='review-identifier')
        self.travel_q = self._question(self.app_form, app_section, 'short-text', 'Travel', key='travel_grant',
                                       is_required=False)

        self.review_form = self._form('review', 'Review', stage=1, linked_form_id=self.app_form.id,
                                      multiple_responses=True, settings={'num_reviews_required': 2})
        review_section = self._section(self.review_form)
        self.score_q = self._question(self.review_form, review_section, 'numeric', 'Quality',
                                      settings={'weight': 2})
        self.comment_q = self._question(self.review_form, review_section, 'long-text', 'Comments',
                                        is_required=False)

        self.reg_form = self._form('registration', 'Registration')
        reg_section = self._section(self.reg_form)
        self.diet_q = self._question(self.reg_form, reg_section, 'short-text', 'Dietary needs')
        db.session.commit()

        self.admin_id = self.admin.id
        self.reviewer_id = self.reviewer.id
        self.applicant_id = self.applicant.id
        self.applicant2_id = self.applicant2.id
        self.event_id = self.event.id
        self.app_form_id = self.app_form.id
        self.review_form_id = self.review_form.id
        self.reg_form_id = self.reg_form.id
        self.identifier_q_id = self.identifier_q.id
        self.travel_q_id = self.travel_q.id
        self.score_q_id = self.score_q.id
        self.comment_q_id = self.comment_q.id
        self.diet_q_id = self.diet_q.id

    # --- builders -------------------------------------------------------

    def _form(self, form_type, name, **kwargs):
        form = Form(event_id=self.event.id, created_by_user_id=self.admin.id,
                    form_type=form_type, is_open=True, **kwargs)
        db.session.add(form)
        db.session.flush()
        db.session.add(FormTranslation(form_id=form.id, language='en', name=name))
        return form

    def _section(self, form):
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        return section

    def _question(self, form, section, question_type, headline, key=None, is_required=True, settings=None):
        question = FormQuestion(form_id=form.id, section_id=section.id, order=len(form.questions) + 1,
                                question_type=question_type, key=key, is_required=is_required,
                                settings=settings)
        db.session.add(question)
        db.session.flush()
        db.session.add(FormQuestionTranslation(form_question_id=question.id, language='en',
                                               headline=headline))
        return question

    def _response(self, form_id, user_id, answers=None, submitted=False, linked_response_id=None):
        response = FormResponse(form_id=form_id, user_id=user_id, linked_response_id=linked_response_id)
        db.session.add(response)
        db.session.flush()
        for question_id, value in (answers or {}).items():
            db.session.add(FormAnswer(response_id=response.id, question_id=question_id, value=value))
        if submitted:
            response.is_submitted = True
            response.submitted_timestamp = datetime.now()
        db.session.commit()
        return response.id

    def _application(self, user_id, title='My project', submitted=True, travel=None):
        answers = {self.identifier_q_id: title}
        if travel:
            answers[self.travel_q_id] = travel
        return self._response(self.app_form_id, user_id, answers, submitted=submitted)

    # --- requests -------------------------------------------------------

    def _json(self, method, url, email, body=None):
        headers = self.get_auth_header_for(email)
        kwargs = {'headers': headers}
        if body is not None:
            kwargs['data'] = json.dumps(body)
            kwargs['content_type'] = 'application/json'
        response = getattr(self.app, method)(url, **kwargs)
        return response, json.loads(response.data) if response.data else None

    def _emails(self, subject):
        return db.session.query(OutboxMessage).filter_by(channel='email', subject=subject).all()


class SystemSelectionTest(NewFormSystemTestCase):

    def test_new_events_default_to_new_forms(self):
        event = Event({'en': 'E'}, {'en': 'D'}, None, None, 'DEFAULTNEW', 1, 'a@b.c', 'url',
                      None, None, None, None, None, None, None, None, None, None,
                      self.event.event_type, False)
        self.assertTrue(event.uses_new_forms)

    def test_typed_forms_ignored_when_event_is_legacy(self):
        event = db.session.query(Event).get(self.event_id)
        event.uses_new_forms = False
        db.session.commit()
        self.assertIsNone(form_system.get_application_form(self.event_id))
        self.assertIsNone(form_system.get_active_review_form(self.event_id))
        self.assertIsNone(form_system.get_registration_form(self.event_id))

    def test_typed_forms_found_when_event_is_new(self):
        self.assertEqual(form_system.get_application_form(self.event_id).id, self.app_form_id)
        self.assertEqual(form_system.get_active_review_form(self.event_id).id, self.review_form_id)
        self.assertEqual(form_system.get_registration_form(self.event_id).id, self.reg_form_id)

    def test_event_info_exposes_flag_and_form_ids(self):
        response, data = self._json('get', '/api/v1/event-by-key?event_key=NEWFORMS&language=en',
                                    'applicant@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['uses_new_forms'])
        self.assertEqual(data['application_form_id'], self.app_form_id)
        self.assertEqual(data['review_form_id'], self.review_form_id)

    def test_typed_form_unavailable_to_respondents_on_legacy_event(self):
        event = db.session.query(Event).get(self.event_id)
        event.uses_new_forms = False
        db.session.commit()
        response, _ = self._json('post', '/api/v1/forms/{}/responses'.format(self.app_form_id),
                                 'applicant@test.com', {'answers': []})
        self.assertEqual(response.status_code, 404)

    def test_form_config_put_toggles_flag(self):
        response, data = self._json('put', '/api/v1/form-config', 'admin@test.com',
                                    {'event_id': self.event_id, 'uses_new_forms': False})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['uses_new_forms'])
        _, config = self._json('get', '/api/v1/form-config?event_id={}'.format(self.event_id), 'admin@test.com')
        self.assertFalse(config['uses_new_forms'])
        self.assertEqual(config['application']['system'], 'old')

    def test_form_config_put_requires_admin(self):
        response, _ = self._json('put', '/api/v1/form-config', 'applicant@test.com',
                                 {'event_id': self.event_id, 'uses_new_forms': False})
        self.assertEqual(response.status_code, 403)


class ReviewStageTest(NewFormSystemTestCase):

    def test_new_review_form_is_linked_to_application_form(self):
        form = Form(event_id=self.event_id, created_by_user_id=self.admin_id, form_type='review')
        apply_form_type_defaults(form, 'review', stage=2)
        self.assertEqual(form.linked_form_id, self.app_form_id)

    def test_new_stage_is_inactive_while_another_stage_is_active(self):
        form = Form(event_id=self.event_id, created_by_user_id=self.admin_id, form_type='review')
        apply_form_type_defaults(form, 'review', stage=2)
        self.assertFalse(form.is_active)

    def test_stage_api_switches_active_stage(self):
        stage2 = Form(event_id=self.event_id, created_by_user_id=self.admin_id, form_type='review',
                      stage=2, is_active=False, linked_form_id=self.app_form_id)
        db.session.add(stage2)
        db.session.commit()
        stage2_id = stage2.id

        response, data = self._json('put', '/api/v1/review-stages', 'admin@test.com',
                                    {'event_id': self.event_id, 'stage': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['current_stage'], 2)
        self.assertEqual(form_system.get_active_review_form(self.event_id).id, stage2_id)
        self.assertEqual([s['is_active'] for s in data['stages']], [False, True])

    def test_stage_api_unknown_stage(self):
        response, _ = self._json('put', '/api/v1/review-stages', 'admin@test.com',
                                 {'event_id': self.event_id, 'stage': 9})
        self.assertEqual(response.status_code, 404)


class ApplicationLifecycleTest(NewFormSystemTestCase):

    def _submit(self, response_id):
        return self._json('post', '/api/v1/forms/{}/responses/{}/submit'.format(self.app_form_id, response_id),
                          'applicant@test.com')

    def _withdraw(self, response_id):
        return self._json('post', '/api/v1/forms/{}/responses/{}/withdraw'.format(self.app_form_id, response_id),
                          'applicant@test.com')

    def test_withdrawn_application_reports_withdrawn(self):
        response_id = self._application(self.applicant_id)
        response, data = self._withdraw(response_id)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['is_submitted'])
        self.assertEqual(get_event_status(self.event_id, self.applicant_id).application_status, 'Withdrawn')

    def test_resubmitting_clears_withdrawal(self):
        response_id = self._application(self.applicant_id)
        self._withdraw(response_id)
        response, data = self._submit(response_id)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['is_submitted'])
        self.assertFalse(data['is_withdrawn'])
        self.assertEqual(get_event_status(self.event_id, self.applicant_id).application_status, 'Submitted')

    def test_submit_and_withdraw_send_emails(self):
        response_id = self._application(self.applicant_id, submitted=False)
        self._submit(response_id)
        self.assertEqual(len(self._emails('application-submitted')), 1)
        self._withdraw(response_id)
        self.assertEqual(len(self._emails('withdrawal')), 1)

    def test_admin_status_update_keeps_flags_exclusive(self):
        response_id = self._application(self.applicant_id)
        url = '/api/v1/forms/{}/responses/{}/admin-status?event_id={}'.format(
            self.app_form_id, response_id, self.event_id)
        response, data = self._json('patch', url, 'admin@test.com', {'is_withdrawn': True})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(data['is_submitted'])
        response, data = self._json('patch', url, 'admin@test.com', {'is_submitted': True})
        self.assertFalse(data['is_withdrawn'])


class OfferTest(NewFormSystemTestCase):

    def test_applicant_can_view_offer(self):
        self._application(self.applicant_id, travel='Travel')
        self.add_offer(self.applicant_id, event_id=self.event_id)
        response, data = self._json('get', '/api/v1/offer?event_id={}'.format(self.event_id), 'applicant@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['requested_travel'])
        self.assertFalse(data['requested_accommodation'])

    def test_offer_requires_submitted_application(self):
        self._application(self.applicant_id, submitted=False)
        self.add_offer(self.applicant_id, event_id=self.event_id)
        response, _ = self._json('get', '/api/v1/offer?event_id={}'.format(self.event_id), 'applicant@test.com')
        self.assertEqual(response.status_code, 404)


class RegistrationTest(NewFormSystemTestCase):

    def _register(self, email='applicant@test.com'):
        response, data = self._json('post', '/api/v1/forms/{}/responses'.format(self.reg_form_id), email,
                                    {'answers': [{'question_id': self.diet_q_id, 'value': 'None'}]})
        if response.status_code != 201:
            return response, data
        return self._json('post', '/api/v1/forms/{}/responses/{}/submit'.format(self.reg_form_id, data['id']),
                          email)

    def test_only_accepted_offers_can_register(self):
        self._application(self.applicant_id)
        self.add_offer(self.applicant_id, event_id=self.event_id, candidate_response=None)
        response, _ = self._register()
        self.assertEqual(response.status_code, 403)

    def test_unpaid_registration_is_not_confirmed(self):
        self._application(self.applicant_id)
        self.add_offer(self.applicant_id, event_id=self.event_id, candidate_response=True, payment_required=True)
        response, _ = self._register()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_event_status(self.event_id, self.applicant_id).registration_status, 'Not Confirmed')
        self.assertEqual(len(self._emails('registration-received')), 1)

    def test_registration_confirmed_when_no_payment_required(self):
        self._application(self.applicant_id)
        self.add_offer(self.applicant_id, event_id=self.event_id, candidate_response=True, payment_required=False)
        self._register()
        self.assertEqual(get_event_status(self.event_id, self.applicant_id).registration_status, 'Confirmed')

    def test_invited_guest_registration_confirmed(self):
        guest = self.add_user('guest@test.com')
        guest_id = guest.id
        self.add_invited_guest(guest_id, event_id=self.event_id)
        response, _ = self._register('guest@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_event_status(self.event_id, guest_id).registration_status, 'Confirmed')

    def test_registration_status_empty_before_registering(self):
        self._application(self.applicant_id)
        self.add_offer(self.applicant_id, event_id=self.event_id, candidate_response=True)
        self.assertIsNone(get_event_status(self.event_id, self.applicant_id).registration_status)


class ReviewAccessTest(NewFormSystemTestCase):

    def test_reviews_cannot_be_created_directly(self):
        app_response_id = self._application(self.applicant_id)
        response, _ = self._json('post', '/api/v1/forms/{}/responses'.format(self.review_form_id),
                                 'reviewer@test.com',
                                 {'answers': [], 'linked_response_id': app_response_id})
        self.assertEqual(response.status_code, 403)

    def test_assigning_single_reviewer_grants_role_and_emails(self):
        app_response_id = self._application(self.applicant_id)
        new_reviewer = self.add_user('newreviewer@test.com')
        new_reviewer_id = new_reviewer.id
        url = '/api/v1/forms/{}/responses/{}/reviews?event_id={}'.format(
            self.app_form_id, app_response_id, self.event_id)
        response, _ = self._json('post', url, 'admin@test.com', {'reviewer_email': 'newreviewer@test.com'})
        self.assertEqual(response.status_code, 201)
        role = db.session.query(EventRole).filter_by(
            user_id=new_reviewer_id, event_id=self.event_id, role='reviewer').first()
        self.assertIsNotNone(role)
        self.assertEqual(len(self._emails('reviews-assigned')), 1)

    def test_applicant_cannot_be_assigned_own_application(self):
        app_response_id = self._application(self.applicant_id)
        url = '/api/v1/forms/{}/responses/{}/reviews?event_id={}'.format(
            self.app_form_id, app_response_id, self.event_id)
        response, _ = self._json('post', url, 'admin@test.com', {'reviewer_email': 'applicant@test.com'})
        self.assertEqual(response.status_code, 400)


class ReviewerFlowTest(NewFormSystemTestCase):

    def _assign(self, app_response_id, reviewer_id=None):
        return self._response(self.review_form_id, reviewer_id or self.reviewer_id,
                              linked_response_id=app_response_id)

    def test_assigned_list(self):
        first = self._assign(self._application(self.applicant_id, title='Alpha'))
        self._assign(self._application(self.applicant2_id, title='Beta'))
        db.session.add(FormAnswer(response_id=first, question_id=self.score_q_id, value='4'))
        db.session.commit()

        response, data = self._json('get', '/api/v1/reviews/assigned?event_id={}'.format(self.event_id),
                                    'reviewer@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['counts'], {'total': 2, 'submitted': 0, 'remaining': 2})
        self.assertEqual([a['status'] for a in data['assignments']], ['in_progress', 'not_started'])
        self.assertEqual(data['assignments'][0]['identifiers'][0]['value'], 'Alpha')
        self.assertEqual(data['assignments'][0]['total_score'], 8.0)

    def test_withdrawn_applications_leave_the_queue(self):
        app_response_id = self._application(self.applicant_id)
        self._assign(app_response_id)
        application = db.session.query(FormResponse).get(app_response_id)
        application.is_submitted = False
        application.is_withdrawn = True
        db.session.commit()
        _, data = self._json('get', '/api/v1/reviews/assigned?event_id={}'.format(self.event_id),
                             'reviewer@test.com')
        self.assertEqual(data['counts']['total'], 0)

    def test_assigned_list_requires_reviewer(self):
        response, _ = self._json('get', '/api/v1/reviews/assigned?event_id={}'.format(self.event_id),
                                 'applicant@test.com')
        self.assertEqual(response.status_code, 403)

    def test_assigned_list_unavailable_on_legacy_event(self):
        event = db.session.query(Event).get(self.event_id)
        event.uses_new_forms = False
        db.session.commit()
        response, _ = self._json('get', '/api/v1/reviews/assigned?event_id={}'.format(self.event_id),
                                 'reviewer@test.com')
        self.assertEqual(response.status_code, 404)

    def test_detail_includes_application_and_navigation(self):
        first = self._assign(self._application(self.applicant_id, title='Alpha'))
        second = self._assign(self._application(self.applicant2_id, title='Beta'))
        response, data = self._json(
            'get', '/api/v1/reviews/assigned/{}?event_id={}'.format(first, self.event_id), 'reviewer@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['application_form']['id'], self.app_form_id)
        self.assertEqual(data['review_form']['id'], self.review_form_id)
        self.assertNotIn('tags', data['application_response'])
        self.assertEqual(data['navigation'], {
            'position': 1, 'total': 2, 'remaining': 2, 'next_review_response_id': second,
        })

    def test_detail_skip_wraps_round(self):
        first = self._assign(self._application(self.applicant_id))
        second = self._assign(self._application(self.applicant2_id))
        _, data = self._json(
            'get', '/api/v1/reviews/assigned/{}?event_id={}'.format(second, self.event_id), 'reviewer@test.com')
        self.assertEqual(data['navigation']['next_review_response_id'], first)

    def test_detail_of_another_reviewers_review_is_not_found(self):
        other = self.add_user('other@test.com')
        review_id = self._assign(self._application(self.applicant_id), reviewer_id=other.id)
        response, _ = self._json(
            'get', '/api/v1/reviews/assigned/{}?event_id={}'.format(review_id, self.event_id), 'reviewer@test.com')
        self.assertEqual(response.status_code, 404)

    def test_reviewer_saves_and_submits_through_response_endpoints(self):
        review_id = self._assign(self._application(self.applicant_id))
        response, _ = self._json('put', '/api/v1/forms/{}/responses'.format(self.review_form_id),
                                 'reviewer@test.com',
                                 {'response_id': review_id,
                                  'answers': [{'question_id': self.score_q_id, 'value': '3'}]})
        self.assertEqual(response.status_code, 200)
        response, _ = self._json(
            'post', '/api/v1/forms/{}/responses/{}/submit'.format(self.review_form_id, review_id),
            'reviewer@test.com')
        self.assertEqual(response.status_code, 200)

        _, history = self._json('get', '/api/v1/reviews/history?event_id={}'.format(self.event_id),
                                'reviewer@test.com')
        self.assertEqual(history['num_entries'], 1)
        self.assertEqual(history['reviews'][0]['review_response_id'], review_id)
        self.assertEqual(history['reviews'][0]['total_score'], 6.0)


class ReviewDashboardTest(NewFormSystemTestCase):

    def test_dashboard_reviews_and_averages(self):
        app_response_id = self._application(self.applicant_id, title='Alpha')
        self._application(self.applicant2_id, title='Beta')
        second_reviewer = self.add_user('reviewer2@test.com')
        self._response(self.review_form_id, self.reviewer_id, {self.score_q_id: '4', self.comment_q_id: 'Good'},
                       submitted=True, linked_response_id=app_response_id)
        self._response(self.review_form_id, second_reviewer.id, {self.score_q_id: '2'},
                       submitted=True, linked_response_id=app_response_id)

        response, data = self._json(
            'get', '/api/v1/forms/{}/review-dashboard?event_id={}'.format(self.review_form_id, self.event_id),
            'admin@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['num_reviews_required'], 2)
        self.assertEqual([q['question_id'] for q in data['score_questions']], [self.score_q_id])
        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['reviews'][0]['answers'][1]['display_value'], 'Good')

        alpha = next(a for a in data['applications'] if a['application_response_id'] == app_response_id)
        self.assertEqual(alpha['reviews_submitted'], 2)
        self.assertEqual(alpha['average_scores'][str(self.score_q_id)], 3.0)
        self.assertEqual(alpha['average_total'], 6.0)
        beta = next(a for a in data['applications'] if a['application_response_id'] != app_response_id)
        self.assertEqual(beta['reviews_submitted'], 0)
        self.assertIsNone(beta['average_total'])

    def test_dashboard_requires_admin(self):
        response, _ = self._json(
            'get', '/api/v1/forms/{}/review-dashboard?event_id={}'.format(self.review_form_id, self.event_id),
            'reviewer@test.com')
        self.assertEqual(response.status_code, 403)

    def test_application_reviewers_include_answers(self):
        app_response_id = self._application(self.applicant_id)
        self._response(self.review_form_id, self.reviewer_id, {self.score_q_id: '5'},
                       submitted=True, linked_response_id=app_response_id)
        response, data = self._json(
            'get', '/api/v1/forms/{}/responses/{}/reviews?event_id={}'.format(
                self.app_form_id, app_response_id, self.event_id), 'admin@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['status'], 'submitted')
        self.assertEqual(data[0]['total_score'], 10.0)
        self.assertEqual(data[0]['answers'][0]['value'], '5')


class LinkedDisplayTest(NewFormSystemTestCase):
    """settings['linked_display'] on the review form hides application answers
    from the reviewer, server-side."""

    def setUp(self):
        super().setUp()
        app_form = db.session.query(Form).get(self.app_form_id)
        personal = FormSection(form_id=self.app_form_id, order=2)
        db.session.add(personal)
        db.session.flush()
        self.personal_section_id = personal.id
        self.app_section_id = db.session.query(FormQuestion).get(self.identifier_q_id).section_id
        self.name_q_id = self._question(app_form, personal, 'short-text', 'Full name').id
        db.session.commit()

    def _set_display(self, display):
        review_form = db.session.query(Form).get(self.review_form_id)
        review_form.settings = {**(review_form.settings or {}), 'linked_display': display}
        db.session.commit()

    def _detail(self):
        app_response_id = self._response(
            self.app_form_id, self.applicant_id,
            {self.identifier_q_id: 'Alpha', self.travel_q_id: 'Yes', self.name_q_id: 'Ada Lovelace'},
            submitted=True)
        review_id = self._response(self.review_form_id, self.reviewer_id, linked_response_id=app_response_id)
        response, data = self._json(
            'get', '/api/v1/reviews/assigned/{}?event_id={}'.format(review_id, self.event_id), 'reviewer@test.com')
        self.assertEqual(response.status_code, 200)
        return data

    @staticmethod
    def _question_ids(data):
        return {q['id'] for s in data['application_form']['sections'] for q in s['questions']}

    @staticmethod
    def _answer_ids(data, key='answers'):
        return {a['question_id'] for a in data['application_response'][key]}

    def test_everything_shown_without_setting(self):
        data = self._detail()
        expected = {self.identifier_q_id, self.travel_q_id, self.name_q_id}
        self.assertEqual(self._question_ids(data), expected)
        self.assertEqual(self._answer_ids(data), expected)
        self.assertEqual(data['application_response']['dependency_answers'], [])

    def test_hidden_section_removes_its_questions_and_answers(self):
        self._set_display({'hidden_section_ids': [self.personal_section_id], 'hidden_question_ids': []})
        data = self._detail()
        self.assertEqual(self._question_ids(data), {self.identifier_q_id, self.travel_q_id})
        self.assertEqual(self._answer_ids(data), {self.identifier_q_id, self.travel_q_id})
        self.assertEqual(len(data['application_form']['sections']), 1)
        self.assertNotIn('Ada Lovelace', json.dumps(data))

    def test_hidden_section_hides_questions_added_later(self):
        self._set_display({'hidden_section_ids': [self.personal_section_id], 'hidden_question_ids': []})
        app_form = db.session.query(Form).get(self.app_form_id)
        personal = db.session.query(FormSection).get(self.personal_section_id)
        later_q_id = self._question(app_form, personal, 'short-text', 'Gender').id
        db.session.commit()
        data = self._detail()
        self.assertNotIn(later_q_id, self._question_ids(data))

    def test_hidden_question_leaves_its_siblings(self):
        self._set_display({'hidden_section_ids': [], 'hidden_question_ids': [self.travel_q_id]})
        data = self._detail()
        self.assertEqual(self._question_ids(data), {self.identifier_q_id, self.name_q_id})
        self.assertEqual(self._answer_ids(data), {self.identifier_q_id, self.name_q_id})

    def test_hidden_answer_used_by_a_dependency_is_sent_separately(self):
        comment_q = db.session.query(FormQuestion).get(self.comment_q_id)
        comment_q.dependency_expression = {
            'operator': 'AND',
            'conditions': [{'question_id': self.travel_q_id, 'operator': 'EQUALS', 'values': ['Yes']}],
        }
        db.session.commit()
        self._set_display({'hidden_section_ids': [self.personal_section_id],
                           'hidden_question_ids': [self.travel_q_id]})
        data = self._detail()
        self.assertNotIn(self.travel_q_id, self._question_ids(data))
        self.assertNotIn(self.travel_q_id, self._answer_ids(data))
        # The hidden name answer isn't referenced by any dependency, so stays out.
        self.assertEqual(self._answer_ids(data, 'dependency_answers'), {self.travel_q_id})

    def test_malformed_setting_is_rejected(self):
        for settings in ({'linked_display': []},
                         {'linked_display': {'hidden_question_ids': 'all'}},
                         {'linked_display': {'hidden_section_ids': [True]}}):
            response, _ = self._json('put', '/api/v1/forms/{}'.format(self.review_form_id),
                                     'admin@test.com', {'settings': settings})
            self.assertEqual(response.status_code, 400, settings)
            response, _ = self._json('put', '/api/v1/forms/{}/structure'.format(self.review_form_id),
                                     'admin@test.com', {'settings': settings})
            self.assertEqual(response.status_code, 400, settings)

    def test_valid_setting_is_saved(self):
        display = {'hidden_section_ids': [self.personal_section_id], 'hidden_question_ids': [999999]}
        response, data = self._json('put', '/api/v1/forms/{}'.format(self.review_form_id),
                                    'admin@test.com', {'settings': {'linked_display': display}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['settings']['linked_display'], display)


class EventStatsTest(NewFormSystemTestCase):

    def test_stats_count_new_form_responses(self):
        app_response_id = self._application(self.applicant_id)
        self._application(self.applicant2_id, submitted=False)
        self._response(self.review_form_id, self.reviewer_id, {self.score_q_id: '5'},
                       submitted=True, linked_response_id=app_response_id)

        response, data = self._json('get', '/api/v1/eventstats?event_id={}'.format(self.event_id),
                                    'admin@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['num_responses'], 2)
        self.assertEqual(data['num_submitted_responses'], 1)
        self.assertEqual(data['reviews_completed'], 1)
        # One submitted application needing two reviews, one assigned.
        self.assertEqual(data['reviews_unallocated'], 1)
