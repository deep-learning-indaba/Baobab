import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './VisibilityExpressionEditor.css';

const VisibilityExpressionEditor = ({ expression, onChange }) => {
  const { t } = useTranslation();
  const [showEditor, setShowEditor] = useState(false);

  const createSimpleCondition = () => {
    return { tag: '' };
  };

  const createLogicalExpression = (operator) => {
    return {
      operator: operator,
      conditions: [createSimpleCondition()]
    };
  };

  const handleToggleEditor = () => {
    if (!showEditor && !expression) {
      onChange(createSimpleCondition());
    }
    setShowEditor(!showEditor);
  };

  const handleClear = () => {
    onChange(null);
    setShowEditor(false);
  };

  const renderConditionEditor = (condition, path, parentOperator) => {
    const isLogical = condition.operator && ['AND', 'OR', 'NOT'].includes(condition.operator);

    if (isLogical) {
      return (
        <div className="logical-condition" key={path}>
          <div className="logical-operator">
            <select
              value={condition.operator}
              onChange={(e) => updateCondition(path, { ...condition, operator: e.target.value })}
              className="operator-select"
            >
              <option value="AND">{t('AND (all must match)')}</option>
              <option value="OR">{t('OR (any can match)')}</option>
              <option value="NOT">{t('NOT (must not match)')}</option>
            </select>
            <button
              type="button"
              className="btn-icon btn-remove"
              onClick={() => removeCondition(path)}
              title={t('Remove')}
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
          <div className="nested-conditions">
            {(condition.conditions || []).map((subCond, index) => 
              renderConditionEditor(subCond, path + '.' + index, condition.operator)
            )}
            {condition.operator !== 'NOT' && (
              <div className="add-condition-buttons">
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => addCondition(path, createSimpleCondition())}
                >
                  <i className="fas fa-plus"></i> {t('Add Tag')}
                </button>
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => addCondition(path, createLogicalExpression('AND'))}
                >
                  <i className="fas fa-plus"></i> {t('Add Group')}
                </button>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="simple-condition" key={path}>
        <input
          type="text"
          className="form-control tag-input"
          value={condition.tag || ''}
          onChange={(e) => updateCondition(path, { ...condition, tag: e.target.value })}
          placeholder={t('Enter tag name (e.g., invited_guest, selected_attendee)')}
        />
        <button
          type="button"
          className="btn-icon btn-convert"
          onClick={() => convertToLogical(path, 'AND')}
          title={t('Convert to group')}
        >
          <i className="fas fa-layer-group"></i>
        </button>
        {parentOperator && (
          <button
            type="button"
            className="btn-icon btn-remove"
            onClick={() => removeCondition(path)}
            title={t('Remove')}
          >
            <i className="fas fa-times"></i>
          </button>
        )}
      </div>
    );
  };

  const updateCondition = (path, newCondition) => {
    const pathParts = path.split('.').filter(p => p);
    const newExpression = JSON.parse(JSON.stringify(expression));
    
    let current = newExpression;
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (part === 'conditions') {
        continue;
      }
      current = current.conditions[parseInt(part)];
    }
    
    if (pathParts.length === 0) {
      onChange(newCondition);
    } else {
      const lastPart = pathParts[pathParts.length - 1];
      if (current.conditions) {
        current.conditions[parseInt(lastPart)] = newCondition;
      }
      onChange(newExpression);
    }
  };

  const addCondition = (path, newCondition) => {
    const pathParts = path.split('.').filter(p => p);
    const newExpression = JSON.parse(JSON.stringify(expression));
    
    let current = newExpression;
    for (const part of pathParts) {
      if (part === 'conditions') {
        continue;
      }
      current = current.conditions[parseInt(part)];
    }
    
    if (!current.conditions) {
      current.conditions = [];
    }
    current.conditions.push(newCondition);
    onChange(newExpression);
  };

  const removeCondition = (path) => {
    const pathParts = path.split('.').filter(p => p);
    
    if (pathParts.length === 0) {
      onChange(null);
      return;
    }
    
    const newExpression = JSON.parse(JSON.stringify(expression));
    let current = newExpression;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (part === 'conditions') {
        continue;
      }
      current = current.conditions[parseInt(part)];
    }
    
    const lastPart = pathParts[pathParts.length - 1];
    current.conditions.splice(parseInt(lastPart), 1);
    
    onChange(newExpression);
  };

  const convertToLogical = (path, operator) => {
    const pathParts = path.split('.').filter(p => p);
    const newExpression = JSON.parse(JSON.stringify(expression));
    
    let current = newExpression;
    let parent = null;
    let lastIndex = null;
    
    for (let i = 0; i < pathParts.length; i++) {
      const part = pathParts[i];
      if (part === 'conditions') {
        continue;
      }
      parent = current;
      lastIndex = parseInt(part);
      current = current.conditions[lastIndex];
    }
    
    const logicalCondition = {
      operator: operator,
      conditions: [current, createSimpleCondition()]
    };
    
    if (pathParts.length === 0) {
      onChange(logicalCondition);
    } else {
      parent.conditions[lastIndex] = logicalCondition;
      onChange(newExpression);
    }
  };

  const hasExpression = expression && (expression.tag || expression.operator);

  return (
    <div className="visibility-expression-editor">
      <div className="editor-header">
        <label className="settings-label">
          {t('Form Visibility')}
          <span className="settings-description">
            {t('Control who can see this form based on tags (e.g., invited_guest, selected_attendee)')}
          </span>
        </label>
        <div className="editor-actions">
          {hasExpression && (
            <button
              type="button"
              className="btn btn-sm btn-outline-danger"
              onClick={handleClear}
            >
              {t('Clear')}
            </button>
          )}
          <button
            type="button"
            className="btn btn-sm btn-outline-primary"
            onClick={handleToggleEditor}
          >
            {showEditor ? t('Hide') : t('Configure')}
          </button>
        </div>
      </div>

      {showEditor && (
        <div className="editor-body">
          <div className="editor-help">
            <p><strong>{t('Common tags:')}</strong></p>
            <ul>
              <li><code>invited_guest</code> - {t('User is on the invited guest list')}</li>
              <li><code>selected_attendee</code> - {t('User has an offer')}</li>
            </ul>
            <p>{t('You can also use custom tags defined in your event.')}</p>
          </div>
          
          <div className="expression-builder">
            {expression ? (
              renderConditionEditor(expression, '', null)
            ) : (
              <div className="empty-state">
                <p>{t('No visibility restrictions set. The form will be visible to all users.')}</p>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => onChange(createSimpleCondition())}
                >
                  {t('Add Visibility Rule')}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {hasExpression && !showEditor && (
        <div className="expression-summary">
          <i className="fas fa-lock"></i>
          <span>{t('Visibility restrictions configured')}</span>
        </div>
      )}
    </div>
  );
};

export default VisibilityExpressionEditor;
