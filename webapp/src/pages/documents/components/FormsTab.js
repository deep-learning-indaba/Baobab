import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { formServices } from '../../../services/form';
import { Card } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import TranslatableFieldGroup from '../../formEditor/components/TranslatableFieldGroup';

const REQUIREMENT_HELP = {
  none: 'Answers are used if available. The person is not asked to complete this form.',
  recommended: 'The person is asked to complete this form, but can still get the document without it.',
  required: "The document can't be generated until the person has submitted this form. This doesn't require them to have answered any particular question on it.",
};

const FormsTab = ({ template, eventId, languages, autoTranslateEnabled, onReload }) => {
  const { t } = useTranslation();
  const [allForms, setAllForms] = useState([]);
  const primaryLang = languages[0] && languages[0].code;

  const formName = (form) => {
    if (!form.name) return t('Untitled form');
    if (typeof form.name === 'string') return form.name;
    return form.name.en || Object.values(form.name)[0] || t('Untitled form');
  };
  const [links, setLinks] = useState(() =>
    (template.form_links || []).map((link) => ({
      form_id: link.form_id,
      form_name: link.form_name,
      order: link.order,
      requirement: link.requirement,
      prompt_messages: { ...(link.prompt_messages || {}) },
    })),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    formServices.getFormList(eventId).then((result) => {
      setAllForms(result.forms || []);
    });
  }, [eventId]);

  const linkedFormIds = new Set(links.map((l) => l.form_id));
  const availableToAdd = allForms.filter((f) => !linkedFormIds.has(f.id));

  // Every updater below uses the functional setLinks(prev => ...) form rather
  // than closing over `links` directly. TranslatableFieldGroup's debounced
  // auto-translate calls onChange asynchronously, and a textarea `fill()`
  // (Playwright, but also some IME/autofill paths in real browsers) can emit
  // two rapid input events - if a second update closes over the same stale
  // `links` a first update hasn't been re-rendered against yet, it overwrites
  // the first one instead of composing with it, silently dropping an edit.

  const addLink = (formId) => {
    const form = allForms.find((f) => f.id === formId);
    if (!form) return;
    setLinks((prev) => {
      const nextOrder = prev.length ? Math.max(...prev.map((l) => l.order)) + 10 : 10;
      return [{ form_id: form.id, form_name: formName(form), order: nextOrder, requirement: 'none', prompt_messages: {} }, ...prev];
    });
  };

  const removeLink = (formId) => setLinks((prev) => prev.filter((l) => l.form_id !== formId));

  const moveUp = (index) => {
    if (index === 0) return;
    setLinks((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next.map((l, i) => ({ ...l, order: (next.length - i) * 10 }));
    });
  };
  const moveDown = (index) => moveUp(index + 1);

  const updateLink = (formId, field, value) =>
    setLinks((prev) => prev.map((l) => (l.form_id === formId ? { ...l, [field]: value } : l)));

  const updatePromptMessage = (formId, lang, value) =>
    setLinks((prev) => prev.map((l) => (
      l.form_id === formId ? { ...l, prompt_messages: { ...l.prompt_messages, [lang]: value } } : l
    )));

  const handleSave = () => {
    for (const link of links) {
      if (link.requirement !== 'none' && !(link.prompt_messages[primaryLang] || '').trim()) {
        setError(t('Add a message for each required or recommended form, explaining what to do.'));
        return;
      }
    }
    setSaving(true);
    setError(null);
    // Ordered so the first item (highest order) is searched first - matches
    // the resolution order documented in the design.
    const ordered = links.map((l, i) => ({ ...l, order: (links.length - i) * 10 }));
    documentsService.setFormLinks(template.id, ordered).then((result) => {
      setSaving(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      onReload();
    });
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {error && <div className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>}

      <p className="text-sm text-muted-foreground">
        {t('Answers are looked up in this order. The first form where this person has actually answered the question provides the value — if a form doesn\'t ask them the question, or they left it blank, the next form down is used instead.')}
      </p>

      <div className="space-y-3">
        {links.map((link, index) => (
          <Card key={link.form_id} className="p-4">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-muted-foreground w-6">{index === 0 ? t('1st') : `${index + 1}${t('th')}`}</span>
                <span className="font-semibold text-foreground">{link.form_name}</span>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" onClick={() => moveUp(index)} disabled={index === 0}>↑</Button>
                <Button variant="ghost" size="sm" onClick={() => moveDown(index)} disabled={index === links.length - 1}>↓</Button>
                <Button variant="ghost" size="sm" onClick={() => removeLink(link.form_id)}>{t('Unlink')}</Button>
              </div>
            </div>

            <div className="flex items-center gap-4 text-sm mb-2">
              {['none', 'recommended', 'required'].map((option) => (
                <label key={option} className="flex items-center gap-1.5">
                  <input
                    type="radio"
                    name={`requirement-${link.form_id}`}
                    checked={link.requirement === option}
                    onChange={() => updateLink(link.form_id, 'requirement', option)}
                  />
                  {t(option === 'none' ? 'Optional' : option === 'recommended' ? 'Recommended' : 'Required')}
                </label>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mb-2">{t(REQUIREMENT_HELP[link.requirement])}</p>

            {link.requirement !== 'none' && (
              <TranslatableFieldGroup
                label={t('Message shown if not completed')}
                fieldName="prompt_message"
                values={link.prompt_messages}
                languages={languages}
                onChange={(lang, value) => updatePromptMessage(link.form_id, lang, value)}
                multiline
                autoTranslateEnabled={autoTranslateEnabled}
              />
            )}
          </Card>
        ))}

        {links.length === 0 && (
          <p className="text-sm text-muted-foreground">{t('No forms linked yet.')}</p>
        )}
      </div>

      {availableToAdd.length > 0 && (
        <div>
          <label className="block text-sm font-semibold text-foreground mb-1">{t('Link a form')}</label>
          <select
            className="rounded-lg border border-border px-3 py-2 text-sm"
            value=""
            onChange={(e) => e.target.value && addLink(parseInt(e.target.value, 10))}
          >
            <option value="">{t('+ Choose a form to link')}</option>
            {availableToAdd.map((form) => (
              <option key={form.id} value={form.id}>{formName(form)}</option>
            ))}
          </select>
        </div>
      )}

      <div className="pt-2">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? t('Saving...') : t('Save linked forms')}
        </Button>
      </div>
    </div>
  );
};

export default FormsTab;
