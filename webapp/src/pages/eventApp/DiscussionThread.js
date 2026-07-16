import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import { formatInEventTz } from '../../utils/datetime';
import MarkdownRenderer from '../../components/MarkdownRenderer';

function MessageCard(props) {
  var msg = props.msg, t = props.t, timezone = props.timezone;
  var onEdit = props.onEdit, onDelete = props.onDelete, onReport = props.onReport;
  var reported = props.reported;

  var [menuOpen, setMenuOpen] = useState(false);
  var [editing, setEditing] = useState(false);
  var [draft, setDraft] = useState(msg.body_markdown || '');

  if (msg.is_deleted) {
    return (
      <div className="rounded-2xl border border-border bg-muted/20 p-4">
        <p className="text-sm italic text-muted-foreground">
          {msg.deleted_by === 'moderator' ? t('Removed by a moderator') : t('Message deleted by author')}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-white shadow-sm p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-foreground">
            {msg.author.firstname} {msg.author.lastname}
          </p>
          <p className="text-xs text-muted-foreground">
            {formatInEventTz(msg.created_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
            {msg.edited_at && <span className="ml-1.5">· {t('edited')}</span>}
          </p>
        </div>
        {(msg.can_edit || msg.can_delete || !msg.can_edit) && (
          <div className="relative flex-shrink-0">
            <button
              onClick={function () { setMenuOpen(!menuOpen); }}
              className="text-muted-foreground hover:text-foreground px-1"
              aria-label={t('Message actions')}
            >
              <i className="fas fa-ellipsis-h" style={{ fontSize: 14 }} />
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-6 z-10 bg-white border border-border rounded-xl shadow-lg py-1 min-w-[140px]">
                {msg.can_edit && (
                  <button
                    onClick={function () { setEditing(true); setMenuOpen(false); }}
                    className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted/40"
                  >
                    {t('Edit')}
                  </button>
                )}
                {msg.can_delete && (
                  <button
                    onClick={function () {
                      setMenuOpen(false);
                      if (window.confirm(t('Delete this message?'))) onDelete(msg.id);
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-destructive hover:bg-muted/40"
                  >
                    {t('Delete')}
                  </button>
                )}
                {!msg.can_edit && (
                  <button
                    onClick={function () {
                      setMenuOpen(false);
                      if (reported) return;
                      if (window.confirm(t('Report this message?'))) {
                        var reason = window.prompt(t('Reason (optional)')) || '';
                        onReport(msg.id, reason);
                      }
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-muted/40"
                  >
                    {reported ? t('Reported') : t('Report')}
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {editing ? (
        <div className="mt-2 space-y-2">
          <textarea
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            rows={4}
            value={draft}
            onChange={function (e) { setDraft(e.target.value); }}
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={function () { setEditing(false); setDraft(msg.body_markdown || ''); }}
              className="px-3 py-1.5 rounded-lg border border-border text-sm text-foreground hover:bg-muted/50"
            >
              {t('Cancel')}
            </button>
            <button
              onClick={function () {
                if (!draft.trim()) return;
                onEdit(msg.id, draft.trim());
                setEditing(false);
              }}
              className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-container"
            >
              {t('Post')}
            </button>
          </div>
        </div>
      ) : (
        <div className="prose prose-sm max-w-none text-foreground mt-2">
          <MarkdownRenderer source={msg.body_markdown} />
        </div>
      )}
    </div>
  );
}

function DiscussionThread(props) {
  var event = props.event, history = props.history;
  var threadId = props.match && props.match.params && props.match.params.threadId;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;
  var timezone = (event && event.timezone) || 'UTC';

  var [thread, setThread] = useState(null);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);
  var [replyBody, setReplyBody] = useState('');
  var [sending, setSending] = useState(false);
  var [reportedIds, setReportedIds] = useState({});
  var [subToggling, setSubToggling] = useState(false);

  function load() {
    if (!eventId || !threadId) { setLoading(false); return; }
    discussionService.getThread(eventId, threadId).then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setThread(r.data);
    });
  }
  useEffect(load, [eventId, threadId]);

  if (loading) return <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>;
  if (error) return <div className="w-full pt-6 text-center text-destructive">{error}</div>;
  if (!thread) return null;

  function handleReply() {
    if (!replyBody.trim()) return;
    setSending(true);
    discussionService.reply(eventId, threadId, replyBody.trim()).then(function (r) {
      setSending(false);
      if (!r.error) { setReplyBody(''); load(); }
    });
  }

  function handleEdit(messageId, body) {
    discussionService.editMessage(eventId, messageId, body).then(function () { load(); });
  }

  function handleDelete(messageId) {
    discussionService.deleteMessage(eventId, messageId).then(function () { load(); });
  }

  function handleReport(messageId, reason) {
    discussionService.reportMessage(eventId, messageId, reason).then(function (r) {
      if (!r.error) setReportedIds(function (prev) { return Object.assign({}, prev, { [messageId]: true }); });
    });
  }

  function handleSubscriptionToggle() {
    setSubToggling(true);
    discussionService.setSubscription(eventId, threadId, !thread.is_subscribed).then(function (r) {
      setSubToggling(false);
      if (!r.error) setThread(function (prev) { return Object.assign({}, prev, { is_subscribed: r.data.subscribed }); });
    });
  }

  var messages = thread.messages || [];
  var root = messages.length > 0 ? messages[0] : null;
  var replies = messages.slice(1);

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4 pb-8">
      <button
        onClick={function () { history.push('/' + eventKey + '/event-app/discussion/space/' + thread.space_id); }}
        className="flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <i className="fas fa-chevron-left" style={{ fontSize: 13 }} />
        {thread.space_name ? t('Back to {{space}}', { space: thread.space_name }) : t('Back to Discussion')}
      </button>

      <div className="flex items-center justify-between gap-3">
        <h1 className="font-heading text-xl font-bold text-foreground">{thread.subject || t('(no subject)')}</h1>
        <button
          onClick={handleSubscriptionToggle}
          disabled={subToggling}
          className={'flex-shrink-0 text-sm font-semibold px-4 py-2 rounded-full border transition-colors disabled:opacity-50 ' +
            (thread.is_subscribed ? 'bg-primary/10 border-primary text-primary' : 'border-border text-foreground hover:bg-muted/40')}
          title={thread.is_subscribed ? t("You'll be notified of new replies") : ''}
        >
          {thread.is_subscribed ? t('Subscribed') : t('Subscribe')}
        </button>
      </div>

      <div className="space-y-3">
        {root && (
          <MessageCard
            msg={root} t={t} timezone={timezone}
            onEdit={handleEdit} onDelete={handleDelete} onReport={handleReport}
            reported={!!reportedIds[root.id]}
          />
        )}
        {replies.map(function (msg) {
          return (
            <MessageCard
              key={msg.id}
              msg={msg} t={t} timezone={timezone}
              onEdit={handleEdit} onDelete={handleDelete} onReport={handleReport}
              reported={!!reportedIds[msg.id]}
            />
          );
        })}
      </div>

      <div className="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-2">
        <textarea
          className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          rows={3}
          placeholder={t('Write a message...')}
          value={replyBody}
          onChange={function (e) { setReplyBody(e.target.value); }}
        />
        <div className="flex justify-end">
          <button
            onClick={handleReply}
            disabled={sending || !replyBody.trim()}
            className="bg-primary text-primary-foreground text-sm font-semibold px-4 py-2 rounded-full disabled:opacity-50"
          >
            {sending ? t('Sending...') : t('Send')}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DiscussionThread;
