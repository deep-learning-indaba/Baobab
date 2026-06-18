import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { announcementService } from '../../services/eventApp/announcement.service';
import { formatInEventTz } from '../../utils/datetime';
import MarkdownRenderer from '../../components/MarkdownRenderer';

function AnnouncementInbox(props) {
  var event = props.event;
  var history = props.history;
  var { t, i18n } = useTranslation();
  var language = (i18n.language || 'en').slice(0, 2);

  var [items, setItems] = useState([]);
  var [isLoading, setIsLoading] = useState(true);
  var [error, setError] = useState(null);

  var eventId = event && event.id;
  var timezone = (event && event.timezone) || 'UTC';
  var eventKey = event && event.key;

  useEffect(function() {
    if (!eventId) { setIsLoading(false); return; }
    announcementService.listInbox(eventId, language).then(function(result) {
      setIsLoading(false);
      if (result.error) setError(result.error);
      else setItems(result.data || []);
    });
  }, [eventId, language]);

  if (isLoading) {
    return React.createElement('div', { className: 'w-full pt-6 text-center text-muted-foreground' }, t('Loading'));
  }

  if (error) {
    return React.createElement('div', { className: 'w-full pt-6 text-center text-destructive' }, error);
  }

  var unreadCount = items.filter(function(a) { return !a.read; }).length;

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="font-heading text-2xl font-bold text-foreground">{t('Announcements')}</h1>
        {unreadCount > 0 && (
          <span className="bg-primary text-primary-foreground text-xs font-bold px-2 py-0.5 rounded-full">
            {unreadCount}
          </span>
        )}
      </div>

      {items.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">{t('No announcements yet.')}</p>
      )}

      <div className="space-y-3">
        {items.map(function(ann) {
          return (
            <button
              key={ann.id}
              onClick={function() { history.push('/' + eventKey + '/event-app/announcements/' + ann.id); }}
              className={'w-full text-left rounded-2xl border shadow-sm p-4 transition-all ' + (ann.read ? 'bg-white border-border hover:border-border/80' : 'bg-primary/10 border-primary/40 hover:border-primary/60')}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {ann.read
                    ? <span className="w-2.5 h-2.5 rounded-full bg-border block" />
                    : <span className="w-2.5 h-2.5 rounded-full bg-primary block" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <p className={ann.read ? 'text-sm font-medium text-foreground/60' : 'text-sm font-bold text-foreground'}>
                    {ann.title}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {ann.sent_at ? formatInEventTz(ann.sent_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' }) : ''}
                  </p>
                  <p className={'text-sm mt-1 line-clamp-2 ' + (ann.read ? 'text-foreground/40' : 'text-foreground/70')}>
                    {ann.body_markdown}
                  </p>
                </div>
                {!ann.read && (
                  <span className="flex-shrink-0 text-xs font-semibold text-primary-foreground bg-primary px-2 py-0.5 rounded-full self-start">
                    {t('New')}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function AnnouncementDetail(props) {
  var event = props.event;
  var announcementId = props.match && props.match.params && props.match.params.announcementId;
  var history = props.history;
  var { t, i18n } = useTranslation();
  var language = (i18n.language || 'en').slice(0, 2);

  var [ann, setAnn] = useState(null);
  var [isLoading, setIsLoading] = useState(true);
  var [error, setError] = useState(null);

  var eventId = event && event.id;
  var timezone = (event && event.timezone) || 'UTC';
  var eventKey = event && event.key;

  useEffect(function() {
    if (!eventId || !announcementId) { setIsLoading(false); return; }
    announcementService.getAnnouncement(eventId, announcementId, language).then(function(result) {
      setIsLoading(false);
      if (result.error) setError(result.error);
      else setAnn(result.data);
    });
  }, [eventId, announcementId, language]);

  if (isLoading) {
    return React.createElement('div', { className: 'w-full pt-6 text-center text-muted-foreground' }, t('Loading'));
  }
  if (error) {
    return React.createElement('div', { className: 'w-full pt-6 text-center text-destructive' }, error);
  }
  if (!ann) return null;

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <button
        onClick={function() { history.push('/' + eventKey + '/event-app/announcements'); }}
        className="flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        {t('Back to Announcements')}
      </button>

      <div className="bg-white rounded-2xl border border-border shadow-sm p-6 space-y-4">
        <div>
          <h1 className="font-heading text-xl font-bold text-foreground">{ann.title}</h1>
          <p className="text-xs text-muted-foreground mt-1">
            {ann.sent_at ? formatInEventTz(ann.sent_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short', year: 'numeric' }) : ''}
            {ann.expiry_at && (
              <span className="ml-3 text-muted-foreground/70">
                {t('Expires')} {formatInEventTz(ann.expiry_at, timezone, { day: 'numeric', month: 'short' })}
              </span>
            )}
          </p>
        </div>
        <div className="prose prose-sm max-w-none text-foreground">
          <MarkdownRenderer source={ann.body_markdown} />
        </div>
      </div>
    </div>
  );
}

export { AnnouncementInbox, AnnouncementDetail };
export default AnnouncementInbox;
