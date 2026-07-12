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

  const renderValueInput = (questionId, currentValues, onChangeVal, placeholder, isBetween = false) => {
    const selectedQuestion = getSelectedQuestion(questionId);
    if (!selectedQuestion || !selectedQuestion.type) {
      return <input type="text" value={currentValues} onChange={(e) => onChangeVal(e.target.value)} placeholder={placeholder} className={inputCls} />;
    }
    if (isCountryQuestion(selectedQuestion.type)) {
      const selectedCodes = currentValues.split(',').map(v => v.trim()).filter(v => v);
      return (
        <div className="w-full">
          <select multiple value={selectedCodes} onChange={(e) => { const selected = Array.from(e.target.selectedOptions, o => o.value); onChangeVal(selected.join(', ')); }} className={inputCls} size={Math.min(5, ALL_COUNTRIES.length)}>
            {ALL_COUNTRIES.map(country => <option key={country.code} value={country.code}>{country.name} ({country.code})</option>)}
          </select>
          <span className="text-xs text-muted-foreground italic mt-1 block">{t('Hold Ctrl/Cmd to select multiple countries')}</span>
        </div>
      );
    }
    if (hasOptions(selectedQuestion.type) && selectedQuestion.options && selectedQuestion.options.length > 0) {
      const selectedValues = currentValues.split(',').map(v => v.trim()).filter(v => v);
      return (
        <div className="w-full">
          <select multiple value={selectedValues} onChange={(e) => { const selected = Array.from(e.target.selectedOptions, o => o.value); onChangeVal(selected.join(', ')); }} className={inputCls} size={Math.min(5, selectedQuestion.options.length)}>
            {selectedQuestion.options.map(option => { const firstLang = Object.keys(option.labels)[0]; const label = option.labels[firstLang] || option.value; return <option key={option.id} value={option.value}>{label}</option>; })}
          </select>
          <span className="text-xs text-muted-foreground italic mt-1 block">{t('Hold Ctrl/Cmd to select multiple values')}</span>
        </div>
      );
    }
    return <input type="text" value={currentValues} onChange={(e) => onChangeVal(e.target.value)} placeholder={placeholder} className={inputCls} />;
  };

  const handleModeChange = (newMode) => {
    setMode(newMode);
    if (newMode === 'simple') {
      const newExpression = { question_id: '', operator: 'EQUALS', values: [''] };
      setExpression(newExpression); setRawValueInput(''); onChange(newExpression);
    } else {
      const newExpression = { operator: 'AND', conditions: [] };
      setExpression(newExpression); onChange(newExpression);
    }
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
            {renderValueInput(expression.question_id, rawValueInput, handleValuesChange, isBetween ? t('e.g., 18, 65') : t('e.g., yes, maybe (comma-separated)'), isBetween)}
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
              {renderValueInput(condition.question_id, (condition.values || ['']).join(', '), (value) => updateConditionValues(path, value), isBetween ? t('min, max') : t('value(s)'), isBetween)}
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

  const handleClear = () => { setExpression(null); onChange(null); };

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
