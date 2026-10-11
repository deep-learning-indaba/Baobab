import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { reviewService } from "../../services/reviews/review.service";
import { resolveContentLanguage } from "../../utils/eventLanguages";
import { Button } from "../../components/ui/button";
import {
  STATUS, ReviewStatusBadge, identifierText, personName, formatScore, formatDate, ProgressBar, PageMessage, Spinner,
} from "./reviewUtils";

const TABS = ['applications', 'reviews', 'reviewers'];

function StatCard({ label, value, hint }) {
  return (
    <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="font-heading text-2xl font-bold text-foreground">{value}</p>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function SortHeader({ label, column, sort, onSort, className = '' }) {
  const active = sort.column === column;
  return (
    <th scope="col" className={`px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider ${className}`}>
      <button type="button" onClick={() => onSort(column)} className="inline-flex items-center gap-1 hover:text-foreground">
        {label}
        <i className={`fas ${active ? (sort.desc ? 'fa-sort-down' : 'fa-sort-up') : 'fa-sort'} text-[0.65rem]`} />
      </button>
    </th>
  );
}

function matches(search, ...values) {
  if (!search) return true;
  const needle = search.toLowerCase();
  return values.some(v => v && String(v).toLowerCase().includes(needle));
}

function ApplicationsTable({ data, event, search, t }) {
  const [sort, setSort] = useState({ column: 'average_total', desc: true });
  const onSort = column => setSort(prev => ({ column, desc: prev.column === column ? !prev.desc : true }));

  const rows = useMemo(() => {
    const valueOf = (row) => {
      if (sort.column === 'name') return personName(row.applicant).toLowerCase();
      if (sort.column === 'reviews') return row.reviews_submitted;
      if (sort.column === 'average_total') return row.average_total;
      return row.average_scores[sort.column];
    };
    return data.applications
      .filter(a => matches(search, personName(a.applicant), a.applicant.email,
        identifierText(a.identifiers, a.application_response_id, t)))
      .sort((a, b) => {
        const x = valueOf(a), y = valueOf(b);
        // Unscored applications always sink to the bottom.
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        return (x < y ? -1 : x > y ? 1 : 0) * (sort.desc ? -1 : 1);
      });
  }, [data.applications, search, sort, t]);

  if (rows.length === 0) return <p className="text-sm text-muted-foreground text-center py-10">{t('No applications found.')}</p>;

  return (
    <div className="overflow-x-auto bg-white rounded-2xl border border-border shadow-sm">
      <table className="min-w-full divide-y divide-border text-sm text-left">
        <thead className="bg-slate-50">
          <tr>
            <SortHeader label={t('Applicant')} column="name" sort={sort} onSort={onSort} />
            <SortHeader label={t('Reviews')} column="reviews" sort={sort} onSort={onSort} />
            {data.score_questions.map(q => (
              <SortHeader key={q.question_id} column={String(q.question_id)} sort={sort} onSort={onSort}
                          label={<span title={q.headline}>{q.headline.length > 24 ? q.headline.slice(0, 24) + '…' : q.headline} ×{q.weight}</span>} />
            ))}
            <SortHeader label={t('Average total')} column="average_total" sort={sort} onSort={onSort} />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map(row => (
            <tr key={row.application_response_id} className="hover:bg-slate-50/50">
              <td className="px-4 py-3">
                <Link to={`/${event.key}/form-responses/${data.application_form_id}/${row.application_response_id}`}
                      className="font-semibold text-action hover:underline">
                  {personName(row.applicant)}
                </Link>
                <p className="text-xs text-muted-foreground truncate max-w-xs">
                  {identifierText(row.identifiers, row.application_response_id, t)}
                </p>
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span className={row.reviews_submitted >= data.num_reviews_required ? 'text-primary font-semibold' : ''}>
                  {row.reviews_submitted}
                </span>
                <span className="text-muted-foreground"> / {row.reviews_assigned} ({t('{{count}} required', { count: data.num_reviews_required })})</span>
              </td>
              {data.score_questions.map(q => (
                <td key={q.question_id} className="px-4 py-3 whitespace-nowrap">
                  {formatScore(row.average_scores[String(q.question_id)])}
                </td>
              ))}
              <td className="px-4 py-3 whitespace-nowrap font-bold text-foreground">{formatScore(row.average_total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReviewsList({ data, search, t }) {
  const [expanded, setExpanded] = useState(null);
  const rows = data.reviews.filter(r => matches(search,
    personName(r.reviewer), r.reviewer.email, personName(r.applicant),
    identifierText(r.identifiers, r.application_response_id, t)));

  if (rows.length === 0) return <p className="text-sm text-muted-foreground text-center py-10">{t('No reviews found.')}</p>;

  return (
    <ul className="bg-white rounded-2xl border border-border shadow-sm divide-y divide-border overflow-hidden">
      {rows.map(r => {
        const isOpen = expanded === r.review_response_id;
        return (
          <li key={r.review_response_id}>
            <button type="button" onClick={() => setExpanded(isOpen ? null : r.review_response_id)}
                    className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-surface-low transition-colors"
                    aria-expanded={isOpen}>
              <div className="flex-1 min-w-0 space-y-1">
                <p className="font-semibold text-foreground truncate">
                  {personName(r.applicant)}
                  <span className="font-normal text-muted-foreground"> — {identifierText(r.identifiers, r.application_response_id, t)}</span>
                </p>
                <p className="text-xs text-muted-foreground">
                  {t('Reviewed by {{name}}', { name: personName(r.reviewer) })}
                  {r.submitted_timestamp && <> · {formatDate(r.submitted_timestamp)}</>}
                </p>
              </div>
              {r.status === STATUS.SUBMITTED && (
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  {t('Score')}: <span className="font-bold text-foreground">{formatScore(r.total_score)}</span>
                </span>
              )}
              <ReviewStatusBadge status={r.status} t={t} />
              <i className={`fas fa-chevron-${isOpen ? 'up' : 'down'} text-xs text-muted-foreground`} />
            </button>
            {isOpen && (
              <div className="px-5 pb-5 pt-1 bg-slate-50/50">
                {r.answers.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">{t('No answers yet.')}</p>
                ) : (
                  <dl className="grid gap-3">
                    {r.answers.map(a => (
                      <div key={a.question_id}>
                        <dt className="text-xs font-semibold text-muted-foreground">
                          {a.headline}{a.weight > 0 && <span className="ml-1">(×{a.weight})</span>}
                        </dt>
                        <dd className="text-sm text-foreground whitespace-pre-wrap">{a.display_value}</dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function ReviewersTable({ reviewers, search, t }) {
  const rows = (reviewers || []).filter(r => matches(search, personName(r), r.email));
  if (rows.length === 0) return <p className="text-sm text-muted-foreground text-center py-10">{t('No reviewers assigned yet.')}</p>;
  return (
    <ul className="bg-white rounded-2xl border border-border shadow-sm divide-y divide-border overflow-hidden">
      {rows.map(r => (
        <li key={r.reviewer_user_id} className="flex flex-col sm:flex-row sm:items-center gap-3 px-5 py-4">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-foreground">{personName(r)}</p>
            <p className="text-xs text-muted-foreground truncate">{r.email}</p>
          </div>
          <div className="sm:w-64 space-y-1">
            <p className="text-xs text-muted-foreground text-right">
              {t('{{completed}} of {{allocated}} complete', { completed: r.reviews_completed, allocated: r.reviews_allocated })}
            </p>
            <ProgressBar value={r.reviews_completed} total={r.reviews_allocated} />
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Organisers' view of reviewing: scores per application, every review, and reviewer progress. */
export default function ReviewDashboardPage({ event }) {
  const { t, i18n } = useTranslation();
  const language = resolveContentLanguage(event, i18n.language);
  const [stages, setStages] = useState(null);
  const [selectedFormId, setSelectedFormId] = useState(null);
  const [data, setData] = useState(null);
  const [reviewers, setReviewers] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('applications');
  const [search, setSearch] = useState('');
  const [switchingStage, setSwitchingStage] = useState(false);

  const loadStages = useCallback(() => reviewService.getReviewStages(event.id, language).then(result => {
    if (result.error) { setError(result.error); return; }
    setStages(result.data);
    setSelectedFormId(current => {
      if (current) return current;
      const active = result.data.stages.find(s => s.is_active);
      return active ? active.form_id : null;
    });
  }), [event.id, language]);

  useEffect(() => { loadStages(); }, [loadStages]);

  useEffect(() => {
    if (!selectedFormId) return;
    setData(null);
    Promise.all([
      reviewService.getReviewDashboard(selectedFormId, event.id, language),
      reviewService.getFormReviewAssignments(selectedFormId, event.id),
    ]).then(([dashboard, assignments]) => {
      if (dashboard.error) setError(dashboard.error);
      else setData(dashboard.data);
      setReviewers(assignments.reviewers || []);
    });
  }, [selectedFormId, event.id, language]);

  const makeActive = (stage) => {
    setSwitchingStage(true);
    reviewService.setActiveReviewStage(event.id, stage).then(result => {
      setSwitchingStage(false);
      if (result.error) setError(result.error);
      else setStages(result.data);
    });
  };

  if (error) return <PageMessage icon="fa-exclamation-triangle" title={t('Review Dashboard')} tone="error">{error}</PageMessage>;
  if (!stages) return <Spinner />;
  if (stages.stages.length === 0) {
    return (
      <PageMessage icon="fa-clipboard-check" title={t('Review Dashboard')}>
        {t('No review form has been created for this event yet.')}{' '}
        <Link to={`/${event.key}/formConfig`} className="font-semibold text-action hover:underline">{t('Form Configuration')}</Link>
      </PageMessage>
    );
  }

  const selectedStage = stages.stages.find(s => s.form_id === selectedFormId);
  const submittedReviews = data ? data.reviews.filter(r => r.status === STATUS.SUBMITTED).length : 0;
  const fullyReviewed = data ? data.applications.filter(a => a.reviews_submitted >= data.num_reviews_required).length : 0;
  const tabLabels = {
    applications: t('Applications'),
    reviews: t('Reviews'),
    reviewers: t('Reviewers'),
  };

  return (
    <div className="w-full max-w-6xl mx-auto pt-6 px-4 space-y-6 text-left">
      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="font-heading text-2xl font-bold text-foreground">{t('Review Dashboard')}</h1>
          <p className="text-sm text-muted-foreground">
            {selectedStage && (selectedStage.form_name || t('Review'))}
          </p>
        </div>
        {stages.stages.length > 1 && (
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-sm text-muted-foreground" htmlFor="review-stage">{t('Stage')}</label>
            <select id="review-stage" className="rounded-lg border border-border bg-white px-3 py-1.5 text-sm"
                    value={selectedFormId || ''} onChange={e => setSelectedFormId(parseInt(e.target.value, 10))}>
              {stages.stages.map(s => (
                <option key={s.form_id} value={s.form_id}>
                  {t('Stage {{stage}}', { stage: s.stage })}{s.is_active ? ` (${t('active')})` : ''}
                </option>
              ))}
            </select>
            {selectedStage && !selectedStage.is_active && (
              <Button size="sm" variant="secondary" disabled={switchingStage} onClick={() => makeActive(selectedStage.stage)}>
                {t('Make this the active stage')}
              </Button>
            )}
          </div>
        )}
      </header>

      {!data ? <Spinner /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label={t('Applications')} value={data.applications.length} />
            <StatCard label={t('Fully reviewed')} value={fullyReviewed}
                      hint={t('{{count}} review(s) required each', { count: data.num_reviews_required })} />
            <StatCard label={t('Reviews submitted')} value={submittedReviews}
                      hint={t('of {{count}} assigned', { count: data.reviews.length })} />
            <StatCard label={t('Reviewers')} value={(reviewers || []).length} />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
            <div className="flex gap-1 p-1 bg-surface-high rounded-lg w-fit" role="tablist">
              {TABS.map(key => (
                <button key={key} type="button" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}
                        className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                          tab === key ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                  {tabLabels[key]}
                </button>
              ))}
            </div>
            <input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('Search')}
                   className="w-full sm:w-64 rounded-lg border border-border bg-white px-3 py-1.5 text-sm" />
          </div>

          {tab === 'applications' && <ApplicationsTable data={data} event={event} search={search} t={t} />}
          {tab === 'reviews' && <ReviewsList data={data} search={search} t={t} />}
          {tab === 'reviewers' && <ReviewersTable reviewers={reviewers} search={search} t={t} />}
        </>
      )}
    </div>
  );
}
