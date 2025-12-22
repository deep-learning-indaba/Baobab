from datetime import datetime
from app import db
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation,
    FormResponse, FormAnswer,
    ValidationError
)
from app.utils.testing import ApiTestCase


class TestFormModels(ApiTestCase):
    def seed_static_data(self):
        self.user = self.add_user('test@example.com', 'Test', 'User')

    def test_create_form(self):
        """Test creating a basic form"""
        self.seed_static_data()
        form = Form(
            created_by_user_id=self.user.id,
            is_open=True
        )
        db.session.add(form)
        db.session.commit()
        
        self.assertIsNotNone(form.id)
        self.assertTrue(form.is_active)
        self.assertTrue(form.is_open)
        self.assertEqual(form.version, 1)
        self.assertIsNotNone(form.created_at)
    
    def test_form_with_sections(self):
        """Test creating a form with sections"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1, key='personal-info')
        db.session.add(section)
        db.session.commit()
        
        self.assertEqual(len(form.sections), 1)
        self.assertEqual(form.sections[0].order, 1)
        self.assertEqual(form.sections[0].key, 'personal-info')
    
    def test_section_translation(self):
        """Test section translations"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        translation_en = FormSectionTranslation(
            form_section_id=section.id,
            language='en',
            name='Personal Information',
            description='Enter your details'
        )
        translation_fr = FormSectionTranslation(
            form_section_id=section.id,
            language='fr',
            name='Informations Personnelles',
            description='Entrez vos détails'
        )
        db.session.add(translation_en)
        db.session.add(translation_fr)
        db.session.commit()
        
        self.assertEqual(section.get_translation('en').name, 'Personal Information')
        self.assertEqual(section.get_translation('fr').name, 'Informations Personnelles')
    
    def test_form_with_questions(self):
        """Test creating questions in a section"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            is_required=True,
            key='full_name'
        )
        db.session.add(question)
        db.session.commit()
        
        self.assertEqual(len(section.questions), 1)
        self.assertEqual(section.questions[0].type, 'short-text')
        self.assertTrue(section.questions[0].is_required)
    
    def test_question_translation(self):
        """Test question translations"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
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
        db.session.flush()
        
        translation = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='What is your name?',
            placeholder='Enter full name',
            validation_regex='^[A-Za-z ]+$',
            validation_text='Only letters allowed'
        )
        db.session.add(translation)
        db.session.commit()
        
        trans = question.get_translation('en')
        self.assertEqual(trans.headline, 'What is your name?')
        self.assertEqual(trans.validation_regex, '^[A-Za-z ]+$')
    
    def test_question_with_options(self):
        """Test multi-choice question with options"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='multi-choice'
        )
        db.session.add(question)
        db.session.flush()
        
        options = [
            {'value': 'opt1', 'label': 'Option 1'},
            {'value': 'opt2', 'label': 'Option 2'}
        ]
        translation = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Choose one',
            options=options
        )
        db.session.add(translation)
        db.session.commit()
        
        trans = question.get_translation('en')
        self.assertEqual(len(trans.options), 2)
        self.assertEqual(trans.options[0]['value'], 'opt1')
    
    def test_conditional_question(self):
        """Test question with dependency"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        q1 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='multi-choice'
        )
        db.session.add(q1)
        db.session.flush()
        
        q2 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=2,
            question_type='short-text',
            depends_on_question_id=q1.id
        )
        db.session.add(q2)
        db.session.commit()
        
        self.assertEqual(q2.depends_on_question_id, q1.id)
    
    def test_form_linking(self):
        """Test generic form linking"""
        self.seed_static_data()
        form1 = Form(created_by_user_id=self.user.id)
        db.session.add(form1)
        db.session.flush()
        
        form2 = Form(
            created_by_user_id=self.user.id,
            linked_form_id=form1.id
        )
        db.session.add(form2)
        db.session.commit()
        
        self.assertEqual(form2.linked_form_id, form1.id)
        self.assertEqual(form2.linked_form.id, form1.id)
    
    def test_create_response(self):
        """Test creating a form response"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        response = FormResponse(
            form_id=form.id,
            user_id=self.user.id,
            language='en'
        )
        db.session.add(response)
        db.session.commit()
        
        self.assertIsNotNone(response.id)
        self.assertFalse(response.is_submitted)
        self.assertFalse(response.is_withdrawn)
        self.assertIsNotNone(response.started_timestamp)
    
    def test_answer_validation_required(self):
        """Test required field validation"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            is_required=True
        )
        db.session.add(question)
        db.session.flush()
        
        translation = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Name'
        )
        db.session.add(translation)
        db.session.flush()
        
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        # Empty answer
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value=''
        )
        db.session.add(answer)
        db.session.commit()
        
        is_valid, error = answer.validate('en')
        self.assertFalse(is_valid)
        self.assertEqual(error, ValidationError.REQUIRED)
    
    def test_answer_validation_regex(self):
        """Test regex validation"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='short-text',
            is_required=False
        )
        db.session.add(question)
        db.session.flush()
        
        translation = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Name',
            validation_regex='^[A-Za-z ]+$'
        )
        db.session.add(translation)
        db.session.flush()
        
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        # Invalid answer with numbers
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='John123'
        )
        db.session.add(answer)
        db.session.commit()
        
        is_valid, error = answer.validate('en')
        self.assertFalse(is_valid)
        self.assertEqual(error, ValidationError.VALIDATION_REGEX_FAILED)
        
        # Valid answer
        answer.value = 'John Doe'
        is_valid, error = answer.validate('en')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_answer_validation_option(self):
        """Test option validation for multi-choice"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        question = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='multi-choice'
        )
        db.session.add(question)
        db.session.flush()
        
        options = [
            {'value': 'opt1', 'label': 'Option 1'},
            {'value': 'opt2', 'label': 'Option 2'}
        ]
        translation = FormQuestionTranslation(
            form_question_id=question.id,
            language='en',
            headline='Choose',
            options=options
        )
        db.session.add(translation)
        db.session.flush()
        
        response = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response)
        db.session.flush()
        
        # Invalid option
        answer = FormAnswer(
            response_id=response.id,
            question_id=question.id,
            value='invalid'
        )
        db.session.add(answer)
        db.session.commit()
        
        is_valid, error = answer.validate('en')
        self.assertFalse(is_valid)
        self.assertEqual(error, ValidationError.INVALID_OPTION)
        
        # Valid option
        answer.value = 'opt1'
        is_valid, error = answer.validate('en')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_cascade_delete_form(self):
        """Test that deleting form cascades to sections and questions"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
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
        
        form_id = form.id
        section_id = section.id
        question_id = question.id
        
        # Delete form
        db.session.delete(form)
        db.session.commit()
        
        # Check cascade
        self.assertIsNone(db.session.query(FormSection).filter_by(id=section_id).first())
        self.assertIsNone(db.session.query(FormQuestion).filter_by(id=question_id).first())
    
    def test_multiple_responses_flag(self):
        """Test form with multiple_responses enabled"""
        self.seed_static_data()
        form = Form(
            created_by_user_id=self.user.id,
            multiple_responses=True
        )
        db.session.add(form)
        db.session.commit()
        
        self.assertTrue(form.multiple_responses)
    
    def test_multiple_responses_default_false(self):
        """Test that multiple_responses defaults to False"""
        self.seed_static_data()
        form = Form(created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.commit()
        
        self.assertFalse(form.multiple_responses)
    
    def test_multiple_responses_for_user(self):
        """Test creating multiple responses for same user on form with multiple_responses=True"""
        self.seed_static_data()
        form = Form(
            created_by_user_id=self.user.id,
            multiple_responses=True
        )
        db.session.add(form)
        db.session.flush()
        
        # Create first response
        response1 = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response1)
        db.session.commit()
        
        # Create second response from same user
        response2 = FormResponse(form_id=form.id, user_id=self.user.id)
        db.session.add(response2)
        db.session.commit()
        
        # Verify both responses exist
        responses = db.session.query(FormResponse).filter_by(
            form_id=form.id,
            user_id=self.user.id
        ).all()
        
        self.assertEqual(len(responses), 2)
        self.assertNotEqual(response1.id, response2.id)
