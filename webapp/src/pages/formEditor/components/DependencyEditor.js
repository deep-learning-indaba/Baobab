import React, { useState, useEffect } from 'react';
import { formServices } from '../../../services/form/form.service';
import { ALL_COUNTRIES } from '../../../utils/countryData';
import './DependencyEditor.css';

const COMPARISON_OPERATORS = [
  { value: 'EQUALS', label: 'Equals' },
  { value: 'NOT_EQUALS', label: 'Not Equals' },
  { value: 'IN', label: 'In (any of)' },
  { value: 'NOT_IN', label: 'Not In (none of)' },
  { value: 'GREATER_THAN', label: 'Greater Than' },
  { value: 'LESS_THAN', label: 'Less Than' },
  { value: 'GREATER_THAN_OR_EQUAL', label: 'Greater Than or Equal' },
  { value: 'LESS_THAN_OR_EQUAL', label: 'Less Than or Equal' },
  { value: 'BETWEEN', label: 'Between' },
  { value: 'CONTAINS', label: 'Contains' },
  { value: 'STARTS_WITH', label: 'Starts With' },
  { value: 'ENDS_WITH', label: 'Ends With' },
  { value: 'REGEX', label: 'Regex Match' },
  { value: 'IS_EMPTY', label: 'Is Empty' },
  { value: 'IS_NOT_EMPTY', label: 'Is Not Empty' }
];

const LOGICAL_OPERATORS = [
  { value: 'AND', label: 'AND (all must be true)' },
  { value: 'OR', label: 'OR (any can be true)' },
  { value: 'NOT', label: 'NOT (negate condition)' }
];

