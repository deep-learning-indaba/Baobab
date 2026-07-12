from app import db
from app.forms.models import (
    Form, FormSection, FormSectionTranslation,
    FormQuestion, FormQuestionTranslation,
    FormResponse, FormAnswer,
    DependencyEvaluator, DependencyOperator
)
from app.utils.testing import ApiTestCase


class TestDependencyEvaluator(ApiTestCase):
    def test_empty_expression_returns_true(self):
        """Test that empty/None expression always returns True"""
        result = DependencyEvaluator.evaluate(None, {})
        self.assertTrue(result)
        
        result = DependencyEvaluator.evaluate({}, {})
        self.assertTrue(result)
    
    def test_equals_operator(self):
        """Test EQUALS operator"""
        expression = {
            "question_id": 1,
            "operator": "EQUALS",
            "values": ["yes"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "yes"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "no"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {}))
    
    def test_not_equals_operator(self):
        """Test NOT_EQUALS operator"""
        expression = {
            "question_id": 1,
            "operator": "NOT_EQUALS",
            "values": ["no"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "yes"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "no"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {}))
    
    def test_in_operator(self):
        """Test IN operator"""
        expression = {
            "question_id": 1,
            "operator": "IN",
            "values": ["1", "2", "3"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "1"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "2"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "3"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "4"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {}))
    
    def test_not_in_operator(self):
        """Test NOT_IN operator"""
        expression = {
            "question_id": 1,
            "operator": "NOT_IN",
            "values": ["red", "blue"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "green"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "red"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "blue"}))
    
    def test_greater_than_operator(self):
        """Test GREATER_THAN operator with numeric values"""
        expression = {
            "question_id": 1,
            "operator": "GREATER_THAN",
            "values": ["18"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "20"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "19"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "18"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "17"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "not_a_number"}))
    
    def test_less_than_operator(self):
        """Test LESS_THAN operator with numeric values"""
        expression = {
            "question_id": 1,
            "operator": "LESS_THAN",
            "values": ["100"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "50"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "100"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "150"}))
    
    def test_greater_than_or_equal_operator(self):
        """Test GREATER_THAN_OR_EQUAL operator"""
        expression = {
            "question_id": 1,
            "operator": "GREATER_THAN_OR_EQUAL",
            "values": ["18"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "18"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "19"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "17"}))
    
    def test_less_than_or_equal_operator(self):
        """Test LESS_THAN_OR_EQUAL operator"""
        expression = {
            "question_id": 1,
            "operator": "LESS_THAN_OR_EQUAL",
            "values": ["100"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "100"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "99"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "101"}))
    
    def test_between_operator(self):
        """Test BETWEEN operator"""
        expression = {
            "question_id": 1,
            "operator": "BETWEEN",
            "values": ["18", "65"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "18"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "30"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "65"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "17"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "66"}))
    
    def test_contains_operator(self):
        """Test CONTAINS operator for text"""
        expression = {
            "question_id": 1,
            "operator": "CONTAINS",
            "values": ["python"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "I love python"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "python is great"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "I love Java"}))
    
    def test_starts_with_operator(self):
        """Test STARTS_WITH operator"""
        expression = {
            "question_id": 1,
            "operator": "STARTS_WITH",
            "values": ["Dr."]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "Dr. Smith"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "Mr. Smith"}))
    
    def test_ends_with_operator(self):
        """Test ENDS_WITH operator"""
        expression = {
            "question_id": 1,
            "operator": "ENDS_WITH",
            "values": [".com"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "example.com"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "example.org"}))
    
    def test_regex_operator(self):
        """Test REGEX operator"""
        expression = {
            "question_id": 1,
            "operator": "REGEX",
            "values": ["^[0-9]{5}$"]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "12345"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "1234"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "abcde"}))
    
    def test_is_empty_operator(self):
        """Test IS_EMPTY operator"""
        expression = {
            "question_id": 1,
            "operator": "IS_EMPTY"
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: ""}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "   "}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "something"}))
    
    def test_is_not_empty_operator(self):
        """Test IS_NOT_EMPTY operator"""
        expression = {
            "question_id": 1,
            "operator": "IS_NOT_EMPTY"
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "something"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: ""}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "   "}))
    
    def test_and_operator(self):
        """Test AND logical operator"""
        expression = {
            "operator": "AND",
            "conditions": [
                {"question_id": 1, "operator": "EQUALS", "values": ["yes"]},
                {"question_id": 2, "operator": "EQUALS", "values": ["approved"]}
            ]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "yes", 2: "approved"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "yes", 2: "rejected"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "no", 2: "approved"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "no", 2: "rejected"}))
    
    def test_or_operator(self):
        """Test OR logical operator"""
        expression = {
            "operator": "OR",
            "conditions": [
                {"question_id": 1, "operator": "EQUALS", "values": ["red"]},
                {"question_id": 1, "operator": "EQUALS", "values": ["blue"]}
            ]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "red"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "blue"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "green"}))
    
    def test_not_operator(self):
        """Test NOT logical operator"""
        expression = {
            "operator": "NOT",
            "conditions": [
                {"question_id": 1, "operator": "EQUALS", "values": ["no"]}
            ]
        }
        
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "yes"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "no"}))
    
    def test_complex_nested_expression(self):
        """Test complex nested AND/OR expression"""
        expression = {
            "operator": "AND",
            "conditions": [
                {
                    "operator": "OR",
                    "conditions": [
                        {"question_id": 1, "operator": "EQUALS", "values": ["1"]},
                        {"question_id": 1, "operator": "EQUALS", "values": ["2"]}
                    ]
                },
                {
                    "question_id": 2,
                    "operator": "EQUALS",
                    "values": ["X"]
                }
            ]
        }
        
        # (Q1 is "1" OR Q1 is "2") AND Q2 is "X"
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "1", 2: "X"}))
        self.assertTrue(DependencyEvaluator.evaluate(expression, {1: "2", 2: "X"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "3", 2: "X"}))
        self.assertFalse(DependencyEvaluator.evaluate(expression, {1: "1", 2: "Y"}))
    
    def test_user_example_scenario(self):
        """Test the exact scenario from user's requirement:
        Question C depends on question A and B and should show only if 
        (question A is "1" or "2") AND (question B is "X")
        """
        expression = {
            "operator": "AND",
            "conditions": [
                {
                    "question_id": 123,  # Question A
                    "operator": "IN",
                    "values": ["1", "2"]
                },
                {
                    "question_id": 456,  # Question B
                    "operator": "EQUALS",
                    "values": ["X"]
                }
            ]
        }
        
        # Should show when A is "1" and B is "X"
        self.assertTrue(DependencyEvaluator.evaluate(expression, {123: "1", 456: "X"}))
        
        # Should show when A is "2" and B is "X"
        self.assertTrue(DependencyEvaluator.evaluate(expression, {123: "2", 456: "X"}))
        
        # Should NOT show when A is "3" and B is "X"
        self.assertFalse(DependencyEvaluator.evaluate(expression, {123: "3", 456: "X"}))
        
        # Should NOT show when A is "1" and B is "Y"
        self.assertFalse(DependencyEvaluator.evaluate(expression, {123: "1", 456: "Y"}))
        
        # Should NOT show when A is "2" and B is "Y"
        self.assertFalse(DependencyEvaluator.evaluate(expression, {123: "2", 456: "Y"}))


