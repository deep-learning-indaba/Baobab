import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import Attachments from '../../components/Attachments';
import { buildBodyMarkdown } from '../../utils/attachments';

var MAX_SUBJECT_LEN = 200;

function NewDiscussionThread(props) {
  var event = props.event, history = props.history;
  var spaceId = props.match && props.match.params && props.match.params.spaceId;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;

  var [subject, setSubject] = useState('');
  var [body, setBody] = useState('');
  var [attachments, setAttachments] = useState([]);
  var [posting, setPosting] = useState(false);
  var [error, setError] = useState(null);
  var [spaceName, setSpaceName] = useState(null);

  useEffect(function () {
    if (!eventId || !spaceId) return;
    discussionService.getSpace(eventId, spaceId).then(function (r) {
      if (!r.error) setSpaceName(r.data.name);
    });
  }, [eventId, spaceId]);

  function handlePost() {
    if (!subject.trim() || (!body.trim() && attachments.length === 0) || !eventId || !spaceId) return;
    setPosting(true);
    setError(null);
    discussionService.createThread(eventId, spaceId, subject.trim(), buildBodyMarkdown(body, attachments)).then(function (r) {
      setPosting(false);
      if (r.error) { setError(r.error); return; }
      history.push('/' + eventKey + '/event-app/discussion/' + r.data.thread_id);
    });
  }

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <button
        onClick={function () { history.push('/' + eventKey + '/event-app/discussion/space/' + spaceId); }}
        className="flex items-center gap-1.5 text-sm text-primary hover:underline"
      >
        <i className="fas fa-chevron-left" style={{ fontSize: 13 }} />
        {spaceName ? t('Back to {{space}}', { space: spaceName }) : t('Back to Discussion')}
      </button>

      <h1 className="font-heading text-2xl font-bold text-foreground">{t('New discussion')}</h1>

      <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Subject')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={subject}
            maxLength={MAX_SUBJECT_LEN}
            required
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
          <div className="mt-2">
            <Attachments
              attachments={attachments}
              onChange={setAttachments}
              disabled={posting}
            />
          </div>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end">
          <button
            onClick={handlePost}
            disabled={posting || !subject.trim() || (!body.trim() && attachments.length === 0)}
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
