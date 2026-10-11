import React, { useState, useEffect, useRef } from 'react';
import { REACTION_OPTIONS, REACTION_BY_KEY } from './reactions';

var HOVER_CAPABLE = '(hover: hover) and (pointer: fine)';

function canHover() {
  return typeof window !== 'undefined' && window.matchMedia && window.matchMedia(HOVER_CAPABLE).matches;
}

// Current user first, then everyone else in the order the server sent (oldest first).
function sortedUsers(users) {
  return users.filter(function (u) { return u.is_me; }).concat(users.filter(function (u) { return !u.is_me; }));
}

function MessageReactions(props) {
  var reactions = props.reactions || [], t = props.t, onAdd = props.onAdd, onRemove = props.onRemove;

  var [openEmoji, setOpenEmoji] = useState(null);   // emoji key whose names list is showing
  var [pinned, setPinned] = useState(false);        // opened by click, so hover-out must not close it
  var [pickerOpen, setPickerOpen] = useState(false);
  var [busy, setBusy] = useState(false);
  var rootRef = useRef(null);

  useEffect(function () {
    function handleOutside(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpenEmoji(null);
        setPinned(false);
        setPickerOpen(false);
      }
    }
    function handleKey(e) {
      if (e.key === 'Escape') { setOpenEmoji(null); setPinned(false); setPickerOpen(false); }
    }
    document.addEventListener('mousedown', handleOutside);
    document.addEventListener('keydown', handleKey);
    return function () {
      document.removeEventListener('mousedown', handleOutside);
      document.removeEventListener('keydown', handleKey);
    };
  }, []);

  function run(action) {
    setBusy(true);
    action.then(function () { setBusy(false); });
  }

  function handleAdd(key) {
    setPickerOpen(false);
    setOpenEmoji(null);
    setPinned(false);
    run(onAdd(key));
  }

  function handleRemove(key) {
    setOpenEmoji(null);
    setPinned(false);
    run(onRemove(key));
  }

  var mine = reactions.reduce(function (acc, r) { if (r.reacted_by_me) acc[r.emoji] = true; return acc; }, {});

  return (
    <div ref={rootRef} className="mt-3 flex flex-wrap items-center gap-1.5">
      {reactions.map(function (r) {
        var opt = REACTION_BY_KEY[r.emoji];
        if (!opt) return null;
        var isOpen = openEmoji === r.emoji;
        var label = t(opt.label);
        return (
          <div
            key={r.emoji}
            className="relative"
            onMouseEnter={function () { if (canHover() && !pinned) setOpenEmoji(r.emoji); }}
            onMouseLeave={function () { if (!pinned) setOpenEmoji(null); }}
          >
            <button
              onClick={function () {
                setPickerOpen(false);
                if (isOpen && pinned) { setOpenEmoji(null); setPinned(false); }
                else { setOpenEmoji(r.emoji); setPinned(true); }
              }}
              aria-expanded={isOpen}
              aria-label={t('{{label}}: {{count}}', { label: label, count: r.count }) + (r.reacted_by_me ? ' (' + t('You') + ')' : '')}
              className={'flex items-center gap-1 rounded-full border px-2.5 py-1 text-sm leading-none transition-colors min-h-[32px] ' +
                (r.reacted_by_me ? 'bg-primary/10 border-primary text-primary' : 'border-border text-foreground hover:bg-muted/40')}
            >
              <span aria-hidden="true">{opt.glyph}</span>
              <span className="text-xs font-semibold">{r.count}</span>
            </button>
            {isOpen && (
              <div className="absolute left-0 top-full z-20 pt-1 w-max max-w-[calc(100vw-3rem)]">
                <div className="bg-white border border-border rounded-xl shadow-lg py-2 min-w-[200px] max-w-[260px]">
                  <p className="px-3 pb-1.5 text-xs font-bold text-foreground">
                    <span aria-hidden="true">{opt.glyph}</span> {label}
                  </p>
                  <ul className="max-h-[240px] overflow-y-auto">
                    {sortedUsers(r.users).map(function (u) {
                      return (
                        <li key={u.user_id} className="flex items-center justify-between gap-3 px-3 py-1.5 text-sm text-foreground">
                          <span className="truncate">{u.is_me ? t('You') : u.firstname + ' ' + u.lastname}</span>
                          {u.is_me && (
                            <button
                              onClick={function () { handleRemove(r.emoji); }}
                              disabled={busy}
                              className="flex-shrink-0 text-xs font-semibold text-destructive hover:underline disabled:opacity-50"
                            >
                              {t('Remove')}
                            </button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                  {!r.reacted_by_me && (
                    <div className="px-3 pt-1.5 mt-1 border-t border-border">
                      <button
                        onClick={function () { handleAdd(r.emoji); }}
                        disabled={busy}
                        className="text-xs font-semibold text-primary hover:underline disabled:opacity-50"
                      >
                        {t('React with {{emoji}}', { emoji: opt.glyph })}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}

      <div className="relative">
        <button
          onClick={function () { setOpenEmoji(null); setPinned(false); setPickerOpen(!pickerOpen); }}
          aria-label={t('Add reaction')}
          aria-expanded={pickerOpen}
          title={t('Add reaction')}
          className="flex items-center justify-center rounded-full border border-border text-muted-foreground hover:text-foreground hover:bg-muted/40 min-h-[32px] min-w-[32px] px-2"
        >
          <i className="far fa-smile" style={{ fontSize: 14 }} />
        </button>
        {pickerOpen && (
          <div className="absolute left-0 top-full z-20 pt-1 w-max max-w-[calc(100vw-3rem)]">
            <div className="bg-white border border-border rounded-xl shadow-lg p-2 grid grid-cols-4 sm:grid-cols-8 gap-1">
              {REACTION_OPTIONS.map(function (opt) {
                var used = !!mine[opt.key];
                return (
                  <button
                    key={opt.key}
                    onClick={function () { if (used) setPickerOpen(false); else handleAdd(opt.key); }}
                    disabled={busy}
                    aria-label={t(opt.label)}
                    aria-pressed={used}
                    title={t(opt.label)}
                    className={'rounded-lg text-xl leading-none min-h-[40px] min-w-[40px] hover:bg-muted/50 disabled:opacity-50 ' +
                      (used ? 'bg-primary/10' : '')}
                  >
                    {opt.glyph}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageReactions;
