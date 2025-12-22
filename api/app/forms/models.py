from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import column_property
import re
import enum
from typing import Tuple, Optional

from app import db, LOGGER


class DependencyOperator(str, enum.Enum):
    """Operators for dependency conditions"""
    # Comparison operators
    EQUALS = 'EQUALS'
    NOT_EQUALS = 'NOT_EQUALS'
    IN = 'IN'
    NOT_IN = 'NOT_IN'
    
    # Numeric operators
    GREATER_THAN = 'GREATER_THAN'
    LESS_THAN = 'LESS_THAN'
    GREATER_THAN_OR_EQUAL = 'GREATER_THAN_OR_EQUAL'
    LESS_THAN_OR_EQUAL = 'LESS_THAN_OR_EQUAL'
    BETWEEN = 'BETWEEN'
    
    # Text operators
    CONTAINS = 'CONTAINS'
    STARTS_WITH = 'STARTS_WITH'
    ENDS_WITH = 'ENDS_WITH'
    REGEX = 'REGEX'
    
    # Boolean operators
    IS_EMPTY = 'IS_EMPTY'
    IS_NOT_EMPTY = 'IS_NOT_EMPTY'
    
    # Logical operators
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'


class DependencyEvaluator:
    """Evaluates dependency expressions against answer values"""
    
    @staticmethod
    def evaluate(expression: dict, answers_dict: dict) -> bool:
        """
        Evaluate a dependency expression.
        
        Args:
            expression: The dependency expression (JSON structure)
            answers_dict: Dictionary mapping question_id to answer value
                         {question_id: "value"}
        
        Returns:
            bool: True if the condition is satisfied, False otherwise
        
        Example expressions:
            # Simple condition
            {"question_id": 123, "operator": "EQUALS", "values": ["yes"]}
            
            # Complex condition with AND
            {
                "operator": "AND",
                "conditions": [
                    {"question_id": 123, "operator": "IN", "values": ["1", "2"]},
                    {"question_id": 456, "operator": "EQUALS", "values": ["X"]}
                ]
            }
        """
        if not expression:
            return True
        
        operator = expression.get('operator')
        
        # Handle logical operators (AND, OR, NOT)
        if operator in [DependencyOperator.AND.value, DependencyOperator.OR.value, DependencyOperator.NOT.value]:
            return DependencyEvaluator._evaluate_logical(expression, answers_dict)
        
        # Handle leaf condition
        return DependencyEvaluator._evaluate_condition(expression, answers_dict)
    
    @staticmethod
    def _evaluate_logical(expression: dict, answers_dict: dict) -> bool:
        """Evaluate logical operators (AND, OR, NOT)"""
        operator = expression.get('operator')
        conditions = expression.get('conditions', [])
        
        if operator == DependencyOperator.AND.value:
            return all(DependencyEvaluator.evaluate(cond, answers_dict) for cond in conditions)
        
        elif operator == DependencyOperator.OR.value:
            return any(DependencyEvaluator.evaluate(cond, answers_dict) for cond in conditions)
        
        elif operator == DependencyOperator.NOT.value:
            if len(conditions) != 1:
                LOGGER.warning(f"NOT operator expects exactly 1 condition, got {len(conditions)}")
                return False
            return not DependencyEvaluator.evaluate(conditions[0], answers_dict)
        
        return False
    
    @staticmethod
    def _evaluate_condition(expression: dict, answers_dict: dict) -> bool:
        """Evaluate a single condition"""
        question_id = expression.get('question_id')
        operator = expression.get('operator')
        values = expression.get('values', [])
        
        if question_id is None:
            LOGGER.warning("Dependency condition missing question_id")
            return False
        
        # Get the answer value for this question
        answer_value = answers_dict.get(question_id)
        
        # Handle IS_EMPTY and IS_NOT_EMPTY
        if operator == DependencyOperator.IS_EMPTY.value:
            return not answer_value or answer_value.strip() == ''
        
        if operator == DependencyOperator.IS_NOT_EMPTY.value:
            return bool(answer_value and answer_value.strip())
        
        # If no answer exists, condition fails (except for empty checks above)
        if answer_value is None:
            return False
        
        # Comparison operators
        if operator == DependencyOperator.EQUALS.value:
            return len(values) > 0 and answer_value == values[0]
        
        if operator == DependencyOperator.NOT_EQUALS.value:
            return len(values) > 0 and answer_value != values[0]
        
        if operator == DependencyOperator.IN.value:
            return answer_value in values
        
        if operator == DependencyOperator.NOT_IN.value:
            return answer_value not in values
        
        # Numeric operators
        if operator in [DependencyOperator.GREATER_THAN.value, DependencyOperator.LESS_THAN.value,
                       DependencyOperator.GREATER_THAN_OR_EQUAL.value, DependencyOperator.LESS_THAN_OR_EQUAL.value]:
            return DependencyEvaluator._evaluate_numeric(operator, answer_value, values)
        
        if operator == DependencyOperator.BETWEEN.value:
            if len(values) != 2:
                LOGGER.warning(f"BETWEEN operator expects 2 values, got {len(values)}")
                return False
            try:
                val = float(answer_value)
                return float(values[0]) <= val <= float(values[1])
            except (ValueError, TypeError):
                return False
        
        # Text operators
        if operator == DependencyOperator.CONTAINS.value:
            return len(values) > 0 and values[0] in answer_value
        
        if operator == DependencyOperator.STARTS_WITH.value:
            return len(values) > 0 and answer_value.startswith(values[0])
        
        if operator == DependencyOperator.ENDS_WITH.value:
            return len(values) > 0 and answer_value.endswith(values[0])
        
        if operator == DependencyOperator.REGEX.value:
            if len(values) == 0:
                return False
            try:
                return bool(re.match(values[0], answer_value))
            except re.error as e:
                LOGGER.warning(f"Invalid regex pattern in dependency: {e}")
                return False
        
        LOGGER.warning(f"Unknown dependency operator: {operator}")
        return False
    
    @staticmethod
    def _evaluate_numeric(operator: str, answer_value: str, values: list) -> bool:
        """Evaluate numeric comparison operators"""
        if len(values) == 0:
            return False
        
        try:
            answer_num = float(answer_value)
            compare_num = float(values[0])
            
            if operator == DependencyOperator.GREATER_THAN.value:
                return answer_num > compare_num
            elif operator == DependencyOperator.LESS_THAN.value:
                return answer_num < compare_num
            elif operator == DependencyOperator.GREATER_THAN_OR_EQUAL.value:
                return answer_num >= compare_num
            elif operator == DependencyOperator.LESS_THAN_OR_EQUAL.value:
                return answer_num <= compare_num
        except (ValueError, TypeError):
            return False
        
        return False


