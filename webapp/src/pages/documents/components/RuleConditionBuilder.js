import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/button';

/**
 * A builder for the `key`/`operator` answer-comparison leaf (backend
 * app/forms/visibility.py's VisibilityEvaluator._evaluate_answer) - used for
 * derived placeholder rule conditions, e.g. "bringing_poster equals yes".
 * Same "AND-only, flat list" scope as TagExpressionBuilder; a condition
 * built elsewhere with real nesting falls back to a read-only JSON view.
 */

const OPERATORS = [
  { value: 'EQUALS', label: 'equals', needsValue: true },
  { value: 'NOT_EQUALS', label: 'does not equal', needsValue: true },
  { value: 'IN', label: 'is one of', needsValues: true },
  { value: 'NOT_IN', label: 'is not one of', needsValues: true },
  { value: 'IS_EMPTY', label: 'is empty' },
  { value: 'IS_NOT_EMPTY', label: 'is not empty' },
];

function isAnswerLeaf(leaf) {
  return !!leaf && typeof leaf.key === 'string' && typeof leaf.operator === 'string';
}

function decompile(expression) {
  if (!expression) return { conditions: [] };
  if (isAnswerLeaf(expression)) return { conditions: [expression] };
  if (expression.operator === 'AND' && Array.isArray(expression.conditions)
      && expression.conditions.every(isAnswerLeaf)) {
    return { conditions: expression.conditions };
  }
  return null;
}

function compile(conditions) {
  if (conditions.length === 0) return null;
  if (conditions.length === 1) return conditions[0];
  return { operator: 'AND', conditions };
}

const RuleConditionBuilder = ({ expression, onChange }) => {
  const { t } = useTranslation();
  const decompiled = useMemo(() => decompile(expression), [expression]);

  if (decompiled === null) {
    return (
      <div className="space-y-2">
        <p className="text-xs text-warning">
          {t('This condition uses a shape the simple builder can\'t edit. Showing the raw rule instead.')}
        </p>
        <pre className="text-xs bg-surface-low rounded-lg p-2 overflow-x-auto">{JSON.stringify(expression, null, 2)}</pre>
        <Button variant="ghost" size="sm" onClick={() => onChange(null)}>{t('Clear and start over')}</Button>
      </div>
    );
  }

  const { conditions } = decompiled;
  const update = (next) => onChange(compile(next));

  const addCondition = () => update([...conditions, { key: '', operator: 'EQUALS', value: '' }]);
  const removeCondition = (index) => update(conditions.filter((_, i) => i !== index));
  const updateCondition = (index, patch) =>
    update(conditions.map((c, i) => (i === index ? { ...c, ...patch } : c)));

  const setOperator = (index, operatorValue) => {
    const operator = OPERATORS.find((o) => o.value === operatorValue);
    const patch = { operator: operatorValue };
    if (!operator.needsValue) delete patch.value;
    if (!operator.needsValues) delete patch.values;
    if (operator.needsValue && conditions[index].value === undefined) patch.value = '';
    if (operator.needsValues && conditions[index].values === undefined) patch.values = [];
    updateCondition(index, patch);
  };

  return (
    <div className="space-y-2">
      {conditions.length === 0 && (
        <p className="text-sm text-muted-foreground">{t('No condition - this rule always matches (the "otherwise" rule).')}</p>
      )}

      {conditions.length > 1 && (
        <p className="text-xs text-muted-foreground">{t('All of these must hold:')}</p>
      )}

      {conditions.map((condition, index) => {
        const operator = OPERATORS.find((o) => o.value === condition.operator) || OPERATORS[0];
        return (
          <div key={index} className="flex items-center gap-2 flex-wrap">
            <input
              className="rounded-md border border-border px-2 py-1 text-sm w-40 font-mono"
              placeholder={t('placeholder key, e.g. bringing_poster')}
              value={condition.key}
              onChange={(e) => updateCondition(index, { key: e.target.value.trim().toLowerCase() })}
            />
            <select
              className="rounded-md border border-border px-2 py-1 text-sm"
              value={condition.operator}
              onChange={(e) => setOperator(index, e.target.value)}
            >
              {OPERATORS.map((o) => <option key={o.value} value={o.value}>{t(o.label)}</option>)}
            </select>
            {operator.needsValue && (
              <input
                className="rounded-md border border-border px-2 py-1 text-sm flex-1 min-w-[100px]"
                placeholder={t('value')}
                value={condition.value || ''}
                onChange={(e) => updateCondition(index, { value: e.target.value })}
              />
            )}
            {operator.needsValues && (
              <input
                className="rounded-md border border-border px-2 py-1 text-sm flex-1 min-w-[140px]"
                placeholder={t('comma-separated values')}
                value={(condition.values || []).join(', ')}
                onChange={(e) => updateCondition(index, {
                  values: e.target.value.split(',').map((v) => v.trim()).filter(Boolean),
                })}
              />
            )}
            <Button variant="ghost" size="sm" onClick={() => removeCondition(index)}>{t('Remove')}</Button>
          </div>
        );
      })}

      <Button variant="secondary" size="sm" onClick={addCondition}>{t('+ Add condition')}</Button>
    </div>
  );
};

export default RuleConditionBuilder;
