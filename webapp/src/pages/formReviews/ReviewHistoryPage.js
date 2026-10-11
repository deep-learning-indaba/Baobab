import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { reviewService } from "../../services/reviews/review.service";
import { resolveContentLanguage } from "../../utils/eventLanguages";
import { Button } from "../../components/ui/button";
import { identifierText, formatScore, formatDate, PageMessage, Spinner } from "./reviewUtils";

const PAGE_SIZE = 20;

/** Every review the current reviewer has submitted for the event, all stages. */
export default function ReviewHistoryPage({ event }) {
  const { t, i18n } = useTranslation();
  const language = resolveContentLanguage(event, i18n.language);
  const [page, setPage] = useState(0);
  const [sortColumn, setSortColumn] = useState('submitted_timestamp');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    reviewService.getMyReviewHistory(event.id, page, PAGE_SIZE, sortColumn, language).then(result => {
      if (result.error) setError(result.error);
      else setData(result.data);
    });
  }, [event.id, page, sortColumn, language]);

  if (error) return <PageMessage icon="fa-history" title={t('Review History')}>{error}</PageMessage>;
  if (!data) return <Spinner />;

  return (
    <div className="w-full max-w-4xl mx-auto pt-6 px-4 space-y-6 text-left">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div className="space-y-1">
          <Link to={`/${event.key}/reviews`} className="text-sm font-medium text-action hover:underline">
            ← {t('Your Reviews')}
          </Link>
          <h1 className="font-heading text-2xl font-bold text-foreground">{t('Review History')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('{{count}} submitted review(s)', { count: data.num_entries })}
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          {t('Sort by')}
          <select className="rounded-lg border border-border bg-white px-3 py-1.5 text-sm text-foreground"
                  value={sortColumn}
                  onChange={e => { setSortColumn(e.target.value); setPage(0); }}>
            <option value="submitted_timestamp">{t('Most recently submitted')}</option>
            <option value="review_response_id">{t('Most recently assigned')}</option>
          </select>
        </label>
      </header>

      {data.reviews.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-10">{t('You have not submitted any reviews yet.')}</p>
      ) : (
        <ul className="bg-white rounded-2xl border border-border shadow-sm divide-y divide-border overflow-hidden">
          {data.reviews.map(r => (
            <li key={r.review_response_id}>
              <Link to={`/${event.key}/reviews/${r.review_response_id}`}
                    className="flex items-center gap-4 px-5 py-4 hover:bg-surface-low transition-colors">
                <div className="flex-1 min-w-0 space-y-1">
                  <p className="font-semibold text-foreground truncate">
                    {identifierText(r.identifiers, r.application_response_id, t)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t('Stage {{stage}}', { stage: r.stage })} · {t('Response ID')}: {r.application_response_id}
                    {' · '}{t('Submitted')} {formatDate(r.submitted_timestamp)}
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">
                  {t('Score')}: <span className="font-bold text-foreground">{formatScore(r.total_score)}</span>
                </span>
                <i className="fas fa-chevron-right text-xs text-muted-foreground" />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {data.total_pages > 1 && (
        <nav className="flex items-center justify-center gap-3">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
            <i className="fas fa-chevron-left" />{t('Previous')}
          </Button>
          <span className="text-sm text-muted-foreground">
            {t('Page {{page}} of {{total}}', { page: page + 1, total: data.total_pages })}
          </span>
          <Button variant="outline" size="sm" disabled={page + 1 >= data.total_pages} onClick={() => setPage(page + 1)}>
            {t('Next')}<i className="fas fa-chevron-right" />
          </Button>
        </nav>
      )}
    </div>
  );
}
