import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/button';
import { formServices } from '../../../services/form';

/**
 * A rule builder for the tag/predicate expression language shared by document
 * eligibility and variant selection rules (backend app/documents/eligibility.py,
 * app/forms/visibility.py's VisibilityEvaluator). Covers "all/any of these
 * conditions, optionally negated" over the three leaf kinds that language
 * defines for this use - tag, attended, form_submitted - matching every
 * combination in design section 7.4 (travel x accommodation) plus the
 * "attended the event" rule a certificate of attendance needs. Not the fully
 * general nested AND/OR/NOT tree, and not the `key`/`operator` answer-
 * comparison leaf (see RuleConditionBuilder, used for derived placeholder
 * rules instead - eligibility/variant rules test tags and event-level facts,
 * not individual form answers).
 *
 * An expression built elsewhere (or one with real nesting) that doesn't match
 * this shape falls back to a read-only JSON view rather than silently
 * discarding it.
 */

function asCondition(leaf) {
  if (!leaf || typeof leaf !== 'object') return null;
  if (typeof leaf.tag_id === 'number') return { kind: 'tag', tag_id: leaf.tag_id, negate: false };
  if (typeof leaf.attended === 'boolean') return { kind: 'attended', negate: leaf.attended === false };
  if (typeof leaf.form_submitted === 'number') return { kind: 'form_submitted', form_id: leaf.form_submitted, negate: false };
  if (leaf.operator === 'NOT' && Array.isArray(leaf.conditions) && leaf.conditions.length === 1) {
    const inner = leaf.conditions[0];
    if (typeof inner.tag_id === 'number') return { kind: 'tag', tag_id: inner.tag_id, negate: true };
    if (typeof inner.form_submitted === 'number') return { kind: 'form_submitted', form_id: inner.form_submitted, negate: true };
  }
  return null;
}

function decompile(expression) {
  if (!expression) return { mode: 'all', conditions: [] };

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

function leafFor(condition) {
  if (condition.kind === 'attended') return { attended: !condition.negate };
  const base = condition.kind === 'tag' ? { tag_id: condition.tag_id } : { form_submitted: condition.form_id };
  return condition.negate ? { operator: 'NOT', conditions: [base] } : base;
}

function compile(mode, conditions) {
  if (conditions.length === 0) return null;
  if (conditions.length === 1) return leafFor(conditions[0]);
  return { operator: mode === 'all' ? 'AND' : 'OR', conditions: conditions.map(leafFor) };
}

const KIND_LABELS = {
  tag: { has: 'has tag', not: 'does not have tag' },
  attended: { has: 'attended the event', not: 'has not attended the event' },
  form_submitted: { has: 'submitted form', not: 'has not submitted form' },
};

const TagExpressionBuilder = ({ expression, onChange, tags, eventId }) => {
  const { t } = useTranslation();
  const decompiled = useMemo(() => decompile(expression), [expression]);
  const [forms, setForms] = useState([]);

  useEffect(() => {
    if (!eventId) return;
    formServices.getFormList(eventId).then((result) => setForms(result.forms || []));
  }, [eventId]);

  const formName = (form) => {
    if (!form || !form.name) return t('Untitled form');
    return typeof form.name === 'string' ? form.name : (form.name.en || Object.values(form.name)[0]);
  };

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

  const defaultKind = tags.length ? 'tag' : 'attended';
  const defaultCondition = (kind) => {
    if (kind === 'tag') return { kind: 'tag', tag_id: tags[0] && tags[0].id, negate: false };
    if (kind === 'form_submitted') return { kind: 'form_submitted', form_id: forms[0] && forms[0].id, negate: false };
    return { kind: 'attended', negate: false };
  };

  const addCondition = () => update(mode, [...conditions, defaultCondition(defaultKind)]);
  const removeCondition = (index) => update(mode, conditions.filter((_, i) => i !== index));
  const updateCondition = (index, patch) =>
    update(mode, conditions.map((c, i) => (i === index ? { ...c, ...patch } : c)));
  const toggleNegate = (index) => updateCondition(index, { negate: !conditions[index].negate });
  const setKind = (index, kind) => updateCondition(index, defaultCondition(kind));

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

      {conditions.map((condition, index) => {
        const labels = KIND_LABELS[condition.kind] || KIND_LABELS.tag;
        return (
          <div key={index} className="flex items-center gap-2 flex-wrap">
            <select
              className="rounded-md border border-border px-2 py-1 text-sm w-32"
              value={condition.kind}
              onChange={(e) => setKind(index, e.target.value)}
            >
              <option value="tag">{t('Tag')}</option>
              <option value="attended">{t('Attendance')}</option>
              <option value="form_submitted">{t('Form submitted')}</option>
            </select>
            <select
              className="rounded-md border border-border px-2 py-1 text-sm w-44"
              value={condition.negate ? 'not' : 'has'}
              onChange={() => toggleNegate(index)}
            >
              <option value="has">{t(labels.has)}</option>
              <option value="not">{t(labels.not)}</option>
            </select>

            {condition.kind === 'tag' && (
              <select
                className="rounded-md border border-border px-2 py-1 text-sm flex-1"
                value={condition.tag_id || ''}
                onChange={(e) => updateCondition(index, { tag_id: parseInt(e.target.value, 10) })}
              >
                {tags.map((tag) => (
                  <option key={tag.id} value={tag.id}>{tag.name}</option>
                ))}
              </select>
            )}

            {condition.kind === 'form_submitted' && (
              <select
                className="rounded-md border border-border px-2 py-1 text-sm flex-1"
                value={condition.form_id || ''}
                onChange={(e) => updateCondition(index, { form_id: parseInt(e.target.value, 10) })}
              >
                {forms.map((form) => (
                  <option key={form.id} value={form.id}>{formName(form)}</option>
                ))}
              </select>
            )}

            <Button variant="ghost" size="sm" onClick={() => removeCondition(index)}>{t('Remove')}</Button>
          </div>
        );
      })}

      <Button variant="secondary" size="sm" onClick={addCondition}>
        {t('+ Add condition')}
      </Button>
      {!tags.length && (
        <p className="text-xs text-muted-foreground">{t('This event has no tags configured yet.')}</p>
      )}
    </div>
  );
};

export default TagExpressionBuilder;
