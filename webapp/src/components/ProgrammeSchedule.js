import React, { useState, useRef } from 'react';
import { formatTimeInEventTz } from '../utils/datetime';

// ── Time helpers ──────────────────────────────────────────────────────────────

function timeToLocalMinutes(utcIso, timezone) {
  var formatted = formatTimeInEventTz(utcIso, timezone || 'UTC');
  if (!formatted || formatted.indexOf(':') === -1) return 0;
  var parts = formatted.split(':');
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
}

// Group sessions into rows keyed by their local start time so concurrent
// (parallel) sessions land in the same row.
function groupByStartTime(sessions, timezone) {
  var groups = {};
  var order = [];
  sessions.forEach(function(s) {
    var key = timeToLocalMinutes(s.start_time, timezone);
    if (!groups[key]) {
      groups[key] = [];
      order.push(key);
    }
    groups[key].push(s);
  });
  order.sort(function(a, b) { return a - b; });
  return order.map(function(k) {
    // Keep a stable, readable order inside a row (by end time, then title).
    var rowSessions = groups[k].slice().sort(function(a, b) {
      if ((a.end_time || '') !== (b.end_time || '')) {
        return (a.end_time || '') < (b.end_time || '') ? -1 : 1;
      }
      return (a.title || '') < (b.title || '') ? -1 : 1;
    });
    return { startMin: k, sessions: rowSessions };
  });
}

// ── Speaker list ──────────────────────────────────────────────────────────────

function SpeakerList(props) {
  var speakers = props.session.speakers || [];
  if (speakers.length === 0) return null;
  var eventKey = props.eventKey;
  var linkSpeakers = props.linkSpeakers;

  return React.createElement('div', {
    className: 'flex items-start gap-1.5 text-xs text-muted-foreground min-w-0'
  },
    React.createElement('i', { className: 'fas fa-user-friends mt-0.5 flex-none', style: { fontSize: 11 } }),
    React.createElement('div', {
      className: (props.expanded ? 'flex flex-wrap gap-x-2 gap-y-0.5' : 'truncate') + ' min-w-0'
    },
      speakers.map(function(spk, i) {
        var sep = i < speakers.length - 1 ? (props.expanded ? '' : ', ') : '';
        if (linkSpeakers && spk.linked_user_id) {
          return React.createElement(React.Fragment, { key: spk.id },
            React.createElement('a', {
              href: '/' + eventKey + '/app/profile/' + spk.linked_user_id,
              className: 'text-primary font-medium hover:underline'
            }, spk.name),
            sep
          );
        }
        return React.createElement(React.Fragment, { key: spk.id },
          React.createElement('span', { className: 'text-foreground/70' }, spk.name),
          sep
        );
      })
    )
  );
}

// ── Session card (shared by viewer + editor) ──────────────────────────────────

