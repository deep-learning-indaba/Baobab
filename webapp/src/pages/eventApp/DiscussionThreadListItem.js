import React from 'react';
import { formatInEventTz } from '../../utils/datetime';

function DiscussionThreadListItem(props) {
  var th = props.thread, t = props.t, timezone = props.timezone, onClick = props.onClick;
  var spaceName = props.spaceName, onUnsubscribe = props.onUnsubscribe;

  return (
    <div
      className={'w-full rounded-2xl border shadow-sm p-4 transition-all flex items-start gap-3 ' +
        (th.unread ? 'bg-primary/10 border-primary/40 hover:border-primary/60' : 'bg-white border-border hover:border-border/80')}
    >
      <button onClick={onClick} className="flex-1 min-w-0 text-left flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <span className={'w-2.5 h-2.5 rounded-full block ' + (th.unread ? 'bg-primary' : 'bg-border')} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {th.is_pinned && <i className="fas fa-thumbtack text-primary" style={{ fontSize: 12 }} />}
            <p className={'text-sm truncate ' + (th.unread ? 'font-bold text-foreground' : 'font-medium text-foreground/60')}>
              {th.subject || t('(no subject)')}
            </p>
            {spaceName && (
              <span className="text-xs font-semibold text-muted-foreground bg-muted/40 px-2 py-0.5 rounded-full flex-shrink-0">
                {spaceName}
              </span>
            )}
          </div>
          <p className={'text-sm mt-1 line-clamp-2 ' + (th.unread ? 'text-foreground/70' : 'text-foreground/40')}>{th.preview}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {th.author.firstname} {th.author.lastname} · {t('{{count}} replies', { count: th.reply_count })} ·{' '}
            {formatInEventTz(th.last_activity_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
          </p>
        </div>
      </button>
      {th.unread && (
        <span className="flex-shrink-0 text-xs font-semibold text-primary-foreground bg-primary px-2 py-0.5 rounded-full self-start">
          {t('New')}
        </span>
      )}
      {onUnsubscribe && (
        <button
          onClick={onUnsubscribe}
          className="flex-shrink-0 text-xs font-semibold text-muted-foreground hover:text-destructive border border-border rounded-full px-3 py-1 self-start"
        >
          {t('Unsubscribe')}
        </button>
      )}
    </div>
  );
}

export default DiscussionThreadListItem;
