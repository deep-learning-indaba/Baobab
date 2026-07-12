"""Tests for FormReviewAssignmentAPI - review assignment via FormResponse."""
import json
from app import db
from app.forms.models import Form, FormSection, FormQuestion, FormResponse, FormAnswer, FormTranslation
from app.utils.testing import ApiTestCase


class FormReviewAssignmentAPITest(ApiTestCase):

    def seed_static_data(self):
        self.admin = self.add_user('admin@test.com', 'Admin', 'User')
        self.reviewer = self.add_user('reviewer@test.com', 'Rev', 'User')
        self.applicant1 = self.add_user('applicant1@test.com', 'App', 'One')
        self.applicant2 = self.add_user('applicant2@test.com', 'App', 'Two')
        self.applicant3 = self.add_user('applicant3@test.com', 'App', 'Three')

        self.event = self.add_event(key='testevent')
        self.add_event_role('admin', self.admin.id, self.event.id)
        self.add_email_template('reviews-assigned')

        self.app_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='application',
            multiple_responses=False,
            is_open=True
        )
        db.session.add(self.app_form)
        db.session.flush()

        self.review_form = Form(
            event_id=self.event.id,
            created_by_user_id=self.admin.id,
            form_type='review',
            multiple_responses=True,
            linked_form_id=self.app_form.id,
            settings={'num_reviews_required': 2},
            is_open=True
        )
        db.session.add(self.review_form)
        db.session.flush()

        db.session.add(FormTranslation(
            form_id=self.review_form.id, language='en', name='Review Form'
        ))

        section = FormSection(form_id=self.review_form.id, order=1, key='review-section')
        db.session.add(section)
        db.session.flush()
        self.review_question = FormQuestion(
            form_id=self.review_form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            key='review_q'
        )
        db.session.add(self.review_question)
        db.session.flush()

        self.app_response1 = FormResponse(
            form_id=self.app_form.id, user_id=self.applicant1.id
        )
        self.app_response1.is_submitted = True
        self.app_response2 = FormResponse(
            form_id=self.app_form.id, user_id=self.applicant2.id
        )
        self.app_response2.is_submitted = True
        self.app_response3 = FormResponse(
            form_id=self.app_form.id, user_id=self.applicant3.id
        )
        self.app_response3.is_submitted = True

        db.session.add_all([self.app_response1, self.app_response2, self.app_response3])
        db.session.commit()

        # Access IDs now to load them into __dict__ before get_auth_header_for()
        # removes the session, which would otherwise cause DetachedInstanceError.
        self.reviewer_id = self.reviewer.id
        self.review_form_id = self.review_form.id
        self.app_form_id = self.app_form.id
        self.applicant1_id = self.applicant1.id
        self.applicant2_id = self.applicant2.id
        self.applicant3_id = self.applicant3.id
        self.event_id = self.event.id
        self.review_question_id = self.review_question.id

        self.admin_headers = self.get_auth_header_for('admin@test.com')

    def _admin_headers(self):
        return self.admin_headers

    def _post_assign(self, num_reviews, email='reviewer@test.com'):
        return self.app.post(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self._admin_headers(),
            data=json.dumps({
                'reviewer_user_email': email,
                'num_reviews': num_reviews,
                'event_id': self.event_id
            }),
            content_type='application/json'
        )

    def _delete_assign(self, num_reviews, email='reviewer@test.com'):
        return self.app.delete(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self._admin_headers(),
            data=json.dumps({
                'reviewer_user_email': email,
                'num_reviews': num_reviews,
                'event_id': self.event_id
            }),
            content_type='application/json'
        )

    def _get_assignments(self):
        return self.app.get(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self._admin_headers()
        )

    def test_assign_reviews_creates_form_responses(self):
        """POST assigns N reviews by creating FormResponse records."""
        self.seed_static_data()

        response = self._post_assign(2)

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['reviews_assigned'], 2)

        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        self.assertEqual(len(assignments), 2)

    def test_assign_does_not_exceed_num_reviews_required(self):
        """Responses already at num_reviews_required are not assigned again."""
        self.seed_static_data()

        # Fill both slots for app_response1
        for i in range(2):
            other_reviewer = self.add_user(
                'other{}@test.com'.format(i), 'Other', 'User'
            )
            other_reviewer_id = other_reviewer.id
            full = FormResponse(
                form_id=self.review_form_id,
                user_id=other_reviewer_id,
                linked_response_id=self.applicant1_id
            )
            db.session.add(full)
        db.session.commit()

        response = self._post_assign(3)

        self.assertEqual(response.status_code, 201)
        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        linked_ids = [a.linked_response_id for a in assignments]
        self.assertNotIn(self.applicant1_id, linked_ids)

    def test_reviewer_not_assigned_to_own_response(self):
        """A reviewer is not assigned to review their own application."""
        self.seed_static_data()

        own_response = FormResponse(
            form_id=self.app_form_id,
            user_id=self.reviewer_id
        )
        own_response.is_submitted = True
        db.session.add(own_response)
        db.session.commit()
        own_response_id = own_response.id

        response = self._post_assign(10)

        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        linked_ids = [a.linked_response_id for a in assignments]
        self.assertNotIn(own_response_id, linked_ids)

    def test_reviewer_not_double_assigned(self):
        """Assigning again does not create duplicate assignments for same response."""
        self.seed_static_data()
        self._post_assign(2)

        response = self._post_assign(2)

        self.assertEqual(response.status_code, 201)
        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        # Only 1 remaining unassigned (3 total, 2 already taken)
        self.assertEqual(len(assignments), 3)

    def test_assign_ignores_unsubmitted_application_responses(self):
        """Unsubmitted application responses are not assigned."""
        self.seed_static_data()

        new_user_id = self.add_user('new@test.com', 'N', 'U').id
        unsubmitted = FormResponse(
            form_id=self.app_form_id,
            user_id=new_user_id
        )
        db.session.add(unsubmitted)
        db.session.commit()
        unsubmitted_id = unsubmitted.id

        response = self._post_assign(10)

        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        linked_ids = [a.linked_response_id for a in assignments]
        self.assertNotIn(unsubmitted_id, linked_ids)

    def test_delete_removes_unstarted_assignments(self):
        """DELETE removes unstarted (no answers) assignments."""
        self.seed_static_data()
        self._post_assign(3)

        response = self._delete_assign(2)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['num_deleted'], 2)

        remaining = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        self.assertEqual(len(remaining), 1)

    def test_delete_does_not_remove_started_assignments(self):
        """DELETE leaves assignments that have answers (reviewer has started)."""
        self.seed_static_data()
        self._post_assign(2)

        assignment = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).first()
        answer = FormAnswer(
            response_id=assignment.id,
            question_id=self.review_question_id,
            value='some answer'
        )
        db.session.add(answer)
        db.session.commit()

        response = self._delete_assign(2)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['num_deleted'], 1)

    def test_get_returns_reviewer_allocation_counts(self):
        """GET returns per-reviewer allocated and completed counts."""
        self.seed_static_data()
        self._post_assign(2)

        response = self._get_assignments()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        reviewer_data = data[0]
        self.assertEqual(reviewer_data['email'], 'reviewer@test.com')
        self.assertEqual(reviewer_data['reviews_allocated'], 2)
        self.assertEqual(reviewer_data['reviews_completed'], 0)

    def test_get_counts_submitted_as_completed(self):
        """GET counts submitted FormResponses as reviews_completed."""
        self.seed_static_data()
        self._post_assign(2)

        assignment = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).first()
        assignment.is_submitted = True
        db.session.commit()

        response = self._get_assignments()

        data = json.loads(response.data)
        self.assertEqual(data[0]['reviews_allocated'], 2)
        self.assertEqual(data[0]['reviews_completed'], 1)

    def test_post_returns_forbidden_for_non_admin(self):
        """POST returns 403 for non-admin users."""
        self.seed_static_data()

        response = self.app.post(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self.get_auth_header_for('reviewer@test.com'),
            data=json.dumps({
                'reviewer_user_email': 'reviewer@test.com',
                'num_reviews': 1,
                'event_id': self.event_id
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)
