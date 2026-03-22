import json
from datetime import datetime
from app import db
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation,
    FormResponse, FormAnswer
)
from app.utils.testing import ApiTestCase


class TestFormAPI(ApiTestCase):
    
    def seed_static_data(self):
        self.user = self.add_user('test@example.com', 'Test', 'User', password='password123')
        self.auth_headers = self.get_auth_header_for('test@example.com', 'password123')
        self.event = self.add_event()

    def _create_test_form(self):
        """Helper to create a test form with sections and questions"""
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1, key='test-section')
        db.session.add(section)
        db.session.flush()
        
        section_trans = FormSectionTranslation(
            form_section_id=section.id,
            language='en',
            name='Test Section',
            description='Section for testing'
        )
        db.session.add(section_trans)
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            is_required=True,
            key='test_question'
        )
        db.session.add(question)
        db.session.flush()
        
        question_trans = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Test Question',
            placeholder='Enter answer'
        )
        db.session.add(question_trans)
        db.session.commit()
        
        return form, section, question
    
    def test_get_form(self):
        """Test GET /api/v1/forms/{form_id}"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], form.id)
        self.assertTrue(data['is_open'])
        self.assertEqual(len(data['sections']), 1)
    
    def test_get_form_not_found(self):
        """Test GET /api/v1/forms/{form_id} with invalid ID"""
        self.seed_static_data()
        response = self.app.get(
            '/api/v1/forms/99999?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_form(self):
        """Test PUT /api/v1/forms/{form_id}"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        
        update_data = {
            'is_open': False,
            'is_active': True
        }
        
        response = self.app.put(
            f'/api/v1/forms/{form.id}',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['is_open'])
        
        # Verify in database
        updated_form = db.session.query(Form).filter_by(id=form.id).first()
        self.assertFalse(updated_form.is_open)
    
    def test_delete_form(self):
        """Test DELETE /api/v1/forms/{form_id} (soft delete)"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        form_id = form.id
        
        response = self.app.delete(
            f'/api/v1/forms/{form.id}',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 204)
        
        # Verify soft delete
        deleted_form = db.session.query(Form).filter_by(id=form_id).first()
        self.assertFalse(deleted_form.is_active)
    
    def test_create_response(self):
        """Test POST /api/v1/forms/{form_id}/responses"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        form_id = form.id
        
        response_data = {
            'language': 'en',
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Test Answer'
                }
            ]
        }
        
        response = self.app.post(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(response_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['form_id'], form_id)
        self.assertEqual(data['user_id'], self.user.id)
        self.assertFalse(data['is_submitted'])
        self.assertEqual(len(data['answers']), 1)
    
    def test_update_response(self):
        """Test PUT /api/v1/forms/{form_id}/responses to update existing response"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        question_id = question.id

        # Create initial response
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        response_id = response.id
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='Initial Answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        # Update response using PUT
        update_data = {
            'response_id': response.id,
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Updated Answer'
                }
            ]
        }
        
        response_obj = self.app.put(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response_obj.status_code, 200)
        
        # Verify answer was updated
        updated_answer = db.session.query(FormAnswer).filter_by(
            response_id=response_id,
            question_id=question_id,
            is_active=True
        ).first()
        self.assertEqual(updated_answer.value, 'Updated Answer')
    
    def test_get_user_response(self):
        """Test GET /api/v1/forms/{form_id}/responses"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create response
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='My Answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        response_obj = self.app.get(
            f'/api/v1/forms/{form.id}/responses',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 200)
        data = json.loads(response_obj.data)
        self.assertEqual(data['id'], response.id)
        self.assertEqual(len(data['answers']), 1)
    
    def test_submit_response_valid(self):
        """Test POST /api/v1/forms/{form_id}/responses/{response_id}/submit with valid data"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create response with valid answer
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='Valid Answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        response_obj = self.app.post(
            f'/api/v1/forms/{form.id}/responses/{response.id}/submit',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 200)
        data = json.loads(response_obj.data)
        self.assertTrue(data['is_submitted'])
        self.assertIsNotNone(data['submitted_timestamp'])
    
    def test_submit_response_invalid(self):
        """Test submitting response with validation errors"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create response with empty answer (required field)
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value=''
        )
        db.session.add(answer)
        db.session.commit()
        
        response_obj = self.app.post(
            f'/api/v1/forms/{form.id}/responses/{response.id}/submit',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 400)
        data = json.loads(response_obj.data)
        self.assertEqual(data['error'], 'Validation failed')
        self.assertGreater(len(data['details']), 0)
    
    def test_withdraw_response(self):
        """Test POST /api/v1/forms/{form_id}/responses/{response_id}/withdraw"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create submitted response
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        response.is_submitted = True
        response.submitted_timestamp = datetime.now()
        db.session.add(response)
        db.session.commit()
        
        response_obj = self.app.post(
            f'/api/v1/forms/{form.id}/responses/{response.id}/withdraw',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 200)
        data = json.loads(response_obj.data)
        self.assertTrue(data['is_withdrawn'])
        self.assertIsNotNone(data['withdrawn_timestamp'])
    
    def test_submit_response_closed_form(self):
        """Test submitting to a closed form"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        form.is_open = False
        db.session.commit()
        
        response_data = {
            'language': 'en',
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Test Answer'
                }
            ]
        }
        
        response = self.app.post(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(response_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        # Should return error for closed form
        self.assertIn(response.status_code, [400, 403])
    
    def test_unauthorized_access(self):
        """Test accessing form without authentication"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        
        # Request without auth headers
        response = self.app.get(f'/api/v1/forms/{form.id}')
        
        self.assertEqual(response.status_code, 401)
    
    def test_post_error_when_response_exists(self):
        """Test that POST returns error when response exists on single-response form"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        form_id = form.id
        # multiple_responses defaults to False
        
        # Create first response
        response_data = {
            'language': 'en',
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'First Answer'
                }
            ]
        }
        
        response1 = self.app.post(
            f'/api/v1/forms/{form_id}/responses',
            data=json.dumps(response_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, 201)
        data1 = json.loads(response1.data)
        response_id_1 = data1['id']
        
        # Try to create second response without submitting first - should fail
        response2 = self.app.post(
            f'/api/v1/forms/{form_id}/responses',
            data=json.dumps(response_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 400)
        data2 = json.loads(response2.data)
        self.assertEqual(data2['error'], 'Response already exists')
        self.assertEqual(data2['response_id'], response_id_1)
    
    def test_multiple_responses_enabled(self):
        """Test that multiple response forms allow POST to create new responses"""
        # Create form with multiple_responses=True
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True, multiple_responses=True)
        db.session.add(form)
        db.session.flush()
        form_id = form.id
        
        section = FormSection(form_id=form.id, order=1, key='test-section')
        db.session.add(section)
        db.session.flush()
        
        section_trans = FormSectionTranslation(
            form_section_id=section.id,
            language='en',
            name='Test Section',
            description='Section for testing'
        )
        db.session.add(section_trans)
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            is_required=True,
            key='test_question'
        )
        db.session.add(question)
        db.session.flush()
        question_id = question.id
        
        question_trans = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Test Question',
            placeholder='Enter answer'
        )
        db.session.add(question_trans)
        db.session.commit()
        
        # Create first response
        response_data1 = {
            'language': 'en',
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'First Response'
                }
            ]
        }
        
        response1 = self.app.post(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(response_data1),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, 201)
        data1 = json.loads(response1.data)
        response_id_1 = data1['id']
        
        # Create second response - should succeed with multiple_responses=True
        response_data2 = {
            'language': 'en',
            'answers': [
                {
                    'question_id': question_id,
                    'value': 'Second Response'
                }
            ]
        }
        
        response2 = self.app.post(
            f'/api/v1/forms/{form_id}/responses',
            data=json.dumps(response_data2),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 201)
        data2 = json.loads(response2.data)
        response_id_2 = data2['id']
        
        # Should create different response IDs
        self.assertNotEqual(response_id_1, response_id_2)
        self.assertEqual(data1['answers'][0]['value'], 'First Response')
        self.assertEqual(data2['answers'][0]['value'], 'Second Response')
    
    def test_get_responses_multiple_enabled(self):
        """Test GET returns all responses when multiple_responses is enabled"""
        # Create form with multiple_responses=True
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True, multiple_responses=True)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text'
        )
        db.session.add(question)
        db.session.commit()
        
        # Create multiple responses
        for i in range(3):
            response = FormResponse(form_id=form.id, user_id=self.user.id)
            db.session.add(response)
            db.session.flush()
            
            answer = FormAnswer(
                response_id=response.id,
                question_id=question.id,
                value=f'Answer {i+1}'
            )
            db.session.add(answer)
        db.session.commit()
        
        # Get responses
        response_obj = self.app.get(
            f'/api/v1/forms/{form.id}/responses',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 200)
        data = json.loads(response_obj.data)
        self.assertIn('responses', data)
        self.assertEqual(len(data['responses']), 3)
    
    def test_get_responses_single_form(self):
        """Test GET returns single response when multiple_responses is disabled"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create response
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='My Answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        response_obj = self.app.get(
            f'/api/v1/forms/{form.id}/responses',
            headers=self.auth_headers
        )
        
        self.assertEqual(response_obj.status_code, 200)
        data = json.loads(response_obj.data)
        # Should return single response object, not array
        self.assertNotIn('responses', data)
        self.assertIn('id', data)
        self.assertEqual(data['id'], response.id)
    
    def test_multiple_responses_flag_in_form_response(self):
        """Test that form API includes multiple_responses flag"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True, multiple_responses=True)
        db.session.add(form)
        db.session.commit()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['multiple_responses'])
    
    def test_put_without_response_id(self):
        """Test PUT requires response_id"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        update_data = {
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Some Answer'
                }
            ]
        }
        
        response = self.app.put(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'response_id is required')
    
    def test_put_nonexistent_response(self):
        """Test PUT with nonexistent response_id"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        update_data = {
            'response_id': 99999,
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Some Answer'
                }
            ]
        }
        
        response = self.app.put(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Response not found')
    
    def test_put_submitted_response(self):
        """Test that PUT cannot update submitted response"""
        self.seed_static_data()
        form, section, question = self._create_test_form()
        
        # Create and submit response
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        response.is_submitted = True
        response.submitted_timestamp = datetime.now()
        db.session.add(response)
        db.session.flush()
        
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='Original Answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        # Try to update
        update_data = {
            'response_id': response.id,
            'answers': [
                {
                    'question_id': question.id,
                    'value': 'Updated Answer'
                }
            ]
        }
        
        response_obj = self.app.put(
            f'/api/v1/forms/{form.id}/responses',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response_obj.status_code, 400)
        data = json.loads(response_obj.data)
        self.assertEqual(data['error'], 'Cannot update a submitted response')
    
    def test_form_settings_in_get_response(self):
        """Test that form settings are included in GET response"""
        self.seed_static_data()
        settings = {
            'page_per_section': True,
            'show_progress': True
        }
        form = Form(
            created_by_user_id=self.user.id,
            is_open=True,
            settings=settings
        )
        db.session.add(form)
        db.session.commit()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('settings', data)
        self.assertEqual(data['settings']['page_per_section'], True)
        self.assertEqual(data['settings']['show_progress'], True)
    
    def test_form_settings_null_when_not_set(self):
        """Test that form settings is null when not set"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('settings', data)
        self.assertIsNone(data['settings'])
    
    def test_update_form_settings(self):
        """Test PUT /api/v1/forms/{form_id} to update settings"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        
        new_settings = {
            'page_per_section': True,
            'theme': 'dark',
            'custom_option': 'value'
        }
        update_data = {
            'settings': new_settings
        }
        
        response = self.app.put(
            f'/api/v1/forms/{form.id}',
            data=json.dumps(update_data),
            headers=self.auth_headers,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsNotNone(data['settings'])
        self.assertEqual(data['settings']['page_per_section'], True)
        self.assertEqual(data['settings']['theme'], 'dark')
        
        # Verify in database
        updated_form = db.session.query(Form).filter_by(id=form.id).first()
        self.assertEqual(updated_form.settings['page_per_section'], True)
        self.assertEqual(updated_form.settings['theme'], 'dark')
    
    def test_question_settings_in_get_response(self):
        """Test that question settings are included in GET response"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id, is_open=True)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1, key='test-section')
        db.session.add(section)
        db.session.flush()
        
        section_trans = FormSectionTranslation(
            form_section_id=section.id,
            language='en',
            name='Test Section'
        )
        db.session.add(section_trans)
        
        question_settings = {
            'file_type': 'pdf',
            'max_size': 5242880,
            'accept': '.pdf,.doc'
        }
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='file',
            is_required=True,
            key='upload_question',
            settings=question_settings
        )
        db.session.add(question)
        db.session.flush()
        
        question_trans = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Upload File'
        )
        db.session.add(question_trans)
        db.session.commit()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(len(data['sections'][0]['questions']), 1)
        
        question_data = data['sections'][0]['questions'][0]
        self.assertIn('settings', question_data)
        self.assertEqual(question_data['settings']['file_type'], 'pdf')
        self.assertEqual(question_data['settings']['max_size'], 5242880)
        self.assertEqual(question_data['settings']['accept'], '.pdf,.doc')
    
    def test_question_settings_null_when_not_set(self):
        """Test that question settings is null when not set"""
        self.seed_static_data()
        form, _, _ = self._create_test_form()
        
        response = self.app.get(
            f'/api/v1/forms/{form.id}?language=en',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        question_data = data['sections'][0]['questions'][0]
        self.assertIn('settings', question_data)
        self.assertIsNone(question_data['settings'])