class ValidationError(str, enum.Enum):
    REQUIRED = 'required'
    INVALID_OPTION = 'invalid_option'
    VALIDATION_REGEX_FAILED = 'validation_regex_failed'


class Form(db.Model):
    """A generic form."""
    __tablename__ = 'form'
    
    id = db.Column(db.Integer(), primary_key=True)
    
    # Basic form properties
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    is_open = db.Column(db.Boolean(), nullable=False, default=True)
    multiple_responses = db.Column(db.Boolean(), nullable=False, default=False)
    linked_form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=True)
    
    # Settings for UI customization (e.g., page-per-section)
    settings = db.Column(db.JSON(), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)
    created_by_user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    
    # Versioning for form changes
    version = db.Column(db.Integer(), nullable=False, default=1)
    parent_form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=True)

    # Relationships
    sections = db.relationship('FormSection', order_by='FormSection.order', 
                              cascade='all, delete-orphan', foreign_keys='FormSection.form_id',
                              back_populates='form')
    questions = db.relationship('FormQuestion', cascade='all, delete-orphan',
                               foreign_keys='FormQuestion.form_id',
                               back_populates='form')
    responses = db.relationship('FormResponse', back_populates='form',
                               foreign_keys='FormResponse.form_id')
    
    # Link to parent/linked forms
    parent_form = db.relationship('Form', remote_side=[id], foreign_keys=[parent_form_id])
    linked_form = db.relationship('Form', remote_side=[id], foreign_keys=[linked_form_id])
    
    created_by = db.relationship('AppUser', foreign_keys=[created_by_user_id])
    
    def __init__(self, created_by_user_id, is_open=True, is_active=True, 
                 linked_form_id=None, parent_form_id=None, multiple_responses=False,
                 settings=None):
        self.created_by_user_id = created_by_user_id
        self.is_open = is_open
        self.is_active = is_active
        self.linked_form_id = linked_form_id
        self.parent_form_id = parent_form_id
        self.multiple_responses = multiple_responses
        self.settings = settings
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.version = 1


