import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import { formatInEventTz } from '../../utils/datetime';

function DiscussionReportsAdmin(props) {
  var event = props.event;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var timezone = (event && event.timezone) || 'UTC';

  var [reports, setReports] = useState([]);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);

  function load() {
    if (!eventId) { setLoading(false); return; }
    discussionService.listReports(eventId).then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setReports(r.data || []);
    });
  }
  useEffect(load, [eventId]);

  function handleDismiss(reportId) {
    discussionService.dismissReport(eventId, reportId).then(function (r) {
      if (!r.error) load();
    });
  }

  function handleDeleteMessage(messageId, reportId) {
    if (!window.confirm(t('Delete this message?'))) return;
    discussionService.deleteMessage(eventId, messageId).then(function (r) {
      if (!r.error) discussionService.dismissReport(eventId, reportId).then(load);
    });
  }

  if (loading) return <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>;
  if (error) return <div className="w-full pt-6 text-center text-destructive">{t('Access denied')}</div>;

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <h1 className="font-heading text-2xl font-bold text-foreground">{t('Reported messages')}</h1>

      {reports.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">{t('No reported messages.')}</p>
      )}

      <div className="space-y-3">
        {reports.map(function (r) {
          return (
            <div key={r.report_id} className="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-2">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-muted-foreground">
                    {t('Reported by')} {r.reporter.firstname} {r.reporter.lastname} ·{' '}
                    {formatInEventTz(r.created_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
                  </p>
                  {r.reason && <p className="text-sm text-foreground mt-1">{t('Reason')}: {r.reason}</p>}
                  <div className="mt-2 p-3 bg-muted/30 rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground mb-1">
                      {r.message_author ? r.message_author.firstname + ' ' + r.message_author.lastname : ''}
                    </p>
                    <p className="text-sm text-foreground/80">
                      {r.message_is_deleted ? t('Message deleted by author') : r.message_excerpt}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col gap-2 flex-shrink-0">
                  {!r.message_is_deleted && (
                    <button
                      onClick={function () { handleDeleteMessage(r.message_id, r.report_id); }}
                      className="px-3 py-1.5 rounded-lg border border-destructive text-destructive text-xs font-semibold hover:bg-destructive/5"
                    >
                      {t('Delete message')}
                    </button>
                  )}
                  <button
                    onClick={function () { handleDismiss(r.report_id); }}
                    className="px-3 py-1.5 rounded-lg border border-border text-foreground text-xs font-semibold hover:bg-muted/40"
                  >
                    {t('Dismiss')}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default DiscussionReportsAdmin;
