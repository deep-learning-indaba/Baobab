import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { tagsService } from '../../../services/tags/tags.service';

// Tags that Baobab derives from a user's state rather than from the event's tag
// list, so they will never appear in the tag picker but are valid to reference.
const AUTOMATIC_TAGS = ['invited_guest', 'selected_attendee'];

const VisibilityExpressionEditor = ({ expression, onChange, scope = 'form', eventId = null }) => {
  const { t } = useTranslation();
  const [showEditor, setShowEditor] = useState(false);
  const [availableTags, setAvailableTags] = useState([]);

  // Offer the event's real tag names - free text would let a single typo produce
  // a rule that silently matches nobody, with nothing indicating why.
  useEffect(() => {
    if (!eventId) return;
    let cancelled = false;
    tagsService.getTagList(eventId, 'en').then(result => {
      if (cancelled || !result.tags) return;
      const names = result.tags
        .map(tag => (typeof tag.name === 'object' ? tag.name.en || Object.values(tag.name)[0] : tag.name))
        .filter(Boolean);
      setAvailableTags(names);
    });
    return () => { cancelled = true; };
  }, [eventId]);

  const tagChoices = [...AUTOMATIC_TAGS, ...availableTags.filter(n => !AUTOMATIC_TAGS.includes(n))];

  // Copy adapts to where this editor is embedded (form/section/question),
  // rather than always saying "Form Visibility" / "this form".
  const scopeCopy = {
    form: {
      title: t('Form Visibility'),
      help: t('Control who can see this form based on tags'),
      empty: t('No visibility restrictions set. The form will be visible to all users.')
    },
    section: {
      title: t('Section Visibility'),
      help: t('Control who can see this section based on tags'),
      empty: t('No visibility restrictions set. The section will be visible to all users.')
    },
    question: {
      title: t('Question Visibility'),
      help: t('Control who can see this question based on tags'),
      empty: t('No visibility restrictions set. The question will be visible to all users.')
    }
  }[scope] || {};

  const createSimpleCondition = () => ({ tag: '' });
  const createLogicalExpression = (operator) => ({ operator, conditions: [createSimpleCondition()] });

  const handleToggleEditor = () => {
    if (!showEditor && !expression) onChange(createSimpleCondition());
    setShowEditor(!showEditor);
  };

  const handleClear = () => { onChange(null); setShowEditor(false); };

  const renderConditionEditor = (condition, path, parentOperator) => {
    const isLogical = condition.operator && ['AND', 'OR', 'NOT'].includes(condition.operator);

    if (isLogical) {
      return (
        <div key={path} className="border-2 border-border rounded-md p-4 my-2 bg-surface">
          <div className="flex gap-2 items-center mb-3">
            <select
              value={condition.operator}
              onChange={(e) => updateCondition(path, { ...condition, operator: e.target.value })}
              className="px-3 py-1.5 border border-border rounded-md text-sm bg-white font-semibold text-foreground cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="AND">{t('AND (all must match)')}</option>
              <option value="OR">{t('OR (any can match)')}</option>
              <option value="NOT">{t('NOT (must not match)')}</option>
            </select>
            <button
              type="button"
              onClick={() => removeCondition(path)}
              title={t('Remove')}
              className="p-1.5 border border-error/30 text-error rounded-md bg-white hover:bg-error-container transition-colors"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
          <div className="pl-6 border-l-[3px] border-border">
            {(condition.conditions || []).map((subCond, index) =>
              renderConditionEditor(subCond, path + '.' + index, condition.operator)
            )}
            {condition.operator !== 'NOT' && (
              <div className="flex gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => addCondition(path, createSimpleCondition())}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border text-foreground rounded-md text-xs font-medium hover:bg-surface-low transition-colors"
                >
                  <i className="fas fa-plus"></i> {t('Add Tag')}
                </button>
                <button
                  type="button"
                  onClick={() => addCondition(path, createLogicalExpression('AND'))}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-border text-foreground rounded-md text-xs font-medium hover:bg-surface-low transition-colors"
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
      <div key={path} className="flex gap-2 items-center my-2">
        <div className="flex-1">
          <input
            type="text"
            list={`visibility-tags-${scope}`}
            value={condition.tag || ''}
            onChange={(e) => updateCondition(path, { ...condition, tag: e.target.value })}
            placeholder={t('Enter tag name (e.g., invited_guest, selected_attendee)')}
            className={`w-full px-3 py-2 border rounded-md text-sm font-mono bg-white focus:outline-none focus:ring-2 focus:ring-ring ${
              condition.tag && tagChoices.length > 0 && !tagChoices.includes(condition.tag)
                ? 'border-warning' : 'border-border'
            }`}
          />
          <datalist id={`visibility-tags-${scope}`}>
            {tagChoices.map(name => <option key={name} value={name} />)}
          </datalist>
          {condition.tag && tagChoices.length > 0 && !tagChoices.includes(condition.tag) && (
            <span className="block text-warning text-xs mt-1">
              {t('No tag with this name exists for this event - nobody will match it.')}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => convertToLogical(path, 'AND')}
          title={t('Convert to group')}
          className="p-1.5 border border-action/30 text-action rounded-md bg-white hover:bg-action/5 transition-colors"
        >
          <i className="fas fa-layer-group"></i>
        </button>
        {parentOperator && (
          <button
            type="button"
            onClick={() => removeCondition(path)}
            title={t('Remove')}
            className="p-1.5 border border-error/30 text-error rounded-md bg-white hover:bg-error-container transition-colors"
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
      if (part === 'conditions') continue;
      current = current.conditions[parseInt(part)];
    }
    if (pathParts.length === 0) {
      onChange(newCondition);
    } else {
      const lastPart = pathParts[pathParts.length - 1];
      if (current.conditions) current.conditions[parseInt(lastPart)] = newCondition;
      onChange(newExpression);
    }
  };

  const addCondition = (path, newCondition) => {
    const pathParts = path.split('.').filter(p => p);
    const newExpression = JSON.parse(JSON.stringify(expression));
    let current = newExpression;
    for (const part of pathParts) {
      if (part === 'conditions') continue;
      current = current.conditions[parseInt(part)];
    }
    if (!current.conditions) current.conditions = [];
    current.conditions.push(newCondition);
    onChange(newExpression);
  };

  const removeCondition = (path) => {
    const pathParts = path.split('.').filter(p => p);
    if (pathParts.length === 0) { onChange(null); return; }
    const newExpression = JSON.parse(JSON.stringify(expression));
    let current = newExpression;
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (part === 'conditions') continue;
      current = current.conditions[parseInt(part)];
    }
    current.conditions.splice(parseInt(pathParts[pathParts.length - 1]), 1);
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
      if (part === 'conditions') continue;
      parent = current;
      lastIndex = parseInt(part);
      current = current.conditions[lastIndex];
    }
    const logicalCondition = { operator, conditions: [current, createSimpleCondition()] };
    if (pathParts.length === 0) { onChange(logicalCondition); }
    else { parent.conditions[lastIndex] = logicalCondition; onChange(newExpression); }
  };

  const hasExpression = expression && (expression.tag || expression.operator);

  return (
    <div className="my-6 p-4 border border-border rounded-lg bg-surface">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <label className="flex flex-col gap-1">
          <span className="font-semibold text-foreground text-sm">{scopeCopy.title}</span>
          <span className="text-sm text-muted-foreground font-normal">{scopeCopy.help}</span>
        </label>
        <div className="flex gap-2 flex-shrink-0 ml-4">
          {hasExpression && (
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-error text-error rounded-md text-xs font-medium hover:bg-error-container transition-colors"
            >
              {t('Clear')}
            </button>
          )}
          <button
            type="button"
            onClick={handleToggleEditor}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-primary text-primary rounded-md text-xs font-medium hover:bg-primary/5 transition-colors"
          >
            {showEditor ? t('Hide') : t('Configure')}
          </button>
        </div>
      </div>

      {showEditor && (
        <div className="mt-4">
          {/* Help callout */}
          <div className="p-4 bg-action/5 border-l-4 border-action rounded-r-md mb-4 text-sm text-action/90">
            <p className="font-semibold m-0 mb-1">{t('Common tags:')}</p>
            <ul className="mt-1 pl-5 mb-1 space-y-0.5">
              <li><code className="bg-action/10 px-1 py-0.5 rounded text-xs font-mono">invited_guest</code> — {t('User is on the invited guest list')}</li>
              <li><code className="bg-action/10 px-1 py-0.5 rounded text-xs font-mono">selected_attendee</code> — {t('User has an offer')}</li>
            </ul>
            <p className="m-0">{t('You can also use custom tags defined in your event.')}</p>
          </div>

          <div className="p-4 bg-white rounded-md border border-border">
            {expression ? (
              renderConditionEditor(expression, '', null)
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p className="mb-4">{scopeCopy.empty}</p>
                <button
                  type="button"
                  onClick={() => onChange(createSimpleCondition())}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors"
                >
                  {t('Add Visibility Rule')}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {hasExpression && !showEditor && (
        <div className="flex items-center gap-2 px-4 py-3 bg-action/5 border-l-4 border-action rounded-r-md mt-3 text-action font-medium text-sm">
          <i className="fas fa-lock"></i>
          <span>{t('Visibility restrictions configured')}</span>
        </div>
      )}
    </div>
  );
};

export default VisibilityExpressionEditor;
