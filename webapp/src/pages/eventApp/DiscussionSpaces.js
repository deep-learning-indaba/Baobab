import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { discussionService } from '../../services/eventApp/discussion.service';
import { isCommsOfficer } from '../../utils/user';
import Modal, { ConfirmModal } from '../../components/Modal';
import DiscussionThreadListItem from './DiscussionThreadListItem';

var TABS = { SPACES: 'spaces', SUBSCRIPTIONS: 'subscriptions' };

function SpaceEditorModal(props) {
  var t = props.t, visible = props.visible, space = props.space;
  var onSave = props.onSave, onClose = props.onClose;

  var [name, setName] = useState('');
  var [description, setDescription] = useState('');
  var [subscribeOnReply, setSubscribeOnReply] = useState(true);
  var [saving, setSaving] = useState(false);

  useEffect(function () {
    setName((space && space.name) || '');
    setDescription((space && space.description) || '');
    setSubscribeOnReply(space ? space.subscribe_on_reply : true);
  }, [space, visible]);

  if (!visible) return null;

  function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    onSave({ name: name.trim(), description: description.trim(), subscribe_on_reply: subscribeOnReply })
      .then(function () { setSaving(false); });
  }

  return (
    <Modal visible={visible} onClickBackdrop={onClose}>
      <h2 className="font-heading text-lg font-bold text-foreground">
        {space ? t('Edit space') : t('New space')}
      </h2>
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">{t('Name')}</label>
        <input
          className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          value={name}
          maxLength={200}
          onChange={function (e) { setName(e.target.value); }}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-foreground mb-1">{t('Description (optional)')}</label>
        <textarea
          className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          rows={3}
          value={description}
          onChange={function (e) { setDescription(e.target.value); }}
        />
      </div>
      <label className="flex items-start gap-2 cursor-pointer">
        <input
          type="checkbox"
          className="mt-0.5"
          checked={subscribeOnReply}
          onChange={function (e) { setSubscribeOnReply(e.target.checked); }}
        />
        <span className="text-sm text-foreground">
          {t('Subscribe members to a thread when they post or reply in this space')}
          <span className="block text-xs text-muted-foreground mt-0.5">
            {t('Members can always change their own subscription on a thread regardless of this setting.')}
          </span>
        </span>
      </label>
      <div className="flex justify-end gap-3 pt-2">
        <button
          onClick={onClose}
          className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/80"
        >
          {t('Cancel')}
        </button>
        <button
          onClick={handleSave}
          disabled={saving || !name.trim()}
          className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {t('Save')}
        </button>
      </div>
    </Modal>
  );
}

