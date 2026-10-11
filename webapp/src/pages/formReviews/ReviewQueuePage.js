import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { reviewService } from "../../services/reviews/review.service";
import { resolveContentLanguage } from "../../utils/eventLanguages";
import { Button } from "../../components/ui/button";
import {
  STATUS, ReviewStatusBadge, identifierText, formatScore, formatDate, ProgressBar, PageMessage, Spinner,
} from "./reviewUtils";

const FILTERS = ['todo', 'submitted', 'all'];

/** The reviewer's assignments for the event's active review stage. */
export default function ReviewQueuePage({ event, history }) {
  const { t, i18n } = useTranslation();
  const language = resolveContentLanguage(event, i18n.language);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('todo');

  useEffect(() => {
    reviewService.getAssignedReviews(event.id, language).then(result => {
      if (result.error) setError(result.error);
      else setData(result.data);
    });
  }, [event.id, language]);

  const assignments = useMemo(() => (data ? data.assignments : []), [data]);
  const visible = useMemo(() => assignments.filter(a => {
    if (filter === 'todo') return a.status !== STATUS.SUBMITTED;
    if (filter === 'submitted') return a.status === STATUS.SUBMITTED;
    return true;
  }), [assignments, filter]);

  if (error) return <PageMessage icon="fa-clipboard-list" title={t('Reviews')}>{error}</PageMessage>;
  if (!data) return <Spinner />;

  const { counts } = data;
  // Carry on with a half-finished review before starting a fresh one.
  const next = assignments.find(a => a.status === STATUS.IN_PROGRESS)
    || assignments.find(a => a.status === STATUS.NOT_STARTED);
  const reviewUrl = id => `/${event.key}/reviews/${id}`;
  const filterLabels = {
    todo: t('To do ({{count}})', { count: counts.remaining }),
    submitted: t('Submitted ({{count}})', { count: counts.submitted }),
    all: t('All ({{count}})', { count: counts.total }),
  };

  return (
    <div className="w-full max-w-4xl mx-auto pt-6 px-4 space-y-6 text-left">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="font-heading text-2xl font-bold text-foreground">{t('Your Reviews')}</h1>
          <p className="text-sm text-muted-foreground">
            {data.form_name || t('Review')} · {t('Stage {{stage}}', { stage: data.stage })}
          </p>
        </div>
        <Link to={`/${event.key}/reviews/history`} className="text-sm font-semibold text-action hover:underline">
          <i className="fas fa-history mr-1.5" />{t('Review History')}
        </Link>
      </header>

      {!data.is_open && (
        <div className="flex items-center gap-3 p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-800 text-sm">
          <i className="fas fa-lock" />
          {t('Reviewing is currently closed. You can look at your reviews but not change them.')}
        </div>
      )}

      <section className="bg-white rounded-2xl border border-border shadow-sm p-6 space-y-4">
        {counts.total === 0 ? (
          <div className="text-center space-y-2 py-4">
            <i className="fas fa-inbox text-3xl text-muted-foreground" />
            <p className="font-semibold text-foreground">{t('No reviews have been assigned to you yet.')}</p>
            <p className="text-sm text-muted-foreground">{t('You will receive an email when reviews are assigned to you.')}</p>
          </div>
        ) : counts.remaining === 0 ? (
          <div className="text-center space-y-2 py-4">
            <i className="fas fa-check-circle text-4xl text-primary" />
            <p className="font-heading text-xl font-bold text-foreground">{t('All Done!')}</p>
            <p className="text-sm text-muted-foreground">
              {t('You have completed all your reviews! Please let us know if you have any capacity for more')}
            </p>
            <p className="text-sm text-muted-foreground">{t('Thank you for your contribution!')}</p>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-semibold text-foreground">
                  {t('{{submitted}} of {{total}} reviews submitted', { submitted: counts.submitted, total: counts.total })}
                </span>
                <span className="text-muted-foreground">{t('{{count}} remaining', { count: counts.remaining })}</span>
              </div>
              <ProgressBar value={counts.submitted} total={counts.total} />
            </div>
            {next && (
              <Button onClick={() => history.push(reviewUrl(next.review_response_id))}>
                <i className="fas fa-play" />
                {next.status === STATUS.IN_PROGRESS ? t('Continue reviewing') : t('Start next review')}
              </Button>
            )}
          </div>
        )}
      </section>

      {counts.total > 0 && (
        <section className="space-y-3">
          <div className="flex gap-1 p-1 bg-surface-high rounded-lg w-fit" role="tablist">
            {FILTERS.map(key => (
              <button key={key} type="button" role="tab" aria-selected={filter === key}
                      onClick={() => setFilter(key)}
                      className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                        filter === key ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}>
                {filterLabels[key]}
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">{t('Nothing here.')}</p>
          ) : (
            <ul className="bg-white rounded-2xl border border-border shadow-sm divide-y divide-border overflow-hidden">
              {visible.map(a => (
                <li key={a.review_response_id}>
                  <Link to={reviewUrl(a.review_response_id)}
                        className="flex items-center gap-4 px-5 py-4 hover:bg-surface-low transition-colors">
                    <div className="flex-1 min-w-0 space-y-1">
                      <p className="font-semibold text-foreground truncate">
                        {identifierText(a.identifiers, a.application_response_id, t)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t('Response ID')}: {a.application_response_id}
                        {a.submitted_timestamp && <> · {t('Submitted')} {formatDate(a.submitted_timestamp)}</>}
                      </p>
                    </div>
                    {a.status === STATUS.SUBMITTED && (
                      <span className="hidden sm:block text-sm text-muted-foreground">
                        {t('Score')}: <span className="font-bold text-foreground">{formatScore(a.total_score)}</span>
                      </span>
                    )}
                    <ReviewStatusBadge status={a.status} t={t} />
                    <i className="fas fa-chevron-right text-xs text-muted-foreground" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
