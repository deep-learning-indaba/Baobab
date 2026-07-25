import React, { useState, useEffect } from 'react';
import { formServices } from '../../../services/form/form.service';
import { ALL_COUNTRIES } from '../../../utils/countryData';

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

// Operators that compare against a single value. Offering a multi-select for
// these would let an admin select several options for EQUALS when only the
// first is ever compared.
const SINGLE_VALUE_OPERATORS = [
  'EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'LESS_THAN',
  'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL',
  'CONTAINS', 'STARTS_WITH', 'ENDS_WITH', 'REGEX'
];

// Types whose answer is a separator-joined list of selected values, so an
// equality or membership test against a single option can never match.
const MULTI_VALUE_TYPES = ['checkboxes'];

/** Flatten a (possibly nested) expression down to its leaf conditions. */
function collectLeafConditions(expression) {
  if (!expression) return [];
  if (expression.question_id !== undefined) return [expression];
  if (Array.isArray(expression.conditions)) {
    return expression.conditions.flatMap(collectLeafConditions);
  }
  return [];
}

const inputCls = "w-full px-3 py-2 border border-border rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-ring";
const selectCls = "w-full px-3 py-2 border border-border rounded-md text-sm bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring";
const selectSmCls = "px-2 py-1.5 border border-border rounded-md text-xs bg-white cursor-pointer focus:outline-none focus:ring-1 focus:ring-ring min-w-[150px]";

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
  const [, setLoadingLinkedQuestions] = useState(false);

  useEffect(() => {
    if (!isInitialized) {
      if (dependencyExpression) {
        setExpression(dependencyExpression);
        if (dependencyExpression.operator && ['AND', 'OR', 'NOT'].includes(dependencyExpression.operator)) {
          setMode('advanced');
        } else {
          setMode('simple');
          if (dependencyExpression.values) setRawValueInput(dependencyExpression.values.join(', '));
        }
      } else {
        setExpression({ question_id: '', operator: 'EQUALS', values: [''] });
        setRawValueInput('');
      }
      setIsInitialized(true);
    }
  }, [dependencyExpression, isInitialized]);

  useEffect(() => {
    if (!linkedFormId) { setLinkedFormQuestions([]); return; }
    const fetchLinkedFormQuestions = async () => {
      setLoadingLinkedQuestions(true);
      try {
        const response = await formServices.getForm(linkedFormId);
        if (response.form && response.form.sections) {
          const allQuestions = [];
          response.form.sections.forEach((section) => {
            const sectionName = typeof section.name === 'object' ? (section.name.en || Object.values(section.name)[0]) : section.name;
            section.questions.forEach((question) => {
              const questionHeadline = typeof question.headline === 'object' ? (question.headline.en || Object.values(question.headline)[0]) : question.headline;
              allQuestions.push({ id: question.id, headline: questionHeadline || `Question ${question.order}`, sectionName, sectionOrder: section.order, order: question.order, type: question.type, options: question.options || [], isLinked: true });
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
      if (q.id === currentQuestionId) return false;
      if (currentQuestionOrder === undefined || currentQuestionOrder === null) return q.sectionOrder < currentSectionOrder;
      if (q.sectionOrder < currentSectionOrder) return true;
      if (q.sectionOrder === currentSectionOrder && q.order < currentQuestionOrder) return true;
      return false;
    });
    return [...currentFormQuestions, ...linkedFormQuestions];
  };

  const getSelectedQuestion = (questionId) => [...availableQuestions, ...linkedFormQuestions].find(q => q.id === questionId);

  const hasOptions = (questionType) => ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(questionType);
  const isCountryQuestion = (questionType) => questionType === 'country';

  // Options come back from the API as { en: [...], fr: [...] } for a linked
  // form, and as the editor's unified [{ value, labels }] for this form.
  const optionListFor = (question) => {
    const opts = question && question.options;
    if (!opts) return [];
    if (Array.isArray(opts)) {
      return opts.map(o => ({
        value: o.value,
        label: o.labels ? (o.labels[Object.keys(o.labels)[0]] || o.value) : (o.label || o.value)
      }));
    }
    const byLang = opts.en || Object.values(opts)[0] || [];
    return Array.isArray(byLang)
      ? byLang.map(o => ({ value: o.value, label: o.label || o.value }))
      : [];
  };

  const renderValueInput = (questionId, currentValues, onChangeVal, placeholder, operator, isBetween = false) => {
    const selectedQuestion = getSelectedQuestion(questionId);
    const allowsMultiple = !SINGLE_VALUE_OPERATORS.includes(operator) && !isBetween;

    if (!selectedQuestion || !selectedQuestion.type) {
      return <input type="text" value={currentValues} onChange={(e) => onChangeVal(e.target.value)} placeholder={placeholder} className={inputCls} />;
    }

    const renderChoice = (choices, hint) => {
      const selected = currentValues.split(',').map(v => v.trim()).filter(v => v);
      if (allowsMultiple) {
        return (
          <div className="w-full">
            <select
              multiple
              value={selected}
              onChange={(e) => onChangeVal(Array.from(e.target.selectedOptions, o => o.value).join(', '))}
              className={inputCls}
              size={Math.min(5, choices.length)}
            >
              {choices.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            <span className="text-xs text-muted-foreground italic mt-1 block">{hint}</span>
          </div>
        );
      }
      // Single-value operator: a single select, so the extra selections that
      // would have been silently ignored can't be made in the first place.
      return (
        <select
          value={selected[0] || ''}
          onChange={(e) => onChangeVal(e.target.value)}
          className={selectCls}
        >
          <option value="">{t('Select a value...')}</option>
          {choices.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      );
    };

    if (isCountryQuestion(selectedQuestion.type)) {
      return renderChoice(
        ALL_COUNTRIES.map(c => ({ value: c.code, label: `${c.name} (${c.code})` })),
        t('Hold Ctrl/Cmd to select multiple countries')
      );
    }

    const choices = hasOptions(selectedQuestion.type) ? optionListFor(selectedQuestion) : [];
    if (choices.length > 0) {
      return renderChoice(choices, t('Hold Ctrl/Cmd to select multiple values'));
    }

    return <input type="text" value={currentValues} onChange={(e) => onChangeVal(e.target.value)} placeholder={placeholder} className={inputCls} />;
  };

  // Checkbox answers are stored as a joined list, so EQUALS/IN against one
  // option never matches. Say so rather than letting the admin build a rule
  // that silently never fires.
  const multiValueWarning = (questionId, operator) => {
    const q = getSelectedQuestion(questionId);
    if (!q || !MULTI_VALUE_TYPES.includes(q.type)) return null;
    if (!['EQUALS', 'NOT_EQUALS', 'IN', 'NOT_IN'].includes(operator)) return null;
    return t('This question allows several answers at once. Use "Contains" to test for one of them.');
  };

  // Simple -> Advanced wraps the existing condition in an AND group rather than
  // discarding it. Advanced -> Simple keeps the first leaf condition, confirming
  // first if that would drop others - switching modes must not silently throw
  // away whatever the admin has already built.
  const handleModeChange = (newMode) => {
    if (newMode === mode) return;

    if (newMode === 'advanced') {
      const isLeaf = expression && expression.question_id !== undefined && expression.question_id !== '';
      const newExpression = isLeaf
        ? { operator: 'AND', conditions: [expression] }
        : { operator: 'AND', conditions: [] };
      setMode('advanced');
      setExpression(newExpression);
      onChange(newExpression);
      return;
    }

    const leaves = collectLeafConditions(expression);
    if (leaves.length > 1 && !window.confirm(
      t('Simple mode keeps only the first condition. Discard the others?')
    )) {
      return;
    }
    const kept = leaves[0] || { question_id: '', operator: 'EQUALS', values: [''] };
    setMode('simple');
    setExpression(kept);
    setRawValueInput((kept.values || []).join(', '));
    onChange(kept);
  };

  const handleSimpleChange = (field, value) => { const newExpression = { ...expression, [field]: value }; setExpression(newExpression); onChange(newExpression); };

  const handleValuesChange = (valueString) => {
    setRawValueInput(valueString);
    const values = valueString.split(',').map(v => v.trim()).filter(v => v !== '');
    handleSimpleChange('values', values.length > 0 ? values : ['']);
  };

  const addCondition = (parentPath = []) => {
    const newCondition = { question_id: '', operator: 'EQUALS', values: [''] };
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    for (const key of parentPath) target = target.conditions[key];
    if (!target.conditions) target.conditions = [];
    target.conditions.push(newCondition);
    setExpression(newExpression); onChange(newExpression);
  };

  const addLogicalGroup = (parentPath = [], logicalOp = 'AND') => {
    const newGroup = { operator: logicalOp, conditions: [] };
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    for (const key of parentPath) target = target.conditions[key];
    if (!target.conditions) target.conditions = [];
    target.conditions.push(newGroup);
    setExpression(newExpression); onChange(newExpression);
  };

  const updateCondition = (path, field, value) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    for (let i = 0; i < path.length - 1; i++) target = target.conditions[path[i]];
    target.conditions[path[path.length - 1]][field] = value;
    setExpression(newExpression); onChange(newExpression);
  };

  const updateConditionValues = (path, valueString) => {
    const values = valueString.split(',').map(v => v.trim()).filter(v => v !== '');
    updateCondition(path, 'values', values.length > 0 ? values : ['']);
  };

  const removeCondition = (path) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    for (let i = 0; i < path.length - 1; i++) target = target.conditions[path[i]];
    target.conditions.splice(path[path.length - 1], 1);
    setExpression(newExpression); onChange(newExpression);
  };

  const changeLogicalOperator = (path, newOperator) => {
    const newExpression = JSON.parse(JSON.stringify(expression));
    let target = newExpression;
    for (const key of path) target = target.conditions[key];
    target.operator = newOperator;
    setExpression(newExpression); onChange(newExpression);
  };

  const renderSimpleMode = () => {
    if (!expression) return null;
    const needsValues = expression.operator && !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(expression.operator);
    const isBetween = expression.operator === 'BETWEEN';
    return (
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">{t('Show this when')}</label>
          <select value={expression.question_id || ''} onChange={(e) => handleSimpleChange('question_id', e.target.value)} className={selectCls}>
            <option value="">{t('Select a question...')}</option>
            {getAvailableQuestions().map(q => {
              const headline = q.headline && typeof q.headline === 'object' ? (q.headline[Object.keys(q.headline)[0]] || t('Untitled Question')) : (q.headline || t('Untitled Question'));
              const prefix = q.isLinked ? `[Linked] ${q.sectionName} - ` : `Q${q.order}: `;
              return <option key={q.id} value={q.id}>{prefix}{headline}</option>;
            })}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-semibold text-foreground">{t('Condition')}</label>
          <select value={expression.operator || 'EQUALS'} onChange={(e) => handleSimpleChange('operator', e.target.value)} className={selectCls}>
            {COMPARISON_OPERATORS.map(op => <option key={op.value} value={op.value}>{t(op.label)}</option>)}
          </select>
        </div>
        {needsValues && (
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">
              {isBetween ? t('Values (min, max)') : t('Value(s)')}
            </label>
            {renderValueInput(expression.question_id, rawValueInput, handleValuesChange, isBetween ? t('e.g., 18, 65') : t('e.g., yes, maybe (comma-separated)'), expression.operator, isBetween)}
            {multiValueWarning(expression.question_id, expression.operator) && (
              <p className="text-warning text-xs flex items-center gap-1.5">
                <i className="fas fa-exclamation-triangle"></i>
                {multiValueWarning(expression.question_id, expression.operator)}
              </p>
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
    const needsValues = condition.operator && !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(condition.operator);
    const isBetween = condition.operator === 'BETWEEN';
    return (
      <div key={path.join('-')} className="flex items-center gap-2 bg-surface p-3 rounded-md border border-border">
        <div className="flex items-center gap-2 flex-1 flex-wrap">
          <select value={condition.question_id || ''} onChange={(e) => updateCondition(path, 'question_id', e.target.value)} className={selectSmCls}>
            <option value="">{t('Select question...')}</option>
            {getAvailableQuestions().map(q => {
              const headline = q.headline && typeof q.headline === 'object' ? (q.headline[Object.keys(q.headline)[0]] || t('Untitled')) : (q.headline || t('Untitled'));
              const prefix = q.isLinked ? `[Linked] ${q.sectionName} - ` : `Q${q.order}: `;
              return <option key={q.id} value={q.id}>{prefix}{headline}</option>;
            })}
          </select>
          <select value={condition.operator || 'EQUALS'} onChange={(e) => updateCondition(path, 'operator', e.target.value)} className={selectSmCls}>
            {COMPARISON_OPERATORS.map(op => <option key={op.value} value={op.value}>{t(op.label)}</option>)}
          </select>
          {needsValues && (
            <div className="flex-1 min-w-0">
              {renderValueInput(condition.question_id, (condition.values || ['']).join(', '), (value) => updateConditionValues(path, value), isBetween ? t('min, max') : t('value(s)'), condition.operator, isBetween)}
              {multiValueWarning(condition.question_id, condition.operator) && (
                <p className="text-warning text-xs mt-1 flex items-center gap-1.5">
                  <i className="fas fa-exclamation-triangle"></i>
                  {multiValueWarning(condition.question_id, condition.operator)}
                </p>
              )}
            </div>
          )}
        </div>
        <button type="button" onClick={() => removeCondition(path)} title={t('Remove condition')} className="flex-shrink-0 px-2 py-1.5 bg-error text-white rounded text-xs hover:opacity-90 transition-opacity">
          <i className="fas fa-times"></i>
        </button>
      </div>
    );
  };

  const renderLogicalGroup = (group, path, isRoot = false) => (
    <div key={path.join('-')} className={`bg-white rounded-md p-4 mb-3 border-2 ${isRoot ? 'border-primary' : 'border-action'}`}>
      <div className="flex items-center gap-3 mb-4">
        <select value={group.operator} onChange={(e) => changeLogicalOperator(path, e.target.value)} className={`px-3 py-1.5 border-2 rounded-md text-sm font-semibold cursor-pointer ${isRoot ? 'border-primary bg-primary/5 text-primary' : 'border-action bg-action/5 text-action'}`}>
          {LOGICAL_OPERATORS.map(op => <option key={op.value} value={op.value}>{t(op.label)}</option>)}
        </select>
        {!isRoot && (
          <button type="button" onClick={() => removeCondition(path)} title={t('Remove group')} className="px-2 py-1.5 bg-error text-white rounded text-xs hover:opacity-90 transition-opacity">
            <i className="fas fa-times"></i>
          </button>
        )}
      </div>
      <div className="flex flex-col gap-2.5 ml-5 pl-4 border-l-2 border-border">
        {(group.conditions || []).map((condition, index) => renderCondition(condition, [...path, index]))}
      </div>
      <div className="flex gap-2 mt-3 flex-wrap">
        {[
          { label: t('Add Condition'), onClick: () => addCondition(path) },
          { label: t('Add AND Group'), onClick: () => addLogicalGroup(path, 'AND') },
          { label: t('Add OR Group'), onClick: () => addLogicalGroup(path, 'OR') }
        ].map(({ label, onClick }) => (
          <button key={label} type="button" onClick={onClick} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white rounded-md text-xs font-medium hover:bg-primary-container transition-colors">
            <i className="fas fa-plus text-[10px]"></i>{label}
          </button>
        ))}
      </div>
    </div>
  );

  // Reset to an empty condition rather than null, so the panel offers a way to
  // add a condition back without toggling modes. The dependency is only
  // actually saved once a question is chosen (an empty question_id serialises
  // to no dependency).
  const handleClear = () => {
    const fresh = { question_id: '', operator: 'EQUALS', values: [''] };
    setMode('simple');
    setExpression(fresh);
    setRawValueInput('');
    onChange(null);
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-5 mt-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-base font-semibold text-foreground m-0">{t('Dependency Settings')}</h4>
        <button type="button" onClick={handleClear} className="px-3 py-1.5 bg-error text-white rounded-md text-xs font-medium hover:opacity-90 transition-opacity">
          {t('Clear All')}
        </button>
      </div>

      {/* Mode toggle — segmented control */}
      <div className="inline-flex bg-surface-mid rounded-lg p-1 gap-0 mb-4">
        {[{ value: 'simple', label: t('Simple') }, { value: 'advanced', label: t('Advanced') }].map(opt => (
          <label key={opt.value} className="relative cursor-pointer">
            <input type="radio" name="dependency-mode" value={opt.value} checked={mode === opt.value} onChange={() => handleModeChange(opt.value)} className="sr-only peer" />
            <span className="block px-4 py-1.5 text-sm font-medium text-muted-foreground rounded-md transition-all peer-checked:bg-white peer-checked:text-foreground peer-checked:shadow-sm">
              {opt.label}
            </span>
          </label>
        ))}
      </div>

      {/* Description callout */}
      <div className="mb-5 px-4 py-3 bg-action/5 border-l-4 border-action rounded-r-md text-xs text-action/80">
        {mode === 'simple' ? t('Show this item only when a single question meets a condition') : t('Build complex conditions with AND, OR, and NOT logic')}
      </div>

      {mode === 'simple' ? renderSimpleMode() : <div className="mt-3">{expression && renderCondition(expression, [], true)}</div>}

      {/* JSON Preview */}
      {expression && (
        <div className="mt-5 p-4 bg-white border border-border rounded-md">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-semibold text-muted-foreground m-0">{t('JSON Preview')}</label>
            <button type="button" onClick={() => setShowJsonPreview(!showJsonPreview)} className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface border border-border rounded text-xs text-muted-foreground hover:bg-surface-mid transition-colors">
              <i className={`fas fa-chevron-${showJsonPreview ? 'up' : 'down'} text-[10px]`}></i>
              {showJsonPreview ? t('Hide') : t('Show')}
            </button>
          </div>
          {showJsonPreview && (
            <pre className="bg-surface border border-border rounded p-3 text-xs font-mono text-foreground overflow-x-auto m-0">
              {JSON.stringify(expression, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};

export default DependencyEditor;