class FormSection(db.Model):
    """Sections group related questions."""
    __tablename__ = 'form_section'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    key = db.Column(db.String(255), nullable=True)  # Optional identifier
    
    # Conditional visibility using expression-based dependencies
    dependency_expression = db.Column(db.JSON(), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='sections', foreign_keys=[form_id])
    translations = db.relationship('FormSectionTranslation', lazy='dynamic',
                                   cascade='all, delete-orphan',
                                   back_populates='section')
    questions = db.relationship('FormQuestion', order_by='FormQuestion.order',
                               cascade='all, delete-orphan', 
                               foreign_keys='FormQuestion.section_id',
                               back_populates='section')
    
    def __init__(self, form_id, order, key=None, dependency_expression=None):
        self.form_id = form_id
        self.order = order
        self.key = key
        self.dependency_expression = dependency_expression
    
    def get_translation(self, language: str) -> 'FormSectionTranslation':
        return self.translations.filter_by(language=language).first()
    
    def evaluate_dependency(self, answers_dict: dict) -> bool:
        """
        Evaluate whether this section should be visible based on its dependencies.
        
        Args:
            answers_dict: Dictionary mapping question_id to answer value
        
        Returns:
            bool: True if section should be visible, False otherwise
        """
        if not self.dependency_expression:
            return True
        
        return DependencyEvaluator.evaluate(self.dependency_expression, answers_dict)