function SessionCard(props) {
  var session = props.session;
  var timezone = props.timezone;
  var t = props.t;
  var compact = props.compact;
  var expandedState = useState(false);
  var expanded = expandedState[0];
  var setExpanded = expandedState[1];

  var startFmt = formatTimeInEventTz(session.start_time, timezone);
  var endFmt = formatTimeInEventTz(session.end_time, timezone);
  var title = session.title || t('Untitled Session');

  var speakerCount = (session.speakers || []).length;
  var titleLong = title.length > 42;
  var hasExtra = !!session.description || titleLong || speakerCount > 0;

  return React.createElement('div', {
    // text-left guards against the app-wide `.container-fluid { text-align:center }`
    className: 'text-left bg-white rounded-xl border border-border shadow-sm overflow-hidden flex flex-col h-full'
  },
    React.createElement('div', { className: 'h-1 bg-primary flex-none' }),
    React.createElement('div', { className: 'p-3 flex flex-col gap-1.5 flex-1 min-w-0' },

      // Top row: badges + optional actions
      React.createElement('div', { className: 'flex items-start justify-between gap-2' },
        React.createElement('div', { className: 'flex flex-wrap items-center gap-1.5 min-w-0' },
          React.createElement('span', { className: 'text-xs font-semibold text-primary whitespace-nowrap tabular-nums' },
            startFmt + ' – ' + endFmt
          ),
          session.session_type && React.createElement('span', {
            className: 'bg-primary/10 text-primary text-xs px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap'
          }, session.session_type.name),
          (session.tracks || []).map(function(track) {
            return React.createElement('span', {
              key: track.id,
              className: 'bg-muted text-muted-foreground text-xs px-1.5 py-0.5 rounded-full whitespace-nowrap'
            }, track.name);
          })
        ),
        props.actions && React.createElement('div', { className: 'flex-none flex gap-1 -mr-1 -mt-1' },
          props.actions
        )
      ),

      // Title — clamped when collapsed, full title available on hover + on expand.
      // Rendered as a div (not h3) so the global heading font-size does not win
      // over these Tailwind text-size utilities in the cascade.
      React.createElement('div', {
        title: title,
        className: 'font-heading font-semibold text-foreground leading-snug ' +
          (compact ? 'text-sm ' : 'text-[15px] ') +
          (expanded ? '' : 'line-clamp-2')
      }, title),

      // Venue
      session.venue && React.createElement('div', {
        className: 'flex items-center gap-1 text-xs text-muted-foreground min-w-0'
      },
        React.createElement('i', { className: 'fas fa-map-marker-alt flex-none', style: { fontSize: 11 } }),
        React.createElement('span', { className: 'truncate' }, session.venue)
      ),

      // Speakers
      speakerCount > 0 && React.createElement(SpeakerList, {
        session: session,
        eventKey: props.eventKey,
        linkSpeakers: props.linkSpeakers,
        expanded: expanded
      }),

      // Description — only when expanded
      expanded && session.description && React.createElement('p', {
        className: 'text-xs text-muted-foreground whitespace-pre-line leading-relaxed'
      }, session.description),

      // Details toggle
      hasExtra && React.createElement('button', {
        type: 'button',
        onClick: function() { setExpanded(!expanded); },
        className: 'mt-auto pt-1 self-start flex items-center gap-1 text-xs font-medium text-primary hover:underline'
      },
        expanded ? t('Hide details') : t('Details'),
        React.createElement('i', {
          className: 'fas ' + (expanded ? 'fa-chevron-up' : 'fa-chevron-down'),
          style: { fontSize: 10 }
        })
      )
    )
  );
}

// ── Parallel sessions (horizontally scrollable track) ─────────────────────────

