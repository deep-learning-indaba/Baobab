"""Tests for FormResponseTagAPI and FormReviewSummaryAPI."""
import json
from app import db
from app.forms.models import Form, FormResponse, FormResponseTag, FormTranslation
from app.reviews.models import ReviewerTag
from app.events.models import EventRole
from app.tags.models import Tag, TagTranslation
from app.utils.testing import ApiTestCase


class FormResponseTagAndSummaryTest(ApiTestCase):

    def seed_static_data(self):
        self.admin = self.add_user('admin@test.com', 'Admin', 'User')
        self.reviewer = self.add_user('reviewer@test.com', 'Rev', 'User')
        self.applicant1 = self.add_user('applicant1@test.com', 'App', 'One')
        self.applicant2 = self.add_user('applicant2@test.com', 'App', 'Two')

        self.event = self.add_event(key='testevent2')
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

        self.app_response1 = FormResponse(
            form_id=self.app_form.id, user_id=self.applicant1.id
        )
        self.app_response1.is_submitted = True
        self.app_response2 = FormResponse(
            form_id=self.app_form.id, user_id=self.applicant2.id
        )
        self.app_response2.is_submitted = True
        db.session.add_all([self.app_response1, self.app_response2])
        db.session.flush()

        self.tag = Tag(event_id=self.event.id, tag_type='RESPONSE')
        db.session.add(self.tag)
        db.session.flush()
        db.session.add(TagTranslation(
            tag_id=self.tag.id, language='en', name='ML', description='Machine Learning'
        ))
        db.session.commit()

        # Capture IDs before auth header call
        self.admin_id = self.admin.id
        self.reviewer_id = self.reviewer.id
        self.event_id = self.event.id
        self.app_form_id = self.app_form.id
        self.review_form_id = self.review_form.id
        self.app_response1_id = self.app_response1.id
        self.app_response2_id = self.app_response2.id
        self.tag_id = self.tag.id

        self.admin_headers = self.get_auth_header_for('admin@test.com')

    def _post_tag(self, response_id, tag_id):
        return self.app.post(
            '/api/v1/forms/{}/responses/{}/tags?event_id={}'.format(
                self.app_form_id, response_id, self.event_id
            ),
            headers=self.admin_headers,
            data=json.dumps({'tag_id': tag_id}),
            content_type='application/json'
        )

    def _delete_tag(self, response_id, tag_id):
        return self.app.delete(
            '/api/v1/forms/{}/responses/{}/tags?event_id={}'.format(
                self.app_form_id, response_id, self.event_id
            ),
            headers=self.admin_headers,
            data=json.dumps({'tag_id': tag_id}),
            content_type='application/json'
        )

    def _get_summary(self, tag_ids=None):
        url = '/api/v1/forms/{}/review-summary?event_id={}'.format(
            self.review_form_id, self.event_id
        )
        if tag_ids:
            for tid in tag_ids:
                url += '&tags[]={}'.format(tid)
        return self.app.get(url, headers=self.admin_headers)

    def _assign(self, num_reviews, tag_ids=None, email='reviewer@test.com'):
        return self.app.post(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self.admin_headers,
            data=json.dumps({
                'reviewer_user_email': email,
                'num_reviews': num_reviews,
                'event_id': self.event_id,
                'tag_ids': tag_ids or []
            }),
            content_type='application/json'
        )

    # --- FormResponseTagAPI ---

    def test_add_tag_to_form_response(self):
        """POST adds a FormResponseTag record."""
        self.seed_static_data()

        response = self._post_tag(self.app_response1_id, self.tag_id)

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['tag_id'], self.tag_id)
        self.assertEqual(data['form_response_id'], self.app_response1_id)
        self.assertEqual(data['name'], 'ML')

        tag_in_db = db.session.query(FormResponseTag).filter_by(
            form_response_id=self.app_response1_id, tag_id=self.tag_id
        ).first()
        self.assertIsNotNone(tag_in_db)

    def test_add_duplicate_tag_returns_400(self):
        """POST returns 400 when the tag is already applied."""
        self.seed_static_data()
        self._post_tag(self.app_response1_id, self.tag_id)

        response = self._post_tag(self.app_response1_id, self.tag_id)

        self.assertEqual(response.status_code, 400)

    def test_delete_tag_from_form_response(self):
        """DELETE removes the FormResponseTag record."""
        self.seed_static_data()
        self._post_tag(self.app_response1_id, self.tag_id)

        response = self._delete_tag(self.app_response1_id, self.tag_id)

        self.assertEqual(response.status_code, 200)
        tag_in_db = db.session.query(FormResponseTag).filter_by(
            form_response_id=self.app_response1_id, tag_id=self.tag_id
        ).first()
        self.assertIsNone(tag_in_db)

    def test_add_tag_non_admin_returns_403(self):
        """POST returns 403 for non-admin users."""
        self.seed_static_data()
        reviewer_headers = self.get_auth_header_for('reviewer@test.com')

        response = self.app.post(
            '/api/v1/forms/{}/responses/{}/tags?event_id={}'.format(
                self.app_form_id, self.app_response1_id, self.event_id
            ),
            headers=reviewer_headers,
            data=json.dumps({'tag_id': self.tag_id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)

    # --- FormReviewSummaryAPI ---

    def test_summary_returns_total_unallocated(self):
        """GET returns count of reviews still needed."""
        self.seed_static_data()

        response = self._get_summary()

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # 2 responses * 2 required each = 4 total needed, 0 assigned
        self.assertEqual(data['reviews_unallocated'], 4)

    def test_summary_decreases_after_assignment(self):
        """Unallocated count decreases after assigning reviews."""
        self.seed_static_data()
        self._assign(2)

        response = self._get_summary()

        data = json.loads(response.data)
        # 2 reviews assigned out of 4 total needed
        self.assertEqual(data['reviews_unallocated'], 2)

    def test_summary_filtered_by_tag(self):
        """Summary with tag filter only counts tagged responses."""
        self.seed_static_data()
        # Tag only response1
        self._post_tag(self.app_response1_id, self.tag_id)

        response = self._get_summary(tag_ids=[self.tag_id])

        data = json.loads(response.data)
        # Only 1 tagged response * 2 required = 2 unallocated
        self.assertEqual(data['reviews_unallocated'], 2)

    # --- Tag-filtered assignment ---

    def test_assign_with_tag_filter_only_assigns_tagged_responses(self):
        """POST with tag_ids only assigns reviews for responses with those tags."""
        self.seed_static_data()
        # Only tag response1
        self._post_tag(self.app_response1_id, self.tag_id)

        response = self._assign(5, tag_ids=[self.tag_id])

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        # Only response1 is tagged, so max 1 assignment (num_reviews_required=2, but reviewer only counts once)
        self.assertEqual(data['reviews_assigned'], 1)

        assignments = db.session.query(FormResponse).filter_by(
            form_id=self.review_form_id,
            user_id=self.reviewer_id
        ).all()
        linked_ids = [a.linked_response_id for a in assignments]
        self.assertIn(self.app_response1_id, linked_ids)
        self.assertNotIn(self.app_response2_id, linked_ids)

    def test_assign_adds_reviewer_event_role(self):
        """POST assigns the reviewer EventRole so ReviewerTagAPI can be used."""
        self.seed_static_data()

        self._assign(1)

        role = db.session.query(EventRole).filter_by(
            role='reviewer', user_id=self.reviewer_id, event_id=self.event_id
        ).first()
        self.assertIsNotNone(role)

    def test_get_assignments_includes_reviewer_tags(self):
        """GET returns reviewer tags in the response."""
        self.seed_static_data()
        self._assign(1)

        # Add a reviewer tag (reviewer now has the role)
        reviewer_tag = ReviewerTag(
            reviewer_user_id=self.reviewer_id,
            tag_id=self.tag_id,
            event_id=self.event_id
        )
        db.session.add(reviewer_tag)
        db.session.commit()

        result = self.app.get(
            '/api/v1/forms/{}/review-assignments?event_id={}'.format(
                self.review_form_id, self.event_id
            ),
            headers=self.admin_headers
        )

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]['tags']), 1)
        self.assertEqual(data[0]['tags'][0]['name'], 'ML')
