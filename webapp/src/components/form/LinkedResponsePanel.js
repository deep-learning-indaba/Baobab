import React, { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { answerSections, localised, QuestionAnswers } from "./ResponseAnswers";

// Below this many sections the whole response is easy enough to scroll.
const JUMP_TO_MIN_SECTIONS = 3;

/**
 * A linked form's response (the application, beside a review form), in a
 * panel that scrolls on its own, with collapsible sections and a jump-to menu.
 * Pass `emptyText` to label every answer slot instead, as the admin preview
 * does with no response to show.
 */
export default function LinkedResponsePanel({ form, answers, language = 'en', title, emptyText, className = '' }) {
  const { t } = useTranslation();
  const scrollRef = useRef(null);
  const [collapsed, setCollapsed] = useState({});
  const sections = answerSections(form, emptyText ? [] : answers);

  const jumpTo = (sectionId) => {
    if (!sectionId) return;
    setCollapsed(prev => ({ ...prev, [sectionId]: false }));
    const container = scrollRef.current;
    const target = container && container.querySelector(`[data-section-id="${sectionId}"]`);
    // Scroll only the panel: scrollIntoView would also scroll the page.
    if (target) container.scrollTo({ top: target.offsetTop, behavior: 'smooth' });
  };

  const namedSections = sections.filter(({ section }) => localised(section.name, language));

  return (
    <section className={`bg-white rounded-2xl border border-border shadow-sm flex flex-col min-h-0 ${className}`}>
      <div className="px-6 py-4 border-b border-border flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-lg! font-bold text-foreground m-0">{title}</h2>
        {namedSections.length >= JUMP_TO_MIN_SECTIONS && (
          <select
            value=""
            onChange={(e) => jumpTo(Number(e.target.value))}
            aria-label={t('Jump to section')}
            className="max-w-full sm:max-w-[16rem] px-2 py-1 border border-border rounded-md text-sm bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">{t('Jump to section...')}</option>
            {namedSections.map(({ section }) => (
              <option key={section.id} value={section.id}>{localised(section.name, language)}</option>
            ))}
          </select>
        )}
      </div>

      <div ref={scrollRef} className="relative p-6 overflow-y-auto space-y-6 text-left">
        {sections.length === 0 && (
          <p className="text-sm text-muted-foreground italic">{t('No answers to show.')}</p>
        )}
        {sections.map(({ section, questions }) => {
          const name = localised(section.name, language);
          const isCollapsed = !!collapsed[section.id];
          return (
            <section key={section.id} data-section-id={section.id} className="space-y-4">
              {name && (
                <h3 className="text-base! font-bold text-foreground border-b border-border pb-2 mt-0">
                  <button
                    type="button"
                    onClick={() => setCollapsed(prev => ({ ...prev, [section.id]: !isCollapsed }))}
                    aria-expanded={!isCollapsed}
                    className="w-full flex items-center gap-2 text-left bg-transparent border-none cursor-pointer p-0 font-bold"
                  >
                    <i className={`fas fa-chevron-${isCollapsed ? 'right' : 'down'} w-3 text-xs text-muted-foreground`} />
                    <span className="flex-1 min-w-0">{name}</span>
                  </button>
                </h3>
              )}
              {!isCollapsed && (
                <QuestionAnswers questions={questions} answers={answers} language={language} emptyText={emptyText} />
              )}
            </section>
          );
        })}
      </div>
    </section>
  );
}
