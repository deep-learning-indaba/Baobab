import React, { useMemo, useState } from 'react';
import useLinkedForm from '../utils/useLinkedForm';
import {
  getLinkedDisplay, isLinkedQuestionShown, LINKED_DISPLAY_ONLY_TYPES,
} from '../../../utils/linkedDisplay';

const localised = (value, language) => {
  if (!value) return '';
  if (typeof value === 'string') return value;
  return value[language] || value.en || Object.values(value).find(v => v) || '';
};

const Toggle = ({ checked, partial = false, disabled = false, onChange, label }) => (
  <label className={`inline-flex items-center ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}>
    <input
      type="checkbox"
      className="sr-only"
      checked={checked}
      disabled={disabled}
      onChange={(e) => onChange(e.target.checked)}
      aria-label={label}
    />
    <span className={`form-toggle${partial ? ' form-toggle-partial' : ''}`} />
  </label>
);

/**
 * Chooses which of the linked form's sections and questions are shown next to
 * this form (to reviewers, for a review form). Stored as
 * `settings.linked_display`; see utils/linkedDisplay.js.
 */
const LinkedFormDisplayEditor = ({ linkedFormId, settings, onChange, dependencyIds, language, t }) => {
  const { form: linkedForm, loading, error } = useLinkedForm(linkedFormId);
  const display = getLinkedDisplay(settings);
  const [open, setOpen] = useState(!(settings && settings.linked_display));
  const [expanded, setExpanded] = useState({});

  const sections = useMemo(() => (linkedForm ? linkedForm.sections || [] : [])
    .map(section => ({
      ...section,
      questions: (section.questions || []).filter(q => !LINKED_DISPLAY_ONLY_TYPES.includes(q.type)),
    }))
    .filter(section => section.questions.length > 0), [linkedForm]);

  const allQuestionIds = sections.flatMap(s => s.questions.map(q => q.id));
  const shownCount = sections.reduce((n, s) =>
    n + s.questions.filter(q => isLinkedQuestionShown(display, s.id, q.id)).length, 0);

  // Ids are pruned to the current linked form on every write, so ids of
  // since-deleted sections and questions don't pile up in the setting.
  const write = (hiddenSectionIds, hiddenQuestionIds) => {
    const sectionIds = new Set(sections.map(s => s.id));
    const questionIds = new Set(allQuestionIds);
    onChange({
      ...settings,
      linked_display: {
        hidden_section_ids: [...new Set(hiddenSectionIds)].filter(id => sectionIds.has(id)),
        hidden_question_ids: [...new Set(hiddenQuestionIds)].filter(id => questionIds.has(id)),
      },
    });
  };

  const toggleSection = (sectionId, shown) => write(
    shown
      ? display.hidden_section_ids.filter(id => id !== sectionId)
      : [...display.hidden_section_ids, sectionId],
    display.hidden_question_ids
  );

  const toggleQuestion = (questionId, shown) => write(
    display.hidden_section_ids,
    shown
      ? display.hidden_question_ids.filter(id => id !== questionId)
      : [...display.hidden_question_ids, questionId]
  );

  const showAll = () => write([], []);
  const hideAll = () => write(sections.map(s => s.id), []);

  const linkBtn = "text-sm font-medium text-action hover:underline bg-transparent border-none cursor-pointer p-0 disabled:opacity-40 disabled:cursor-not-allowed disabled:no-underline";

  const renderBody = () => {
    if (loading) {
      return (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
          <i className="fas fa-spinner fa-spin"></i>
          <span>{t('Loading linked form...')}</span>
        </div>
      );
    }
    if (error) {
      return (
        <div className="flex items-center gap-2 text-sm text-error py-2">
          <i className="fas fa-exclamation-triangle"></i>
          <span>{t('Failed to load the linked form')}</span>
        </div>
      );
    }
    if (sections.length === 0) {
      return <p className="text-sm text-muted-foreground italic m-0">{t('The linked form has no questions yet.')}</p>;
    }

    return (
      <div className="border border-border rounded-lg divide-y divide-border">
        {sections.map(section => {
          const sectionShown = !display.hidden_section_ids.includes(section.id);
          const sectionShownCount = section.questions.filter(q => isLinkedQuestionShown(display, section.id, q.id)).length;
          const isExpanded = !!expanded[section.id];
          const name = localised(section.name, language) || t('Untitled section');

          return (
            <div key={section.id}>
              <div className="flex items-center gap-3 px-4 py-3 bg-surface">
                <button
                  type="button"
                  onClick={() => setExpanded(prev => ({ ...prev, [section.id]: !isExpanded }))}
                  className="flex-1 min-w-0 flex items-center gap-2 text-left bg-transparent border-none cursor-pointer p-0"
                  aria-expanded={isExpanded}
                >
                  <i className={`fas fa-chevron-${isExpanded ? 'down' : 'right'} w-3 text-xs text-muted-foreground`}></i>
                  <span className="font-semibold text-sm text-foreground truncate">{name}</span>
                </button>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {t('{{shown}} of {{total}} shown', { shown: sectionShownCount, total: section.questions.length })}
                </span>
                <Toggle
                  checked={sectionShown}
                  partial={sectionShown && sectionShownCount < section.questions.length}
                  onChange={(shown) => toggleSection(section.id, shown)}
                  label={t('Show section {{name}}', { name })}
                />
              </div>

              {isExpanded && (
                <ul className="m-0 p-0 list-none divide-y divide-border">
                  {section.questions.map(question => {
                    const shown = isLinkedQuestionShown(display, section.id, question.id);
                    const headline = localised(question.headline, language) || t('Question {{order}}', { order: question.order });
                    const usedByDependency = !shown && dependencyIds.has(question.id);
                    return (
                      <li key={question.id} className="flex items-start gap-3 pl-10 pr-4 py-2.5">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`text-sm ${shown ? 'text-foreground' : 'text-muted-foreground'}`}>{headline}</span>
                            <span className="text-[11px] px-1.5 py-0.5 rounded bg-surface-low text-muted-foreground">{question.type}</span>
                          </div>
                          {usedByDependency && (
                            <p className="flex items-start gap-1.5 text-xs text-warning mt-1 mb-0">
                              <i className="fas fa-exclamation-triangle mt-0.5"></i>
                              <span>{t("A question in this form depends on this answer. It won't be displayed, but its value is still sent to the reviewer's browser.")}</span>
                            </p>
                          )}
                        </div>
                        <Toggle
                          checked={shown}
                          disabled={!sectionShown}
                          onChange={(value) => toggleQuestion(question.id, value)}
                          label={t('Show question {{name}}', { name: headline })}
                        />
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-white px-8 py-6 mx-auto mb-8 max-w-[1200px] rounded-lg shadow-sm">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="flex items-start gap-3 text-left bg-transparent border-none cursor-pointer p-0 min-w-0"
          aria-expanded={open}
        >
          <i className={`fas fa-chevron-${open ? 'down' : 'right'} w-3 text-sm text-muted-foreground mt-1.5`}></i>
          <span className="min-w-0">
            <span className="block text-lg font-semibold text-foreground">{t('Linked form answers')}</span>
            <span className="block text-sm text-muted-foreground">
              {linkedForm
                ? t('Choose which answers from "{{name}}" are shown beside this form. Hidden answers are not sent to reviewers.', { name: localised(linkedForm.name, language) })
                : t('Choose which answers from the linked form are shown beside this form.')}
            </span>
          </span>
        </button>
        {linkedForm && sections.length > 0 && (
          <div className="flex items-center gap-4 pt-1">
            <span className="text-sm text-muted-foreground whitespace-nowrap">
              {t('{{shown}} of {{total}} shown', { shown: shownCount, total: allQuestionIds.length })}
            </span>
            {open && (
              <>
                <button type="button" className={linkBtn} onClick={showAll} disabled={shownCount === allQuestionIds.length}>
                  {t('Show all')}
                </button>
                <button type="button" className={linkBtn} onClick={hideAll} disabled={shownCount === 0}>
                  {t('Hide all')}
                </button>
              </>
            )}
          </div>
        )}
      </div>
      {open && <div className="mt-4">{renderBody()}</div>}
    </div>
  );
};

export default LinkedFormDisplayEditor;