class TestFormQuestionDependencies(ApiTestCase):
    def seed_static_data(self):
        self.user = self.add_user('test@example.com', 'Test', 'User')
        self.event = self.add_event()
    
    def test_question_with_simple_dependency(self):
        """Test creating a question with a simple dependency expression"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        q1 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='dropdown'
        )
        db.session.add(q1)
        db.session.flush()
        
        dependency_expr = {
            "question_id": q1.id,
            "operator": "EQUALS",
            "values": ["yes"]
        }
        
        q2 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=2,
            question_type='short-text',
            dependency_expression=dependency_expr
        )
        db.session.add(q2)
        db.session.commit()
        
        self.assertIsNotNone(q2.dependency_expression)
        self.assertEqual(q2.dependency_expression['question_id'], q1.id)
        self.assertEqual(q2.dependency_expression['operator'], 'EQUALS')
    
    def test_question_evaluate_dependency_simple(self):
        """Test evaluating a question's dependency"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        q1 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=1,
            question_type='dropdown'
        )
        db.session.add(q1)
        db.session.flush()
        
        dependency_expr = {
            "question_id": q1.id,
            "operator": "EQUALS",
            "values": ["yes"]
        }
        
        q2 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=2,
            question_type='short-text',
            dependency_expression=dependency_expr
        )
        db.session.add(q2)
        db.session.commit()
        
        # Test with answer that satisfies dependency
        answers_dict = {q1.id: "yes"}
        self.assertTrue(q2.evaluate_dependency(answers_dict))
        
        # Test with answer that doesn't satisfy dependency
        answers_dict = {q1.id: "no"}
        self.assertFalse(q2.evaluate_dependency(answers_dict))
    
    def test_question_evaluate_dependency_complex(self):
        """Test evaluating a complex multi-dependency"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.flush()
        
        q1 = FormQuestion(form_id=form.id, section_id=section.id, order=1, question_type='dropdown')
        q2 = FormQuestion(form_id=form.id, section_id=section.id, order=2, question_type='dropdown')
        db.session.add(q1)
        db.session.add(q2)
        db.session.flush()
        
        dependency_expr = {
            "operator": "AND",
            "conditions": [
                {"question_id": q1.id, "operator": "IN", "values": ["1", "2"]},
                {"question_id": q2.id, "operator": "EQUALS", "values": ["X"]}
            ]
        }
        
        q3 = FormQuestion(
            form_id=form.id,
            section_id=section.id,
            order=3,
            question_type='short-text',
            dependency_expression=dependency_expr
        )
        db.session.add(q3)
        db.session.commit()
        
        # Test various combinations
        self.assertTrue(q3.evaluate_dependency({q1.id: "1", q2.id: "X"}))
        self.assertTrue(q3.evaluate_dependency({q1.id: "2", q2.id: "X"}))
        self.assertFalse(q3.evaluate_dependency({q1.id: "3", q2.id: "X"}))
        self.assertFalse(q3.evaluate_dependency({q1.id: "1", q2.id: "Y"}))
    
    def test_question_without_dependency_always_visible(self):
        """Test that questions without dependencies are always visible"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
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
        
        # Should be visible regardless of answers
        self.assertTrue(question.evaluate_dependency({}))
        self.assertTrue(question.evaluate_dependency({999: "any_value"}))


