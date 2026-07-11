import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import { formatInEventTz } from '../../utils/datetime';

var FILTERS = { ALL: 'all', SUBSCRIBED: 'subscribed' };

function DiscussionBoard(props) {
  var event = props.event, history = props.history;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;
  var timezone = (event && event.timezone) || 'UTC';

  var [filter, setFilter] = useState(FILTERS.ALL);
  var [threads, setThreads] = useState([]);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);

  function load() {
    if (!eventId) { setLoading(false); return; }
    setLoading(true);
    var request = filter === FILTERS.SUBSCRIBED
      ? discussionService.listSubscriptions(eventId)
      : discussionService.listThreads(eventId);
    request.then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setThreads(r.data || []);
    });
  }
  useEffect(load, [eventId, filter]);

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold text-foreground">{t('Discussion')}</h1>
        <button
          onClick={function () { history.push('/' + eventKey + '/event-app/discussion/new'); }}
          className="bg-primary text-primary-foreground text-sm font-semibold px-4 py-2 rounded-full">
          {t('New post')}
        </button>
      </div>

      <div className="flex gap-2 border-b border-border">
        {[FILTERS.ALL, FILTERS.SUBSCRIBED].map(function (f) {
          var label = f === FILTERS.ALL ? t('All discussions') : t('My subscriptions');
          return (
            <button
              key={f}
              onClick={function () { setFilter(f); }}
              className={'pb-2 px-1 text-sm font-medium border-b-2 transition-colors ' + (filter === f ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground')}
            >
              {label}
            </button>
          );
        })}
      </div>

      {loading && <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>}
      {!loading && error && <div className="w-full pt-6 text-center text-destructive">{error}</div>}

      {!loading && !error && threads.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">
          {filter === FILTERS.SUBSCRIBED ? t("You're not subscribed to any discussions yet.") : t('No discussions yet. Start one!')}
        </p>
      )}

      {!loading && !error && (
        <div className="space-y-3">
          {threads.map(function (th) {
            return (
              <button key={th.id}
                onClick={function () { history.push('/' + eventKey + '/event-app/discussion/' + th.id); }}
                className={'w-full text-left rounded-2xl border shadow-sm p-4 transition-all ' + (th.unread ? 'bg-primary/10 border-primary/40 hover:border-primary/60' : 'bg-white border-border hover:border-border/80')}>
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <span className={'w-2.5 h-2.5 rounded-full block ' + (th.unread ? 'bg-primary' : 'bg-border')} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {th.is_pinned && <i className="fas fa-thumbtack text-primary" style={{ fontSize: 12 }} />}
                      <p className={'text-sm truncate ' + (th.unread ? 'font-bold text-foreground' : 'font-medium text-foreground/60')}>
                        {th.subject || t('(no subject)')}
                      </p>
                    </div>
                    <p className={'text-sm mt-1 line-clamp-2 ' + (th.unread ? 'text-foreground/70' : 'text-foreground/40')}>{th.preview}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {th.author.firstname} {th.author.lastname} · {t('{{count}} replies', { count: th.reply_count })} ·{' '}
                      {formatInEventTz(th.last_activity_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
                    </p>
                  </div>
                  {th.unread && (
                    <span className="flex-shrink-0 text-xs font-semibold text-primary-foreground bg-primary px-2 py-0.5 rounded-full self-start">
                      {t('New')}
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default DiscussionBoard;
