import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';

var MAX_SUBJECT_LEN = 200;

function NewDiscussionThread(props) {
  var event = props.event, history = props.history;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;

  var [subject, setSubject] = useState('');
  var [body, setBody] = useState('');
  var [posting, setPosting] = useState(false);
  var [error, setError] = useState(null);

  function handlePost() {
    if (!body.trim() || !eventId) return;
    setPosting(true);
    setError(null);
    discussionService.createThread(eventId, subject.trim(), body.trim()).then(function (r) {
      setPosting(false);
      if (r.error) { setError(r.error); return; }
      history.push('/' + eventKey + '/event-app/discussion/' + r.data.thread_id);
    });
  }

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <button
        onClick={function () { history.push('/' + eventKey + '/event-app/discussion'); }}
        className="flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <i className="fas fa-chevron-left" style={{ fontSize: 13 }} />
        {t('Back to Discussion')}
      </button>

      <h1 className="font-heading text-2xl font-bold text-foreground">{t('New discussion')}</h1>

      <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Subject (optional)')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={subject}
            maxLength={MAX_SUBJECT_LEN}
            onChange={function (e) { setSubject(e.target.value); }}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Write a message...')}</label>
          <textarea
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            rows={6}
            value={body}
            onChange={function (e) { setBody(e.target.value); }}
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end">
          <button
            onClick={handlePost}
            disabled={posting || !body.trim()}
            className="bg-primary text-primary-foreground text-sm font-semibold px-5 py-2 rounded-full disabled:opacity-50"
          >
            {posting ? t('Sending...') : t('Post')}
          </button>
        </div>
      </div>
    </div>
  );
}

export default NewDiscussionThread;