function DiscussionSpaces(props) {
  var event = props.event, history = props.history, user = props.user;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;
  var timezone = (event && event.timezone) || 'UTC';
  var isAdmin = isCommsOfficer(user, event);

  var [tab, setTab] = useState(TABS.SPACES);

  var [spaces, setSpaces] = useState([]);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);
  var [editorSpace, setEditorSpace] = useState(undefined); // undefined = closed, null = new, object = editing
  var [deleteTarget, setDeleteTarget] = useState(null);

  var [subscriptions, setSubscriptions] = useState([]);
  var [subsLoading, setSubsLoading] = useState(true);
  var [subsError, setSubsError] = useState(null);

  function load() {
    if (!eventId) { setLoading(false); return; }
    setLoading(true);
    discussionService.listSpaces(eventId).then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setSpaces(r.data || []);
    });
  }
  useEffect(load, [eventId]);

  function loadSubscriptions() {
    if (!eventId) { setSubsLoading(false); return; }
    setSubsLoading(true);
    discussionService.listSubscriptions(eventId).then(function (r) {
      setSubsLoading(false);
      if (r.error) setSubsError(r.error); else setSubscriptions(r.data || []);
    });
  }
  useEffect(function () {
    if (tab === TABS.SUBSCRIPTIONS) loadSubscriptions();
  }, [eventId, tab]);

  function handleSave(fields) {
    var request = editorSpace
      ? discussionService.updateSpace(eventId, editorSpace.id, fields)
      : discussionService.createSpace(eventId, fields.name, fields.description, fields.subscribe_on_reply);
    return request.then(function (r) {
      if (!r.error) { setEditorSpace(undefined); load(); }
    });
  }

  function handleDelete() {
    var space = deleteTarget;
    setDeleteTarget(null);
    discussionService.deleteSpace(eventId, space.id).then(function (r) {
      if (!r.error) load();
    });
  }

  function handleUnsubscribe(threadId) {
    discussionService.setSubscription(eventId, threadId, false).then(function (r) {
      if (!r.error) loadSubscriptions();
    });
  }

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold text-foreground">{t('Discussion')}</h1>
        {tab === TABS.SPACES && isAdmin && (
          <button
            onClick={function () { setEditorSpace(null); }}
            className="bg-primary text-primary-foreground text-sm font-semibold px-4 py-2 rounded-full"
          >
            {t('New space')}
          </button>
        )}
      </div>

      <div className="flex gap-2 border-b border-border">
        {[TABS.SPACES, TABS.SUBSCRIPTIONS].map(function (tb) {
          var label = tb === TABS.SPACES ? t('Spaces') : t('My subscriptions');
          return (
            <button
              key={tb}
              onClick={function () { setTab(tb); }}
              className={'pb-2 px-1 text-sm font-medium border-b-2 transition-colors ' + (tab === tb ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground')}
            >
              {label}
            </button>
          );
        })}
      </div>

      {tab === TABS.SPACES && (
        <React.Fragment>
          {loading && <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>}
          {!loading && error && <div className="w-full pt-6 text-center text-destructive">{error}</div>}

          {!loading && !error && spaces.length === 0 && (
            <p className="text-sm text-muted-foreground py-8 text-center">
              {isAdmin ? t('No spaces yet. Create one to get started.') : t('Discussion has not been set up for this event yet.')}
            </p>
          )}

          {!loading && !error && (
            <div className="space-y-3">
              {spaces.map(function (space) {
                return (
                  <div key={space.id}
                    className="w-full rounded-2xl border shadow-sm p-4 transition-all bg-white border-border hover:border-border/80 flex items-start gap-3">
                    <button
                      onClick={function () { history.push('/' + eventKey + '/event-app/discussion/space/' + space.id); }}
                      className="flex-1 min-w-0 text-left"
                    >
                      <div className="flex items-center gap-2">
                        {space.has_unread && <span className="w-2.5 h-2.5 rounded-full bg-primary flex-shrink-0" />}
                        <p className="text-sm font-bold text-foreground truncate">{space.name}</p>
                        {space.is_archived && (
                          <span className="text-xs font-semibold text-muted-foreground bg-muted/40 px-2 py-0.5 rounded-full">
                            {t('Archived')}
                          </span>
                        )}
                      </div>
                      {space.description && (
                        <p className="text-sm text-foreground/60 mt-1 line-clamp-2">{space.description}</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        {t('{{count}} threads', { count: space.thread_count })}
                      </p>
                    </button>
                    {isAdmin && (
                      <div className="flex-shrink-0 flex gap-2">
                        <button
                          onClick={function () { setEditorSpace(space); }}
                          className="text-sm text-primary hover:underline px-1"
                        >
                          {t('Edit')}
                        </button>
                        <button
                          onClick={function () { setDeleteTarget(space); }}
                          className="text-sm text-destructive hover:underline px-1"
                        >
                          {t('Delete')}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </React.Fragment>
      )}

      {tab === TABS.SUBSCRIPTIONS && (
        <React.Fragment>
          {subsLoading && <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>}
          {!subsLoading && subsError && <div className="w-full pt-6 text-center text-destructive">{subsError}</div>}

          {!subsLoading && !subsError && subscriptions.length === 0 && (
            <p className="text-sm text-muted-foreground py-8 text-center">{t("You're not subscribed to any discussions yet.")}</p>
          )}

          {!subsLoading && !subsError && (
            <div className="space-y-3">
              {subscriptions.map(function (th) {
                return (
                  <DiscussionThreadListItem
                    key={th.id}
                    thread={th} t={t} timezone={timezone}
                    spaceName={th.space_name}
                    onClick={function () { history.push('/' + eventKey + '/event-app/discussion/' + th.id); }}
                    onUnsubscribe={function () { handleUnsubscribe(th.id); }}
                  />
                );
              })}
            </div>
          )}
        </React.Fragment>
      )}

      <SpaceEditorModal
        t={t}
        visible={editorSpace !== undefined}
        space={editorSpace}
        onSave={handleSave}
        onClose={function () { setEditorSpace(undefined); }}
      />

      <ConfirmModal
        visible={!!deleteTarget}
        onOK={handleDelete}
        onCancel={function () { setDeleteTarget(null); }}
        okText={t('Delete')}
      >
        {deleteTarget && deleteTarget.thread_count > 0
          ? t('This space has existing threads, so it will be archived instead of deleted. It will disappear from this list but existing threads will remain reachable and no new posts will be accepted.')
          : t('Are you sure you want to delete this space?')}
      </ConfirmModal>
    </div>
  );
}

export default DiscussionSpaces;