class FormSectionTranslation(db.Model):
    """i18n support for sections."""
    __tablename__ = 'form_section_translation'
    __table_args__ = (
        db.UniqueConstraint('form_section_id', 'language'),
    )
    
    id = db.Column(db.Integer(), primary_key=True)
    form_section_id = db.Column(db.Integer(), 
                               db.ForeignKey('form_section.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    
    section = db.relationship('FormSection', back_populates='translations')
    
    def __init__(self, form_section_id, language, name, description=None):
        self.form_section_id = form_section_id
        self.language = language
        self.name = name
        self.description = description


class FormQuestion(db.Model):
    """Generic question model supporting multiple types."""
    __tablename__ = 'form_question'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    section_id = db.Column(db.Integer(), 
                          db.ForeignKey('form_section.id'), nullable=False)
    
    # Question type (extensible via QuestionType registry)
    type = db.Column(db.String(50), nullable=False)
    # Types: short-text, long-text, dropdown, checkboxes, 
    #        date, file, multi-file, numeric, single-checkbox, etc.
    
    order = db.Column(db.Integer(), nullable=False)
    is_required = db.Column(db.Boolean(), nullable=False, default=True)
    key = db.Column(db.String(255), nullable=True)  # Optional identifier
    
    # Settings for UI customization (e.g., file-type)
    settings = db.Column(db.JSON(), nullable=True)  
    
    # Conditional visibility using expression-based dependencies
    dependency_expression = db.Column(db.JSON(), nullable=True)
    
    # Generic question linking - questions can reference other questions
    # Use case: Review questions can link to application questions to display alongside
    linked_question_id = db.Column(db.Integer(), 
                                   db.ForeignKey('form_question.id'), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='questions', foreign_keys=[form_id])
    section = db.relationship('FormSection', back_populates='questions', foreign_keys=[section_id])
    translations = db.relationship('FormQuestionTranslation', lazy='dynamic',
                                   cascade='all, delete-orphan',
                                   back_populates='question')
    answers = db.relationship('FormAnswer', back_populates='question')
    linked_question = db.relationship('FormQuestion', remote_side=[id], 
                                     foreign_keys=[linked_question_id])
    
    def __init__(self, form_id, section_id, order, question_type, 
                 is_required=True, key=None, dependency_expression=None,
                 linked_question_id=None, settings=None):
        self.form_id = form_id
        self.section_id = section_id
        self.order = order
        self.type = question_type
        self.is_required = is_required
        self.key = key
        self.dependency_expression = dependency_expression
        self.linked_question_id = linked_question_id
        self.settings = settings
    
    def get_translation(self, language: str) -> 'FormQuestionTranslation':
        return self.translations.filter_by(language=language).first()
    
    def evaluate_dependency(self, answers_dict: dict) -> bool:
        """
        Evaluate whether this question should be visible based on its dependencies.
        
        Args:
            answers_dict: Dictionary mapping question_id to answer value
        
        Returns:
            bool: True if question should be visible, False otherwise
        """
        if not self.dependency_expression:
            return True
        
        return DependencyEvaluator.evaluate(self.dependency_expression, answers_dict)


class FormQuestionTranslation(db.Model):
    """i18n support for questions."""
    __tablename__ = 'form_question_translation'
    __table_args__ = (
        db.UniqueConstraint('form_question_id', 'language'),
    )
    
    id = db.Column(db.Integer(), primary_key=True)
    form_question_id = db.Column(db.Integer(), 
                                 db.ForeignKey('form_question.id'), nullable=False)
    language = db.Column(db.String(2), nullable=False)
    
    headline = db.Column(db.Text(), nullable=False)
    description = db.Column(db.Text(), nullable=True)
    placeholder = db.Column(db.String(255), nullable=True)
    
    # Validation
    validation_regex = db.Column(db.String(500), nullable=True)
    validation_text = db.Column(db.Text(), nullable=True)
    
    # Options for multi-choice questions (JSON array)
    options = db.Column(db.JSON(), nullable=True)
    # Format: [{"value": "opt1", "label": "Option 1"}, ...]
    
    question = db.relationship('FormQuestion', back_populates='translations')
    
    def __init__(self, form_question_id, language, headline, description=None,
                 placeholder=None, validation_regex=None, validation_text=None,
                 options=None):
        self.form_question_id = form_question_id
        self.language = language
        self.headline = headline
        self.description = description
        self.placeholder = placeholder
        self.validation_regex = validation_regex
        self.validation_text = validation_text
        self.options = options


class FormResponse(db.Model):
    """User's response to a form."""
    __tablename__ = 'form_response'
    
    id = db.Column(db.Integer(), primary_key=True)
    form_id = db.Column(db.Integer(), db.ForeignKey('form.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('app_user.id'), nullable=False)
    
    # Lifecycle
    is_submitted = db.Column(db.Boolean(), nullable=False, default=False)
    submitted_timestamp = db.Column(db.DateTime(), nullable=True)
    is_withdrawn = db.Column(db.Boolean(), nullable=False, default=False)
    withdrawn_timestamp = db.Column(db.DateTime(), nullable=True)
    started_timestamp = db.Column(db.DateTime(), nullable=False)
    
    language = db.Column(db.String(2), nullable=False, default='en')
    
    # For multiple submissions.
    parent_response_id = db.Column(db.Integer(), 
                                   db.ForeignKey('form_response.id'), nullable=True)
    
    # Relationships
    form = db.relationship('Form', back_populates='responses', foreign_keys=[form_id])
    user = db.relationship('AppUser', foreign_keys=[user_id])
    answers = db.relationship('FormAnswer',
                             cascade='all, delete-orphan',
                             back_populates='response')
    parent_response = db.relationship('FormResponse', remote_side=[id],
                                     foreign_keys=[parent_response_id])
    
    # Indexes
    __table_args__ = (
        db.Index('idx_form_response_lookup', 'form_id', 'user_id'),
        db.Index('idx_submitted_responses', 'form_id', 'is_submitted'),
    )
    
    def __init__(self, form_id, user_id, language='en', parent_response_id=None):
        self.form_id = form_id
        self.user_id = user_id
        self.language = language
        self.parent_response_id = parent_response_id
        self.is_submitted = False
        self.is_withdrawn = False
        self.started_timestamp = datetime.now()


class FormAnswer(db.Model):
    """Individual answer to a question."""
    __tablename__ = 'form_answer'
    
    id = db.Column(db.Integer(), primary_key=True)
    response_id = db.Column(db.Integer(), 
                           db.ForeignKey('form_response.id'), nullable=False)
    question_id = db.Column(db.Integer(), 
                           db.ForeignKey('form_question.id'), nullable=False)
    
    value = db.Column(db.Text(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    created_on = db.Column(db.DateTime(), nullable=False)
    updated_on = db.Column(db.DateTime(), nullable=False)
    
    # For versioning/audit
    version = db.Column(db.Integer(), nullable=False, default=1)
    
    # Relationships
    response = db.relationship('FormResponse', back_populates='answers')
    question = db.relationship('FormQuestion', back_populates='answers')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_answer_lookup', 'question_id', 'response_id', 'is_active'),
        db.Index('idx_response_answers', 'response_id', 'is_active'),
    )
    
    def __init__(self, response_id, question_id, value):
        self.response_id = response_id
        self.question_id = question_id
        self.value = value
        self.is_active = True
        self.created_on = datetime.now()
        self.updated_on = datetime.now()
        self.version = 1
    
    def validate(self, language: str) -> Tuple[bool, Optional[ValidationError]]:
        """Validate answer against question rules."""
        question = self.question
        translation = question.get_translation(language)
        
        # Required check
        if question.is_required and not self.value:
            return False, ValidationError.REQUIRED

        if not translation:
            LOGGER.warning(f"No translation found for question {question.id} in language {language}")
            return True, None
        
        # Regex validation
        if translation.validation_regex and self.value:
            if not re.match(translation.validation_regex, self.value):
                return False, ValidationError.VALIDATION_REGEX_FAILED
        
        # Option validation for multi-choice
        if translation.options:
            valid_values = [opt['value'] for opt in translation.options]
            values = self.value.split(' ; ')
            if not all(v.strip() in valid_values for v in values):
                return False, ValidationError.INVALID_OPTION
        
        return True, None