function ParallelSessions(props) {
  var t = props.t;
  var scrollerRef = useRef(null);

  function scroll(dir) {
    var el = scrollerRef.current;
    if (!el) return;
    el.scrollBy({ left: dir * Math.round(el.clientWidth * 0.8), behavior: 'smooth' });
  }

  return React.createElement('div', null,
    // Header row with label + desktop scroll controls
    React.createElement('div', { className: 'flex items-center justify-between mb-1.5' },
      React.createElement('span', { className: 'text-xs font-semibold uppercase tracking-wide text-muted-foreground' },
        t('Parallel Sessions'),
        React.createElement('span', { className: 'ml-1.5 text-muted-foreground/70 normal-case tracking-normal' },
          '· ' + props.sessions.length
        )
      ),
      React.createElement('div', { className: 'hidden md:flex items-center gap-1' },
        React.createElement('button', {
          type: 'button',
          onClick: function() { scroll(-1); },
          'aria-label': t('Scroll left'),
          className: 'w-7 h-7 rounded-full border border-border bg-white text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors flex items-center justify-center'
        }, React.createElement('i', { className: 'fas fa-chevron-left', style: { fontSize: 11 } })),
        React.createElement('button', {
          type: 'button',
          onClick: function() { scroll(1); },
          'aria-label': t('Scroll right'),
          className: 'w-7 h-7 rounded-full border border-border bg-white text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors flex items-center justify-center'
        }, React.createElement('i', { className: 'fas fa-chevron-right', style: { fontSize: 11 } }))
      )
    ),

    // Scroller + right-edge fade affordance
    React.createElement('div', { className: 'relative' },
      React.createElement('div', {
        ref: scrollerRef,
        className: 'flex gap-3 overflow-x-auto snap-x snap-mandatory pb-2 scroll-smooth hide-scrollbar'
      },
        props.sessions.map(function(session) {
          return React.createElement('div', {
            key: session.id,
            // 2 visible on mobile, 5 on desktop — with a peek of the next card
            className: 'snap-start flex-none w-[44%] md:w-[18.5%]'
          },
            React.createElement(SessionCard, {
              session: session,
              timezone: props.timezone,
              t: t,
              eventKey: props.eventKey,
              linkSpeakers: props.linkSpeakers,
              actions: props.renderActions ? props.renderActions(session) : null,
              compact: true
            })
          );
        })
      ),
      React.createElement('div', {
        'aria-hidden': true,
        className: 'pointer-events-none absolute top-0 bottom-2 right-0 w-10 bg-gradient-to-l from-background to-transparent'
      })
    )
  );
}

// ── Time-slot row ─────────────────────────────────────────────────────────────

function ScheduleRow(props) {
  var row = props.row;
  var timezone = props.timezone;
  var t = props.t;
  var startLabel = formatTimeInEventTz(row.sessions[0].start_time, timezone);
  var isParallel = row.sessions.length > 1;

  return React.createElement('div', { className: 'flex gap-2 md:gap-3' },
    // Time gutter
    React.createElement('div', { className: 'flex-none w-11 md:w-14 text-right pt-2 relative' },
      React.createElement('span', { className: 'text-sm font-semibold text-foreground tabular-nums' }, startLabel)
    ),
    // Timeline + content
    React.createElement('div', { className: 'flex-1 min-w-0 relative border-l-2 border-border/60 pl-3 md:pl-4 pb-5' },
      React.createElement('span', {
        className: 'absolute -left-[5px] top-3 w-2 h-2 rounded-full bg-primary ring-2 ring-background'
      }),
      isParallel
        ? React.createElement(ParallelSessions, {
            sessions: row.sessions,
            timezone: timezone,
            t: t,
            eventKey: props.eventKey,
            linkSpeakers: props.linkSpeakers,
            renderActions: props.renderActions
          })
        : React.createElement(SessionCard, {
            session: row.sessions[0],
            timezone: timezone,
            t: t,
            eventKey: props.eventKey,
            linkSpeakers: props.linkSpeakers,
            actions: props.renderActions ? props.renderActions(row.sessions[0]) : null,
            compact: false
          })
    )
  );
}

// ── Main component ────────────────────────────────────────────────────────────
//
// Props:
//   sessions      – array of session objects (start_time / end_time UTC ISO)
//   timezone      – IANA timezone string
//   t             – i18n translate function
//   eventKey      – event key, used to build speaker profile links (viewer)
//   linkSpeakers  – when true, member speakers link to their profile
//   renderActions – optional function(session) → node, rendered top-right of a
//                   card (used by the editor for edit / delete buttons)
export default function ProgrammeSchedule(props) {
  var sessions = props.sessions || [];
  var timezone = props.timezone || 'UTC';
  if (sessions.length === 0) return null;

  var rows = groupByStartTime(sessions, timezone);

  return React.createElement('div', { className: 'space-y-0.5' },
    rows.map(function(row) {
      return React.createElement(ScheduleRow, {
        key: row.startMin,
        row: row,
        timezone: timezone,
        t: props.t,
        eventKey: props.eventKey,
        linkSpeakers: props.linkSpeakers,
        renderActions: props.renderActions
      });
    })
  );
}