const DependencyEditor = ({ 
  dependencyExpression, 
  onChange, 
  availableQuestions, 
  currentQuestionId,
  currentSectionOrder,
  currentQuestionOrder,
  linkedFormId,
  t 
}) => {
  const [mode, setMode] = useState('simple');
  const [expression, setExpression] = useState(null);
  const [rawValueInput, setRawValueInput] = useState('');
  const [isInitialized, setIsInitialized] = useState(false);
  const [showJsonPreview, setShowJsonPreview] = useState(false);
  const [linkedFormQuestions, setLinkedFormQuestions] = useState([]);
  const [loadingLinkedQuestions, setLoadingLinkedQuestions] = useState(false);

  useEffect(() => {
    if (!isInitialized) {
      if (dependencyExpression) {
        setExpression(dependencyExpression);
        
        if (dependencyExpression.operator && 
            ['AND', 'OR', 'NOT'].includes(dependencyExpression.operator)) {
          setMode('advanced');
        } else {
          setMode('simple');
          if (dependencyExpression.values) {
            setRawValueInput(dependencyExpression.values.join(', '));
          }
        }
      } else {
        const initialExpression = {
          question_id: '',
          operator: 'EQUALS',
          values: ['']
        };
        setExpression(initialExpression);
        setRawValueInput('');
      }
      setIsInitialized(true);
    }
  }, [dependencyExpression, isInitialized]);

  useEffect(() => {
    if (!linkedFormId) {
      setLinkedFormQuestions([]);
      return;
    }

    const fetchLinkedFormQuestions = async () => {
      setLoadingLinkedQuestions(true);
      try {
        const response = await formServices.getForm(linkedFormId);
        if (response.form && response.form.sections) {
          const allQuestions = [];
          response.form.sections.forEach((section) => {
            const sectionName = typeof section.name === 'object' 
              ? (section.name.en || Object.values(section.name)[0]) 
              : section.name;
            
            section.questions.forEach((question) => {
              const questionHeadline = typeof question.headline === 'object'
                ? (question.headline.en || Object.values(question.headline)[0])
                : question.headline;
              
              allQuestions.push({
                id: question.id,
                headline: questionHeadline || `Question ${question.order}`,
                sectionName: sectionName,
                sectionOrder: section.order,
                order: question.order,
                type: question.type,
                options: question.options || [],
                isLinked: true
              });
            });
          });
          setLinkedFormQuestions(allQuestions);
        }
      } catch (err) {
        console.error('Error fetching linked form questions:', err);
      } finally {
        setLoadingLinkedQuestions(false);
      }
    };

    fetchLinkedFormQuestions();
  }, [linkedFormId]);

  const getAvailableQuestions = () => {
    const currentFormQuestions = availableQuestions.filter(q => {
      // Exclude the current question
      if (q.id === currentQuestionId) return false;
      
      // For section dependencies (no current question), show all questions from previous sections
      if (currentQuestionOrder === undefined || currentQuestionOrder === null) {
        return q.sectionOrder < currentSectionOrder;
      }
      
      // For question dependencies, show:
      // 1. Questions from previous sections (lower section order)
      // 2. Questions from the same section that appear before (lower question order)
      if (q.sectionOrder < currentSectionOrder) {
        return true;
      }
      
      if (q.sectionOrder === currentSectionOrder && q.order < currentQuestionOrder) {
        return true;
      }
      
      return false;
    });

    return [...currentFormQuestions, ...linkedFormQuestions];
  };

  const getSelectedQuestion = (questionId) => {
    const allQuestions = [...availableQuestions, ...linkedFormQuestions];
    return allQuestions.find(q => q.id === questionId);
  };

  const hasOptions = (questionType) => {
    return ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(questionType);
  };

  const isCountryQuestion = (questionType) => {
    return questionType === 'country';
  };

  const renderValueInput = (questionId, currentValues, onChange, placeholder, isBetween = false) => {
    const selectedQuestion = getSelectedQuestion(questionId);
    
    if (!selectedQuestion || !selectedQuestion.type) {
      // Default text input if no question selected or type unknown
      return (
        <input
          type="text"
          value={currentValues}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="dependency-input"
        />
      );
    }

    // For country questions, show multi-select with countries
    if (isCountryQuestion(selectedQuestion.type)) {
      const selectedCodes = currentValues.split(',').map(v => v.trim()).filter(v => v);
      
      return (
        <div className="dependency-value-multiselect">
          <select
            multiple
            value={selectedCodes}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              onChange(selected.join(', '));
            }}
            className="dependency-select-multiple"
            size={Math.min(5, ALL_COUNTRIES.length)}
          >
            {ALL_COUNTRIES.map(country => (
              <option key={country.code} value={country.code}>
                {country.name} ({country.code})
              </option>
            ))}
          </select>
          <span className="dependency-hint">
            {t('Hold Ctrl/Cmd to select multiple countries')}
          </span>
        </div>
      );
    }

    // For questions with options, show multi-select with those options
    if (hasOptions(selectedQuestion.type) && selectedQuestion.options && selectedQuestion.options.length > 0) {
      const selectedValues = currentValues.split(',').map(v => v.trim()).filter(v => v);
      
      return (
        <div className="dependency-value-multiselect">
          <select
            multiple
            value={selectedValues}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              onChange(selected.join(', '));
            }}
            className="dependency-select-multiple"
            size={Math.min(5, selectedQuestion.options.length)}
          >
            {selectedQuestion.options.map(option => {
              const firstLang = Object.keys(option.labels)[0];
              const label = option.labels[firstLang] || option.value;
              return (
                <option key={option.id} value={option.value}>
                  {label}
                </option>
              );
            })}
          </select>
          <span className="dependency-hint">
            {t('Hold Ctrl/Cmd to select multiple values')}
          </span>
        </div>
      );
    }

    // Default to text input for other question types
    return (
      <input
        type="text"
        value={currentValues}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="dependency-input"
      />
    );
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    
    if (newMode === 'simple') {
      const newExpression = {
        question_id: '',
        operator: 'EQUALS',
        values: ['']
      };
      setExpression(newExpression);
      setRawValueInput('');
      onChange(newExpression);
    } else {
      const newExpression = {
        operator: 'AND',
        conditions: []
      };
      setExpression(newExpression);
      onChange(newExpression);
    }
  };

  const handleSimpleChange = (field, value) => {
    const newExpression = { ...expression, [field]: value };
    setExpression(newExpression);
    onChange(newExpression);
  };

  const handleValuesChange = (valueString) => {
    setRawValueInput(valueString);
    const values = valueString
      .split(',')
      .map(v => v.trim())
      .filter(v => v !== '');
    handleSimpleChange('values', values.length > 0 ? values : ['']);
  };

  const addCondition = (parentPath = []) => {
    const newCondition = {
      question_id: '',
      operator: 'EQUALS',
      values: ['']
    };

    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    
    for (const key of parentPath) {
      target = target.conditions[key];
    }
    
    if (!target.conditions) {
      target.conditions = [];
    }
    target.conditions.push(newCondition);
    
    setExpression(newExpression);
    onChange(newExpression);
  };

  const addLogicalGroup = (parentPath = [], logicalOp = 'AND') => {
    const newGroup = {
      operator: logicalOp,
      conditions: []
    };

    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    
    for (const key of parentPath) {
      target = target.conditions[key];
    }
    
    if (!target.conditions) {
      target.conditions = [];
    }
    target.conditions.push(newGroup);
    
    setExpression(newExpression);
    onChange(newExpression);
  };

  const updateCondition = (path, field, value) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    
    for (let i = 0; i < path.length - 1; i++) {
      target = target.conditions[path[i]];
    }
    
    const conditionIndex = path[path.length - 1];
    target.conditions[conditionIndex][field] = value;
    
    setExpression(newExpression);
    onChange(newExpression);
  };

  const updateConditionValues = (path, valueString) => {
    const values = valueString
      .split(',')
      .map(v => v.trim())
      .filter(v => v !== '');
    updateCondition(path, 'values', values.length > 0 ? values : ['']);
  };

  const removeCondition = (path) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    
    for (let i = 0; i < path.length - 1; i++) {
      target = target.conditions[path[i]];
    }
    
    const conditionIndex = path[path.length - 1];
    target.conditions.splice(conditionIndex, 1);
    
    setExpression(newExpression);
    onChange(newExpression);
  };

  const changeLogicalOperator = (path, newOperator) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    
    for (const key of path) {
      target = target.conditions[key];
    }
    
    target.operator = newOperator;
    
    setExpression(newExpression);
    onChange(newExpression);
  };

  const renderSimpleMode = () => {
    if (!expression) return null;

    const needsValues = expression.operator && 
      !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(expression.operator);
    
    const isBetween = expression.operator === 'BETWEEN';

    return (
      <div className="dependency-simple-mode">
        <div className="dependency-field">
          <label>{t('Show this when')}</label>
          <select
            value={expression.question_id || ''}
            onChange={(e) => handleSimpleChange('question_id', e.target.value)}
            className="dependency-select"
          >
            <option value="">{t('Select a question...')}</option>
            {getAvailableQuestions().map(q => {
              const headline = q.headline && typeof q.headline === 'object' 
                ? (q.headline[Object.keys(q.headline)[0]] || t('Untitled Question'))
                : (q.headline || t('Untitled Question'));
              const prefix = q.isLinked ? `[Linked] ${q.sectionName} - ` : `Q${q.order}: `;
              return (
                <option key={q.id} value={q.id}>
                  {prefix}{headline}
                </option>
              );
            })}
          </select>
        </div>

        <div className="dependency-field">
          <label>{t('Condition')}</label>
          <select
            value={expression.operator || 'EQUALS'}
            onChange={(e) => handleSimpleChange('operator', e.target.value)}
            className="dependency-select"
          >
            {COMPARISON_OPERATORS.map(op => (
              <option key={op.value} value={op.value}>{t(op.label)}</option>
            ))}
          </select>
        </div>

        {needsValues && (
          <div className="dependency-field">
            <label>
              {isBetween ? t('Values (min, max)') : t('Value(s)')}
            </label>
            {renderValueInput(
              expression.question_id,
              rawValueInput,
              handleValuesChange,
              isBetween ? t('e.g., 18, 65') : t('e.g., yes, maybe (comma-separated)'),
              isBetween
            )}
          </div>
        )}
      </div>
    );
  };

  const renderCondition = (condition, path, isRoot = false) => {
    if (condition.operator && ['AND', 'OR', 'NOT'].includes(condition.operator)) {
      return renderLogicalGroup(condition, path, isRoot);
    }

    const needsValues = condition.operator && 
      !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(condition.operator);
    
    const isBetween = condition.operator === 'BETWEEN';

    return (
      <div className="dependency-condition" key={path.join('-')}>
        <div className="dependency-condition-content">
          <select
            value={condition.question_id || ''}
            onChange={(e) => updateCondition(path, 'question_id', e.target.value)}
            className="dependency-select-small"
          >
            <option value="">{t('Select question...')}</option>
            {getAvailableQuestions().map(q => {
              const headline = q.headline && typeof q.headline === 'object' 
                ? (q.headline[Object.keys(q.headline)[0]] || t('Untitled'))
                : (q.headline || t('Untitled'));
              const prefix = q.isLinked ? `[Linked] ${q.sectionName} - ` : `Q${q.order}: `;
              return (
                <option key={q.id} value={q.id}>
                  {prefix}{headline}
                </option>
              );
            })}
          </select>

          <select
            value={condition.operator || 'EQUALS'}
            onChange={(e) => updateCondition(path, 'operator', e.target.value)}
            className="dependency-select-small"
          >
            {COMPARISON_OPERATORS.map(op => (
              <option key={op.value} value={op.value}>{t(op.label)}</option>
            ))}
          </select>

          {needsValues && (
            <div className="dependency-condition-value">
              {renderValueInput(
                condition.question_id,
                (condition.values || ['']).join(', '),
                (value) => updateConditionValues(path, value),
                isBetween ? t('min, max') : t('value(s)'),
                isBetween
              )}
            </div>
          )}
        </div>

        <button
          type="button"
          className="dependency-remove-btn"
          onClick={() => removeCondition(path)}
          title={t('Remove condition')}
        >
          <i className="fas fa-times"></i>
        </button>
      </div>
    );
  };

  const renderLogicalGroup = (group, path, isRoot = false) => {
    return (
      <div className={`dependency-logical-group ${isRoot ? 'root' : ''}`} key={path.join('-')}>
        <div className="dependency-logical-header">
          <select
            value={group.operator}
            onChange={(e) => changeLogicalOperator(path, e.target.value)}
            className="dependency-logical-select"
          >
            {LOGICAL_OPERATORS.map(op => (
              <option key={op.value} value={op.value}>{t(op.label)}</option>
            ))}
          </select>
          
          {!isRoot && (
            <button
              type="button"
              className="dependency-remove-btn"
              onClick={() => removeCondition(path)}
              title={t('Remove group')}
            >
              <i className="fas fa-times"></i>
            </button>
          )}
        </div>

        <div className="dependency-conditions-list">
          {(group.conditions || []).map((condition, index) => (
            renderCondition(condition, [...path, index])
          ))}
        </div>

        <div className="dependency-group-actions">
          <button
            type="button"
            className="dependency-add-btn"
            onClick={() => addCondition(path)}
          >
            <i className="fas fa-plus"></i>
            {t('Add Condition')}
          </button>
          <button
            type="button"
            className="dependency-add-btn"
            onClick={() => addLogicalGroup(path, 'AND')}
          >
            <i className="fas fa-plus"></i>
            {t('Add AND Group')}
          </button>
          <button
            type="button"
            className="dependency-add-btn"
            onClick={() => addLogicalGroup(path, 'OR')}
          >
            <i className="fas fa-plus"></i>
            {t('Add OR Group')}
          </button>
        </div>
      </div>
    );
  };

  const renderAdvancedMode = () => {
    if (!expression) return null;

    return (
      <div className="dependency-advanced-mode">
        {renderCondition(expression, [], true)}
      </div>
    );
  };

  const handleClear = () => {
    setExpression(null);
    onChange(null);
  };

  return (
    <div className="dependency-editor">
      <div className="dependency-header">
        <h4>{t('Dependency Settings')}</h4>
        <button
          type="button"
          className="dependency-clear-btn"
          onClick={handleClear}
        >
          {t('Clear All')}
        </button>
      </div>

      <div className="dependency-mode-toggle">
        <label className="radio-option">
          <input
            type="radio"
            name="dependency-mode"
            value="simple"
            checked={mode === 'simple'}
            onChange={() => handleModeChange('simple')}
          />
          <span>{t('Simple')}</span>
        </label>
        <label className="radio-option">
          <input
            type="radio"
            name="dependency-mode"
            value="advanced"
            checked={mode === 'advanced'}
            onChange={() => handleModeChange('advanced')}
          />
          <span>{t('Advanced')}</span>
        </label>
      </div>

      <div className="dependency-description">
        {mode === 'simple' 
          ? t('Show this item only when a single question meets a condition')
          : t('Build complex conditions with AND, OR, and NOT logic')
        }
      </div>

      {mode === 'simple' ? renderSimpleMode() : renderAdvancedMode()}

      {expression && (
        <div className="dependency-preview">
          <div className="dependency-preview-header">
            <label>{t('JSON Preview')}</label>
            <button
              type="button"
              className="dependency-preview-toggle"
              onClick={() => setShowJsonPreview(!showJsonPreview)}
            >
              <i className={`fas fa-chevron-${showJsonPreview ? 'up' : 'down'}`}></i>
              {showJsonPreview ? t('Hide') : t('Show')}
            </button>
          </div>
          {showJsonPreview && (
            <pre className="dependency-json">
              {JSON.stringify(expression, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

export default DependencyEditor;