class TestFormSectionDependencies(ApiTestCase):
    def seed_static_data(self):
        self.user = self.add_user('test@example.com', 'Test', 'User')
        self.event = self.add_event()
    
    def test_section_with_dependency(self):
        """Test creating a section with dependency expression"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section1 = FormSection(form_id=form.id, order=1)
        db.session.add(section1)
        db.session.flush()
        
        q1 = FormQuestion(
            form_id=form.id,
            section_id=section1.id,
            order=1,
            question_type='dropdown'
        )
        db.session.add(q1)
        db.session.flush()
        
        dependency_expr = {
            "question_id": q1.id,
            "operator": "EQUALS",
            "values": ["advanced"]
        }
        
        section2 = FormSection(
            form_id=form.id,
            order=2,
            dependency_expression=dependency_expr
        )
        db.session.add(section2)
        db.session.commit()
        
        self.assertIsNotNone(section2.dependency_expression)
        self.assertEqual(section2.dependency_expression['question_id'], q1.id)
    
    def test_section_evaluate_dependency(self):
        """Test evaluating a section's dependency"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section1 = FormSection(form_id=form.id, order=1)
        db.session.add(section1)
        db.session.flush()
        
        q1 = FormQuestion(
            form_id=form.id,
            section_id=section1.id,
            order=1,
            question_type='dropdown'
        )
        db.session.add(q1)
        db.session.flush()
        
        dependency_expr = {
            "question_id": q1.id,
            "operator": "IN",
            "values": ["opt1", "opt2"]
        }
        
        section2 = FormSection(
            form_id=form.id,
            order=2,
            dependency_expression=dependency_expr
        )
        db.session.add(section2)
        db.session.commit()
        
        # Test with satisfying answers
        self.assertTrue(section2.evaluate_dependency({q1.id: "opt1"}))
        self.assertTrue(section2.evaluate_dependency({q1.id: "opt2"}))
        
        # Test with non-satisfying answer
        self.assertFalse(section2.evaluate_dependency({q1.id: "opt3"}))
    
    def test_section_without_dependency_always_visible(self):
        """Test that sections without dependencies are always visible"""
        self.seed_static_data()
        form = Form(event_id=self.event.id, created_by_user_id=self.user.id)
        db.session.add(form)
        db.session.flush()
        
        section = FormSection(form_id=form.id, order=1)
        db.session.add(section)
        db.session.commit()
        
        self.assertTrue(section.evaluate_dependency({}))
        self.assertTrue(section.evaluate_dependency({999: "any_value"}))
