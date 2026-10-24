import React from "react";
import { useTranslation } from "react-i18next";
import { getDownloadURL } from "../../utils/files";
import { formatAnswerForDisplay } from "../../pages/formRenderer/utils/answerDisplay";

// Question types that render no input, so have no answer to show.
const DISPLAY_ONLY_TYPES = ['information', 'sub-heading'];

export function localised(value, language) {
  if (!value) return '';
  if (typeof value === 'string') return value;
  return value[language] || value.en || Object.values(value)[0] || '';
}

export function AnswerValue({ question, answer, language, emptyText }) {
  const { t } = useTranslation();
  if (!answer || answer.value === null || answer.value === undefined || answer.value === '') {
    return <span className="text-muted-foreground italic">{emptyText || t('No answer provided.')}</span>;
  }

  const value = answer.value;
  const type = question ? question.type : null;

  if (type === 'file') {
    return (
      <a href={getDownloadURL(value)} target="_blank" rel="noopener noreferrer"
         className="text-primary hover:underline">
        {t('Uploaded File')}
      </a>
    );
  }

  if (type === 'multi-file') {
    let files = null;
    try { files = JSON.parse(value); } catch (_) { files = null; }
    if (Array.isArray(files) && files.length > 0) {
      return (
        <div className="space-y-1">
          {files.map(f => (
            <div key={f.name}>
              <a href={getDownloadURL(JSON.stringify(f))} target="_blank" rel="noopener noreferrer"
                 className="text-primary hover:underline">{f.name}</a>
            </div>
          ))}
        </div>
      );
    }
    return <span className="text-muted-foreground italic">{t('No files uploaded')}</span>;
  }

  // Option labels rather than stored values, Yes/No for checkboxes.
  const formatted = formatAnswerForDisplay(question, value, language, t);
  if (formatted !== null && formatted !== value) {
    return <span>{formatted}</span>;
  }
  return <span className="whitespace-pre-wrap">{value}</span>;
}

function activeAnswersByQuestionId(answers) {
  const byId = {};
  for (const a of answers || []) {
    if (a.is_active !== false) byId[a.question_id] = a;
  }
  return byId;
}

/**
 * The sections of `form` that have something to show, each with its
 * answerable questions. Questions removed from the form since are kept when
 * they were answered.
 */
export function answerSections(form, answers) {
  if (!form) return [];
  const answersByQuestionId = activeAnswersByQuestionId(answers);
  return (form.sections || [])
    .map(section => ({
      section,
      questions: (section.questions || [])
        .filter(q => !DISPLAY_ONLY_TYPES.includes(q.type))
        .filter(q => q.is_active !== false || answersByQuestionId[q.id]),
    }))
    .filter(({ questions }) => questions.length > 0);
}

export function QuestionAnswers({ questions, answers, language = 'en', emptyText }) {
  const { t } = useTranslation();
  const answersByQuestionId = activeAnswersByQuestionId(answers);
  return questions.map(q => (
    <div key={q.id} className="space-y-1">
      <p className="text-sm font-semibold text-foreground/90">
        {localised(q.headline, language)}
        {q.is_active === false && (
          <span className="ml-2 text-xs font-normal text-muted-foreground italic">
            ({t('removed from form')})
          </span>
        )}
      </p>
      <div className="text-sm text-foreground pl-2 break-words">
        <AnswerValue question={q} answer={answersByQuestionId[q.id]} language={language} emptyText={emptyText} />
      </div>
    </div>
  ));
}

/** Read-only rendering of a response's answers, grouped by the form's sections. */
export default function ResponseAnswers({ form, answers, language = 'en' }) {
  return (
    <div className="space-y-6 text-left">
      {answerSections(form, answers).map(({ section, questions }) => {
        const sectionName = localised(section.name, language);
        return (
          <section key={section.id} className="space-y-4">
            {sectionName && (
              <h3 className="text-base font-bold text-foreground border-b border-border pb-2">{sectionName}</h3>
            )}
            <QuestionAnswers questions={questions} answers={answers} language={language} />
          </section>
        );
      })}
    </div>
  );
}
