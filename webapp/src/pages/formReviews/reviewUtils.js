import React from "react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { formatUserName } from "../../utils/userName";

export const STATUS = {
  NOT_STARTED: 'not_started',
  IN_PROGRESS: 'in_progress',
  SUBMITTED: 'submitted',
};

/** Previous / next page controls; renders nothing for a single page. */
export function Pager({ page, totalPages, onPage, t }) {
  if (!totalPages || totalPages <= 1) return null;
  return (
    <nav className="flex items-center justify-center gap-3">
      <Button variant="outline" size="sm" disabled={page === 0} onClick={() => onPage(page - 1)}>
        <i className="fas fa-chevron-left" />{t('Previous')}
      </Button>
      <span className="text-sm text-muted-foreground">
        {t('Page {{page}} of {{total}}', { page: page + 1, total: totalPages })}
      </span>
      <Button variant="outline" size="sm" disabled={page + 1 >= totalPages} onClick={() => onPage(page + 1)}>
        {t('Next')}<i className="fas fa-chevron-right" />
      </Button>
    </nav>
  );
}

export function ReviewStatusBadge({ status, t }) {
  if (status === STATUS.SUBMITTED) return <Badge variant="success">{t('Submitted')}</Badge>;
  if (status === STATUS.IN_PROGRESS) return <Badge variant="warning">{t('In progress')}</Badge>;
  return <Badge variant="secondary">{t('Not started')}</Badge>;
}

export function personName(person) {
  if (!person) return '';
  return formatUserName(person.user_title, person.firstname, person.lastname);
}

/** One-line description of an application from its 'review-identifier' answers. */
export function identifierText(identifiers, applicationResponseId, t) {
  const values = (identifiers || []).map(i => i.value).filter(Boolean);
  if (values.length > 0) return values.join(' · ');
  return t('Application #{{id}}', { id: applicationResponseId });
}

/** Weighted questions of a serialised form: those with settings.weight > 0. */
export function weightedQuestions(form) {
  const result = [];
  for (const section of (form && form.sections) || []) {
    for (const q of section.questions || []) {
      const weight = (q.settings && q.settings.weight) || 0;
      if (weight > 0) result.push({ id: q.id, weight });
    }
  }
  return result;
}

/** The same weighted total the server computes (FormResponse.calculate_score). */
export function weightedScore(form, answers) {
  const byQuestion = {};
  for (const a of answers || []) byQuestion[a.question_id] = a.value;
  return weightedQuestions(form).reduce((total, q) => {
    const value = parseFloat(byQuestion[q.id]);
    return Number.isNaN(value) ? total : total + value * q.weight;
  }, 0);
}

export function formatScore(score) {
  if (score === null || score === undefined) return '–';
  return Number.isInteger(score) ? String(score) : score.toFixed(2);
}

export function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export function ProgressBar({ value, total }) {
  const percent = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="h-2 w-full bg-surface-high rounded-full overflow-hidden" role="progressbar"
         aria-valuenow={value} aria-valuemin={0} aria-valuemax={total}>
      <div className="h-full bg-primary rounded-full transition-[width] duration-300" style={{ width: `${percent}%` }} />
    </div>
  );
}

export function PageMessage({ icon, title, children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-white border-border',
    error: 'bg-error/5 border-error/20 text-error',
  };
  return (
    <div className={`max-w-xl mx-auto mt-10 rounded-2xl border p-8 text-center space-y-3 ${tones[tone]}`}>
      {icon && <i className={`fas ${icon} text-3xl ${tone === 'error' ? '' : 'text-muted-foreground'}`} />}
      {title && <h2 className="font-heading text-lg font-bold">{title}</h2>}
      {children && <div className="text-sm text-muted-foreground">{children}</div>}
    </div>
  );
}

export function Spinner() {
  return (
    <div className="flex justify-center items-center py-16">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}
