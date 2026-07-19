import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import DiscussionThreadListItem from './DiscussionThreadListItem';

function DiscussionBoard(props) {
  var event = props.event, history = props.history;
  var spaceId = props.match && props.match.params && props.match.params.spaceId;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;
  var timezone = (event && event.timezone) || 'UTC';

  var [space, setSpace] = useState(null);
  var [threads, setThreads] = useState([]);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);

  function load() {
    if (!eventId || !spaceId) { setLoading(false); return; }
    setLoading(true);
    discussionService.listThreads(eventId, spaceId).then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setThreads(r.data || []);
    });
  }
  useEffect(load, [eventId, spaceId]);

  useEffect(function () {
    if (!eventId || !spaceId) return;
    discussionService.getSpace(eventId, spaceId).then(function (r) {
      if (!r.error) setSpace(r.data);
    });
  }, [eventId, spaceId]);

  return (
    <div className="w-full max-w-5xl pt-6 space-y-4">
      <button
        onClick={function () { history.push('/' + eventKey + '/event-app/discussion'); }}
        className="flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <i className="fas fa-chevron-left" style={{ fontSize: 13 }} />
        {t('Back to Discussion')}
      </button>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-bold text-foreground">{space ? space.name : t('Discussion')}</h1>
          {space && space.description && (
            <p className="text-sm text-muted-foreground mt-1">{space.description}</p>
          )}
        </div>
        {space && !space.is_archived && (
          <button
            onClick={function () { history.push('/' + eventKey + '/event-app/discussion/space/' + spaceId + '/new'); }}
            className="bg-primary text-primary-foreground text-sm font-semibold px-4 py-2 rounded-full">
            {t('New post')}
          </button>
        )}
      </div>

      {space && space.is_archived && (
        <p className="text-xs text-muted-foreground bg-muted/30 rounded-lg px-3 py-2">
          {t('This space has been archived. Existing threads are still visible, but new posts are no longer accepted.')}
        </p>
      )}

      {loading && <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>}
      {!loading && error && <div className="w-full pt-6 text-center text-destructive">{error}</div>}

      {!loading && !error && threads.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">{t('No discussions yet. Start one!')}</p>
      )}

      {!loading && !error && (
        <div className="space-y-3">
          {threads.map(function (th) {
            return (
              <DiscussionThreadListItem
                key={th.id}
                thread={th} t={t} timezone={timezone}
                onClick={function () { history.push('/' + eventKey + '/event-app/discussion/' + th.id); }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

export default DiscussionBoard;
