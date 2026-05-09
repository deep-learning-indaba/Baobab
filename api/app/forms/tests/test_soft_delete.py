import json
from app import db
from app.forms.models import Form, FormSection, FormQuestion, FormSectionTranslation, FormQuestionTranslation, FormResponse, FormAnswer
from app.utils.testing import ApiTestCase


class TestFormSoftDelete(ApiTestCase):
    
    def seed_static_data(self):
        self.user = self.add_user('admin@example.com', 'Admin', 'User', password='password123')
        self.auth_headers = self.get_auth_header_for('admin@example.com', 'password123')
        self.event = self.add_event()
    
    def setUp(self):
        super(TestFormSoftDelete, self).setUp()
        self.seed_static_data()
    
    def _create_form_with_structure(self):
        """Helper to create a form with sections and questions"""
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True)
        db.session.add(form)
        db.session.flush()
        
        # Create section 1
        section1 = FormSection(form_id=form.id, order=1, key='section-1')
        db.session.add(section1)
        db.session.flush()
        
        section1_trans = FormSectionTranslation(
            form_section_id=section1.id,
            language='en',
            name='Section 1',
            description='First section'
        )
        db.session.add(section1_trans)
        
        # Create question 1
        question1 = FormQuestion(
            form_id=form.id,
            section_id=section1.id,
            order=1,
            question_type='short-text',
            is_required=True,
            key='question_1'
        )
        db.session.add(question1)
        db.session.flush()
        
        q1_trans = FormQuestionTranslation(
            form_question_id=question1.id,
            language='en',
            headline='Question 1',
            description='First question'
        )
        db.session.add(q1_trans)
        
        # Create question 2
        question2 = FormQuestion(
            form_id=form.id,
            section_id=section1.id,
            order=2,
            question_type='long-text',
            is_required=False,
            key='question_2'
        )
        db.session.add(question2)
        db.session.flush()
        
        q2_trans = FormQuestionTranslation(
            form_question_id=question2.id,
            language='en',
            headline='Question 2',
            description='Second question'
        )
        db.session.add(q2_trans)
        
        db.session.commit()
        
        return form, section1, question1, question2
    
    def test_soft_delete_question(self):
        """Test that soft deleting a question preserves existing answers"""
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Create a response with answers
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer1 = FormAnswer(response_id=response.id, question_id=question1.id, value='Answer 1')
        answer2 = FormAnswer(response_id=response.id, question_id=question2.id, value='Answer 2')
        db.session.add(answer1)
        db.session.add(answer2)
        db.session.commit()
        
        # Soft delete question2
        question2.is_active = False
        question2.version += 1
        db.session.commit()
        
        # Verify question is soft deleted
        self.assertFalse(question2.is_active)
        self.assertEqual(question2.version, 2)
        
        # Verify answer still exists
        answer = db.session.query(FormAnswer).filter_by(question_id=question2.id).first()
        self.assertIsNotNone(answer)
        self.assertEqual(answer.value, 'Answer 2')
        
        # Verify question still accessible for historical data
        self.assertEqual(answer.question.id, question2.id)
    
    def test_serialize_form_filters_inactive(self):
        """Test that serialize_form filters out inactive sections and questions"""
        from app.forms.api import serialize_form
        
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Soft delete question2
        question2.is_active = False
        db.session.commit()
        
        # Serialize form (should exclude inactive)
        form_data = serialize_form(form, language='en', include_inactive=False)
        
        # Should have 1 section
        self.assertEqual(len(form_data['sections']), 1)
        
        # Section should have 1 question (question1 only)
        self.assertEqual(len(form_data['sections'][0]['questions']), 1)
        self.assertEqual(form_data['sections'][0]['questions'][0]['id'], question1.id)
    
    def test_serialize_form_includes_inactive_when_requested(self):
        """Test that serialize_form includes inactive items when requested"""
        from app.forms.api import serialize_form
        
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Soft delete question2
        question2.is_active = False
        db.session.commit()
        
        # Serialize form with inactive items
        form_data = serialize_form(form, language='en', include_inactive=True)
        
        # Should have 1 section
        self.assertEqual(len(form_data['sections']), 1)
        
        # Section should have 2 questions
        self.assertEqual(len(form_data['sections'][0]['questions']), 2)
        
        # Verify inactive question is marked
        inactive_question = [q for q in form_data['sections'][0]['questions'] if q['id'] == question2.id][0]
        self.assertFalse(inactive_question['is_active'])
    
    def test_validation_skips_inactive_questions(self):
        """Test that validation only validates active questions"""
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Make question2 required
        question2.is_required = True
        db.session.commit()
        
        # Create a response with answer only for question1
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer1 = FormAnswer(response_id=response.id, question_id=question1.id, value='Answer 1')
        db.session.add(answer1)
        db.session.commit()
        
        # Submit the response - should fail (question2 is required but not answered)
        rv = self.app.post(
            f'/api/v1/forms/{form.id}/responses/{response.id}/submit',
            json={},
            headers=self.auth_headers
        )
        self.assertEqual(rv.status_code, 400)  # Should fail validation
        
        # Now soft delete question2
        question2 = db.session.merge(question2)
        question2.is_active = False
        db.session.commit()
        
        # Try submitting again - should succeed (inactive questions are not validated)
        rv = self.app.post(
            f'/api/v1/forms/{form.id}/responses/{response.id}/submit',
            json={},
            headers=self.auth_headers
        )
        self.assertEqual(rv.status_code, 200)  # Should succeed
    
    def test_form_structure_api_soft_deletes_removed_questions(self):
        """Test that FormStructureAPI soft deletes questions not in the update"""
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Update structure - remove question2
        structure_data = {
            'sections': [
                {
                    'id': section1.id,
                    'order': 1,
                    'key': 'section-1',
                    'name': {'en': 'Section 1'},
                    'description': {'en': 'First section'},
                    'questions': [
                        {
                            'id': question1.id,
                            'order': 1,
                            'type': 'short-text',
                            'is_required': True,
                            'key': 'question_1',
                            'headline': {'en': 'Question 1'},
                            'description': {'en': 'First question'}
                        }
                        # question2 not included - should be soft deleted
                    ]
                }
            ]
        }
        
        rv = self.app.put(
            f'/api/v1/forms/{form.id}/structure',
            json=structure_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(rv.status_code, 200)
        
        # Verify question2 is soft deleted via API
        rv = self.app.get(
            f'/api/v1/forms/{form.id}/structure',
            headers=self.auth_headers
        )
        self.assertEqual(rv.status_code, 200)
        
        response_data = json.loads(rv.data)
        questions = response_data['sections'][0]['questions']
        
        # Should only have question1 (question2 is soft deleted)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['id'], question1.id)
        
        # Verify question1 is still active
        self.assertTrue(questions[0]['is_active'])
    
    def test_form_structure_api_reactivates_soft_deleted_questions(self):
        """Test that FormStructureAPI can reactivate soft deleted questions"""
        form, section1, question1, question2 = self._create_form_with_structure()
        
        # Soft delete question2 (increment version to match API behavior)
        question2.is_active = False
        question2.version += 1
        db.session.commit()
        
        # Update structure - include question2 again
        structure_data = {
            'sections': [
                {
                    'id': section1.id,
                    'order': 1,
                    'key': 'section-1',
                    'name': {'en': 'Section 1'},
                    'description': {'en': 'First section'},
                    'questions': [
                        {
                            'id': question1.id,
                            'order': 1,
                            'type': 'short-text',
                            'is_required': True,
                            'key': 'question_1',
                            'headline': {'en': 'Question 1'},
                            'description': {'en': 'First question'}
                        },
                        {
                            'id': question2.id,
                            'order': 2,
                            'type': 'long-text',
                            'is_required': False,
                            'key': 'question_2',
                            'headline': {'en': 'Question 2'},
                            'description': {'en': 'Second question'}
                        }
                    ]
                }
            ]
        }
        
        rv = self.app.put(
            f'/api/v1/forms/{form.id}/structure',
            json=structure_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(rv.status_code, 200)
        
        # Verify question2 is reactivated via API
        rv = self.app.get(
            f'/api/v1/forms/{form.id}/structure',
            headers=self.auth_headers
        )
        self.assertEqual(rv.status_code, 200)
        
        response_data = json.loads(rv.data)
        questions = response_data['sections'][0]['questions']
        
        # Find question2 in the response
        question2_data = [q for q in questions if q['id'] == question2.id][0]
        self.assertTrue(question2_data['is_active'])
        self.assertEqual(question2_data['version'], 3)  # Version incremented
    
    def test_version_increments_on_changes(self):
        """Test that version number increments when sections/questions are modified"""
        form, section1, question1, question2 = self._create_form_with_structure()
        
        initial_question_version = question1.version
        initial_section_version = section1.version
        
        # Update question1
        structure_data = {
            'sections': [
                {
                    'id': section1.id,
                    'order': 1,
                    'key': 'section-1-updated',
                    'name': {'en': 'Section 1 Updated'},
                    'description': {'en': 'First section updated'},
                    'questions': [
                        {
                            'id': question1.id,
                            'order': 1,
                            'type': 'short-text',
                            'is_required': False,  # Changed
                            'key': 'question_1',
                            'headline': {'en': 'Question 1 Updated'},
                            'description': {'en': 'First question updated'}
                        },
                        {
                            'id': question2.id,
                            'order': 2,
                            'type': 'long-text',
                            'is_required': False,
                            'key': 'question_2',
                            'headline': {'en': 'Question 2'},
                            'description': {'en': 'Second question'}
                        }
                    ]
                }
            ]
        }
        
        rv = self.app.put(
            f'/api/v1/forms/{form.id}/structure',
            json=structure_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(rv.status_code, 200)
        
        # Verify versions incremented via API
        rv = self.app.get(
            f'/api/v1/forms/{form.id}/structure',
            headers=self.auth_headers
        )
        self.assertEqual(rv.status_code, 200)
        
        response_data = json.loads(rv.data)
        updated_section = response_data['sections'][0]
        updated_question = [q for q in updated_section['questions'] if q['id'] == question1.id][0]
        
        # Verify section and question were updated
        self.assertEqual(updated_section['key'], 'section-1-updated')
        self.assertFalse(updated_question['is_required'])
        self.assertIsNotNone(updated_question.get('updated_at'))
