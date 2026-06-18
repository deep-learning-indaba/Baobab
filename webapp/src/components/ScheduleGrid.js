import React from 'react';
import { formatTimeInEventTz } from '../utils/datetime';

var PX_PER_MIN = 2.5; // 150px per hour

function timeToLocalMinutes(utcIso, timezone) {
  var formatted = formatTimeInEventTz(utcIso, timezone || 'UTC');
  if (!formatted || formatted.indexOf(':') === -1) return 0;
  var parts = formatted.split(':');
  return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
}

// Assigns each session a column index and a totalCols count so overlapping
// sessions can be rendered side by side with correct widths.
function layoutSessions(sessions) {
  var sorted = sessions.slice().sort(function(a, b) {
    return (a.start_time || '') < (b.start_time || '') ? -1 : 1;
  });

  var columnEnds = []; // end_time of the last session placed in each column
  var assignments = sorted.map(function(s) {
    var col = -1;
    for (var c = 0; c < columnEnds.length; c++) {
      if (columnEnds[c] <= (s.start_time || '')) {
        col = c;
        break;
      }
    }
    if (col === -1) {
      col = columnEnds.length;
      columnEnds.push('');
    }
    columnEnds[col] = s.end_time || '';
    return { session: s, col: col };
  });

  // totalCols for a session = highest column index among all sessions that
  // overlap with it, plus one.
  return assignments.map(function(a) {
    var maxCol = a.col;
    assignments.forEach(function(b) {
      var overlaps = (b.session.start_time || '') < (a.session.end_time || '')
        && (b.session.end_time || '') > (a.session.start_time || '');
      if (overlaps && b.col > maxCol) maxCol = b.col;
    });
    return { session: a.session, col: a.col, totalCols: maxCol + 1 };
  });
}

// Props:
//   sessions   – array of session objects with start_time / end_time (UTC ISO)
//   timezone   – IANA timezone string
//   renderCard – function(session) → React element; the element will be
//                stretched to fill the block's height via CSS
export default function ScheduleGrid(props) {
  var sessions = props.sessions;
  var timezone = props.timezone || 'UTC';
  var renderCard = props.renderCard;

  if (!sessions || sessions.length === 0) return null;

  var startMins = sessions.map(function(s) { return timeToLocalMinutes(s.start_time, timezone); });
  var endMins   = sessions.map(function(s) { return timeToLocalMinutes(s.end_time,   timezone); });
  var minMin = Math.floor(Math.min.apply(null, startMins) / 60) * 60;
  var maxMin = Math.ceil(Math.max.apply(null, endMins)   / 60) * 60;
  if (maxMin <= minMin) maxMin = minMin + 60;

  var totalHeight = (maxMin - minMin) * PX_PER_MIN;

  var hours = [];
  for (var h = minMin / 60; h <= maxMin / 60; h++) hours.push(h);

  var layout = layoutSessions(sessions);

  return (
    <div className="flex">
      {/* Time axis */}
      <div className="flex-shrink-0 relative" style={{ width: 52, height: totalHeight }}>
        {hours.map(function(h) {
          var top = (h * 60 - minMin) * PX_PER_MIN;
          return (
            <div
              key={h}
              className="absolute right-2 text-[11px] text-muted-foreground tabular-nums leading-none"
              style={{ top: top, transform: 'translateY(-50%)' }}
            >
              {String(h).padStart(2, '0')}:00
            </div>
          );
        })}
      </div>

      {/* Grid */}
      <div className="relative flex-1 border-l border-border/50" style={{ height: totalHeight }}>
        {/* Hour lines */}
        {hours.map(function(h) {
          var top = (h * 60 - minMin) * PX_PER_MIN;
          return (
            <div
              key={'line-' + h}
              className="absolute left-0 right-0 border-t border-border/30"
              style={{ top: top }}
            />
          );
        })}

        {/* Session blocks */}
        {layout.map(function(item) {
          var startMin = timeToLocalMinutes(item.session.start_time, timezone);
          var endMin   = timeToLocalMinutes(item.session.end_time,   timezone);
          var top    = (startMin - minMin) * PX_PER_MIN;
          var height = Math.max((endMin - startMin) * PX_PER_MIN, 24);
          var leftPct  = (item.col / item.totalCols * 100) + '%';
          var widthPct = (100 / item.totalCols) + '%';

          return (
            <div
              key={item.session.id}
              className="absolute"
              style={{ top: top, left: leftPct, width: widthPct, height: height, padding: '2px 3px' }}
            >
              {renderCard(item.session)}
            </div>
          );
        })}
      </div>
    </div>
  );
}
