import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/button';

/**
 * A simple rule builder for the tag/predicate expression language shared by
 * document eligibility and variant selection rules (backend
 * app/documents/eligibility.py). Covers "all/any of these tags, optionally
 * negated" - enough to express every combination in design section 7.4
 * (travel x accommodation) - not the fully general nested AND/OR/NOT tree.
 *
 * An expression built elsewhere (or one with real nesting) that doesn't match
 * this {operator, conditions:[{tag_id}|{operator:'NOT',...}]} shape falls
 * back to a read-only JSON view rather than silently discarding it.
 */

function decompile(expression) {
  if (!expression) return { mode: 'all', conditions: [] };

  const asCondition = (leaf) => {
    if (leaf && typeof leaf.tag_id === 'number') return { tag_id: leaf.tag_id, negate: false };
    if (leaf && leaf.operator === 'NOT' && Array.isArray(leaf.conditions) && leaf.conditions.length === 1
        && typeof leaf.conditions[0].tag_id === 'number') {
      return { tag_id: leaf.conditions[0].tag_id, negate: true };
    }
    return null;
  };

  const single = asCondition(expression);
  if (single) return { mode: 'all', conditions: [single] };

  if (expression.operator === 'AND' || expression.operator === 'OR') {
    const conditions = (expression.conditions || []).map(asCondition);
    if (conditions.every((c) => c !== null)) {
      return { mode: expression.operator === 'AND' ? 'all' : 'any', conditions };
    }
  }

  return null; // unsupported shape - caller falls back to raw JSON
}

function compile(mode, conditions) {
  if (conditions.length === 0) return null;
  const leaf = (c) => (c.negate ? { operator: 'NOT', conditions: [{ tag_id: c.tag_id }] } : { tag_id: c.tag_id });
  if (conditions.length === 1) return leaf(conditions[0]);
  return { operator: mode === 'all' ? 'AND' : 'OR', conditions: conditions.map(leaf) };
}

const TagExpressionBuilder = ({ expression, onChange, tags }) => {
  const { t } = useTranslation();
  const decompiled = useMemo(() => decompile(expression), [expression]);

  if (decompiled === null) {
    return (
      <div className="space-y-2">
        <p className="text-xs text-warning">
          {t('This rule uses a shape the simple builder can\'t edit. Showing the raw rule instead.')}
        </p>
        <pre className="text-xs bg-surface-low rounded-lg p-3 overflow-x-auto">{JSON.stringify(expression, null, 2)}</pre>
        <Button variant="ghost" size="sm" onClick={() => onChange(null)}>{t('Clear and start over')}</Button>
      </div>
    );
  }

  const { mode, conditions } = decompiled;

  const update = (nextMode, nextConditions) => onChange(compile(nextMode, nextConditions));

  const addCondition = () => {
    if (!tags.length) return;
    update(mode, [...conditions, { tag_id: tags[0].id, negate: false }]);
  };
  const removeCondition = (index) => update(mode, conditions.filter((_, i) => i !== index));
  const setConditionTag = (index, tagId) =>
    update(mode, conditions.map((c, i) => (i === index ? { ...c, tag_id: tagId } : c)));
  const toggleNegate = (index) =>
    update(mode, conditions.map((c, i) => (i === index ? { ...c, negate: !c.negate } : c)));

  return (
    <div className="space-y-2">
      {conditions.length === 0 && (
        <p className="text-sm text-muted-foreground">{t('No rule set - matches everyone.')}</p>
      )}

      {conditions.length > 1 && (
        <div className="flex items-center gap-2 text-sm text-foreground">
          <span>{t('Match')}</span>
          <select
            className="rounded-md border border-border px-2 py-1 text-sm"
            value={mode}
            onChange={(e) => update(e.target.value, conditions)}
          >
            <option value="all">{t('all of')}</option>
            <option value="any">{t('any of')}</option>
          </select>
          <span>{t('these conditions:')}</span>
        </div>
      )}

      {conditions.map((condition, index) => (
        <div key={index} className="flex items-center gap-2">
          <select
            className="rounded-md border border-border px-2 py-1 text-sm w-28"
            value={condition.negate ? 'not' : 'has'}
            onChange={() => toggleNegate(index)}
          >
            <option value="has">{t('has tag')}</option>
            <option value="not">{t('does not have tag')}</option>
          </select>
          <select
            className="rounded-md border border-border px-2 py-1 text-sm flex-1"
            value={condition.tag_id}
            onChange={(e) => setConditionTag(index, parseInt(e.target.value, 10))}
          >
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>{tag.name}</option>
            ))}
          </select>
          <Button variant="ghost" size="sm" onClick={() => removeCondition(index)}>{t('Remove')}</Button>
        </div>
      ))}

      <Button variant="secondary" size="sm" onClick={addCondition} disabled={!tags.length}>
        {t('+ Add condition')}
      </Button>
      {!tags.length && (
        <p className="text-xs text-muted-foreground">{t('This event has no tags configured yet.')}</p>
      )}
    </div>
  );
};

export default TagExpressionBuilder;
