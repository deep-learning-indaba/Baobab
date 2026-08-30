import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { ConfirmModal } from '../../components/Modal';
import Loading from '../../components/Loading';
import TranslatableFieldGroup from '../formEditor/components/TranslatableFieldGroup';
import RuleConditionBuilder from './components/RuleConditionBuilder';

/**
 * Event-scoped rule builder for derived placeholders (design section 5.7 /
 * 9.6) - conditional text like the invitation letter's presenting sentence,
 * defined once in Baobab and referenced by a single {placeholder} in as many
 * document templates as want it.
 */

let nextClientId = 1;
const newClientId = () => `new-${nextClientId++}`;

function newRule(order) {
  return { clientId: newClientId(), order, condition_expression: { key: '', operator: 'EQUALS', value: '' }, texts: {} };
}

function toEditable(derivedPlaceholder) {
  return {
    id: derivedPlaceholder.id,
    key: derivedPlaceholder.key,
    description: derivedPlaceholder.description || '',
    is_active: derivedPlaceholder.is_active,
    rules: (derivedPlaceholder.rules || []).map((r) => ({
      clientId: `existing-${r.id}`, order: r.order,
      condition_expression: r.condition_expression, texts: r.texts || {},
    })),
  };
}

const DerivedPlaceholdersAdmin = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);

  const [placeholders, setPlaceholders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState(null);
  const [selectedId, setSelectedId] = useState(null); // null = list only, 'new' = creating
  const [editing, setEditing] = useState(null);
  const [newKey, setNewKey] = useState('');
  const [saveError, setSaveError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [autoTranslateEnabled, setAutoTranslateEnabled] = useState(true);

  const orgLanguages = (props.organisation && props.organisation.languages) || [];
  const languages = orgLanguages.length
    ? [...orgLanguages].sort((a, b) => (a.code === 'en' ? -1 : b.code === 'en' ? 1 : 0))
    : [{ code: 'en', description: 'English' }];

  const load = useCallback(() => {
    if (!event) return;
    setLoading(true);
    documentsService.getDerivedPlaceholders(event.id).then((result) => {
      setPlaceholders(result.data || []);
      setListError(result.error || null);
      setLoading(false);
    });
  }, [event]);

  useEffect(() => { load(); }, [load]);

  const selectExisting = (derivedPlaceholder) => {
    setSelectedId(derivedPlaceholder.id);
    setEditing(toEditable(derivedPlaceholder));
    setSaveError(null);
  };

  const selectNew = () => {
    setSelectedId('new');
    setNewKey('');
    setEditing({ id: null, key: '', description: '', is_active: true, rules: [newRule(1)] });
    setSaveError(null);
  };

  const closeEditor = () => {
    setSelectedId(null);
    setEditing(null);
  };

  const hasOtherwise = (editing && editing.rules.some((r) => r.condition_expression === null)) || false;

  const addRule = () => {
    setEditing((prev) => {
      const nonOtherwise = prev.rules.filter((r) => r.condition_expression !== null);
      const otherwise = prev.rules.find((r) => r.condition_expression === null);
      const next = [...nonOtherwise, newRule(nonOtherwise.length + 1)];
      if (otherwise) next.push(otherwise);
      return { ...prev, rules: renumber(next) };
    });
  };

  const addOtherwise = () => {
    setEditing((prev) => ({ ...prev, rules: renumber([...prev.rules, { ...newRule(0), condition_expression: null }]) }));
  };

  function renumber(rules) {
    return rules.map((r, i) => ({ ...r, order: i + 1 }));
  }

  const removeRule = (clientId) => {
    setEditing((prev) => ({ ...prev, rules: renumber(prev.rules.filter((r) => r.clientId !== clientId)) }));
  };

  const moveRule = (clientId, direction) => {
    setEditing((prev) => {
      const index = prev.rules.findIndex((r) => r.clientId === clientId);
      const targetIndex = index + direction;
      if (targetIndex < 0 || targetIndex >= prev.rules.length) return prev;
      // An "otherwise" rule (condition_expression === null) must stay last.
      const targetRule = prev.rules[targetIndex];
      if (targetRule.condition_expression === null || prev.rules[index].condition_expression === null) return prev;
      const next = [...prev.rules];
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      return { ...prev, rules: renumber(next) };
    });
  };

  const updateRuleCondition = (clientId, condition_expression) => {
    setEditing((prev) => ({
      ...prev,
      rules: prev.rules.map((r) => (r.clientId === clientId ? { ...r, condition_expression } : r)),
    }));
  };

  const updateRuleText = (clientId, lang, value) => {
    setEditing((prev) => ({
      ...prev,
      rules: prev.rules.map((r) => (r.clientId === clientId ? { ...r, texts: { ...r.texts, [lang]: value } } : r)),
    }));
  };

  const handleSave = () => {
    setSaving(true);
    setSaveError(null);
    const payload = {
      description: editing.description,
      is_active: editing.is_active,
      rules: editing.rules.map((r) => ({
        order: r.order, condition_expression: r.condition_expression, texts: r.texts,
      })),
    };

    const request = selectedId === 'new'
      ? documentsService.createDerivedPlaceholder(event.id, { key: newKey, ...payload })
      : documentsService.updateDerivedPlaceholder(editing.id, payload);

    request.then((result) => {
      setSaving(false);
      if (result.error) {
        setSaveError(result.error);
        return;
      }
      closeEditor();
      load();
    });
  };

  const handleDelete = () => {
    setConfirmDelete(false);
    documentsService.deleteDerivedPlaceholder(editing.id).then((result) => {
      if (result.error) {
        setSaveError(result.error);
        return;
      }
      closeEditor();
      load();
    });
  };

  if (!event) return <Loading />;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <button
        className="text-sm text-action hover:underline mb-2"
        onClick={() => props.history.push(`/${eventKey}/documentsAdmin`)}
      >
        ← {t('Back to Documents')}
      </button>
      <div className="flex items-start justify-between gap-4 mb-1">
        <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Derived placeholders')}</h1>
        {languages.length > 1 && (
          <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer select-none shrink-0 mt-1">
            <input type="checkbox" checked={autoTranslateEnabled} onChange={(e) => setAutoTranslateEnabled(e.target.checked)} />
            {t('Auto-translate')}
          </label>
        )}
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        {t('Conditional text - like a sentence that only appears for people presenting a poster - defined once here and referenced by one {placeholder} in as many document templates as need it.')}
      </p>

      {listError && <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{listError}</div>}

      {!editing ? (
        <>
          <div className="mb-4">
            <Button onClick={selectNew}>{t('+ New derived placeholder')}</Button>
          </div>
          {loading ? (
            <Loading />
          ) : placeholders.length === 0 ? (
            <Card className="p-8 text-center text-muted-foreground">
              {t('No derived placeholders yet.')}
            </Card>
          ) : (
            <div className="space-y-3">
              {placeholders.map((p) => (
                <Card key={p.id} className="p-5 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-foreground">{'{' + p.key + '}'}</span>
                      {!p.is_active && (
                        <span className="text-xs rounded-full px-2 py-0.5 bg-surface-high text-muted-foreground">{t('Inactive')}</span>
                      )}
                    </div>
                    {p.description && <p className="text-sm text-muted-foreground mt-1">{p.description}</p>}
                    <p className="text-xs text-muted-foreground mt-1">
                      {p.rules.length} {t('rule(s)')}
                    </p>
                  </div>
                  <Button variant="secondary" size="sm" onClick={() => selectExisting(p)}>{t('Edit')}</Button>
                </Card>
              ))}
            </div>
          )}
        </>
      ) : (
        <Card className="p-6">
          {saveError && <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{saveError}</div>}

          <div className="mb-4">
            <label className="block font-semibold text-foreground text-sm mb-1">{t('Key')}</label>
            {selectedId === 'new' ? (
              <input
                className="w-full max-w-xs px-3 py-2 border border-border rounded-md text-sm font-mono"
                placeholder="poster_sentence"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value.trim().toLowerCase())}
              />
            ) : (
              <span className="font-mono text-sm">{'{' + editing.key + '}'}</span>
            )}
            {selectedId !== 'new' && (
              <p className="text-xs text-muted-foreground mt-1">{t('The key cannot be changed once created - documents may already reference it.')}</p>
            )}
          </div>

          <div className="mb-4">
            <label className="block font-semibold text-foreground text-sm mb-1">{t('Description')}</label>
            <input
              className="w-full px-3 py-2 border border-border rounded-md text-sm"
              value={editing.description}
              onChange={(e) => setEditing((prev) => ({ ...prev, description: e.target.value }))}
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-foreground mb-6">
            <input type="checkbox" checked={editing.is_active}
                   onChange={(e) => setEditing((prev) => ({ ...prev, is_active: e.target.checked }))} />
            {t('Active')}
          </label>

          <h3 className="font-heading font-semibold text-foreground mb-1">{t('Rules')}</h3>
          <p className="text-xs text-muted-foreground mb-4">
            {t('Tried in order - the first rule whose condition holds supplies the text.')}
          </p>

          <div className="space-y-4">
            {editing.rules.map((rule, index) => {
              const isOtherwise = rule.condition_expression === null;
              return (
                <div key={rule.clientId} className="border border-border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-muted-foreground">
                      {isOtherwise ? t('Otherwise') : `${t('Rule')} ${index + 1}`}
                    </span>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" onClick={() => moveRule(rule.clientId, -1)} disabled={index === 0 || isOtherwise}>↑</Button>
                      <Button
                        variant="ghost" size="sm" onClick={() => moveRule(rule.clientId, 1)}
                        disabled={
                          index === editing.rules.length - 1 || isOtherwise ||
                          editing.rules[index + 1].condition_expression === null
                        }
                      >↓</Button>
                      <Button variant="ghost" size="sm" onClick={() => removeRule(rule.clientId)}>{t('Remove')}</Button>
                    </div>
                  </div>

                  {!isOtherwise && (
                    <div className="mb-3">
                      <RuleConditionBuilder
                        expression={rule.condition_expression}
                        onChange={(expr) => updateRuleCondition(rule.clientId, expr)}
                      />
                    </div>
                  )}

                  <TranslatableFieldGroup
                    label={t('Text')}
                    fieldName={`rule-${rule.clientId}-text`}
                    values={rule.texts}
                    languages={languages}
                    onChange={(lang, value) => updateRuleText(rule.clientId, lang, value)}
                    multiline
                    autoTranslateEnabled={autoTranslateEnabled}
                  />
                </div>
              );
            })}
          </div>

          <div className="flex items-center gap-2 mt-4 mb-6">
            <Button variant="secondary" size="sm" onClick={addRule}>{t('+ Add rule')}</Button>
            {!hasOtherwise && (
              <Button variant="secondary" size="sm" onClick={addOtherwise}>{t('+ Add "otherwise" rule')}</Button>
            )}
          </div>
          {!hasOtherwise && (
            <p className="text-xs text-warning mb-6">
              {t('No "otherwise" rule - if no condition matches for someone, this placeholder falls through to the next source (or an error, if nothing else defines it). This is sometimes intentional.')}
            </p>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-border">
            <div>
              {selectedId !== 'new' && (
                <Button variant="ghost" onClick={() => setConfirmDelete(true)}>{t('Delete')}</Button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" onClick={closeEditor}>{t('Cancel')}</Button>
              <Button onClick={handleSave} disabled={saving || (selectedId === 'new' && !newKey.trim())}>
                {saving ? t('Saving...') : t('Save')}
              </Button>
            </div>
          </div>
        </Card>
      )}

      <ConfirmModal
        visible={confirmDelete}
        okText={t('Delete')}
        onOK={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      >
        <p className="font-semibold text-foreground mb-1">{t('Delete this derived placeholder?')}</p>
        <p>{t('Any document template still referencing it will show an unresolved placeholder error.')}</p>
      </ConfirmModal>
    </div>
  );
};

export default DerivedPlaceholdersAdmin;
