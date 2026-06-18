export function formatInEventTz(utcIso, timezone, options) {
  if (!utcIso) return '';
  var date = (utcIso instanceof Date) ? utcIso : new Date(utcIso);
  var opts = Object.assign(
    { timeZone: timezone || 'UTC', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
    options || {}
  );
  return new Intl.DateTimeFormat(undefined, opts).format(date);
}

export function eventLocalDateKey(utcIso, timezone) {
  if (!utcIso) return '';
  var date = new Date(utcIso);
  return new Intl.DateTimeFormat('en-CA', { timeZone: timezone || 'UTC', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}

// Given event-local wall-clock date (YYYY-MM-DD) and time (HH:mm) in the given
// IANA timezone, return the matching UTC ISO-8601 instant.
// e.g. eventLocalToUtcIso('2026-08-02', '09:00', 'Africa/Lagos') -> '2026-08-02T08:00:00.000Z'
export function eventLocalToUtcIso(dateStr, timeStr, timezone) {
  if (!dateStr || !timeStr) return '';
  var tzName = timezone || 'UTC';
  // Treat the inputs as if they were UTC to get a provisional Date
  var provisional = new Date(dateStr + 'T' + timeStr + ':00Z');
  // Ask Intl what wall-clock components that provisional instant shows in tzName
  var dtf = new Intl.DateTimeFormat('en-US', {
    timeZone: tzName,
    hour12: false,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
  var parts = dtf.formatToParts(provisional).reduce(function(acc, p) {
    acc[p.type] = p.value;
    return acc;
  }, {});
  // Build the UTC ms that corresponds to that wall-clock time in tzName
  var asTzMs = Date.UTC(
    Number(parts.year),
    Number(parts.month) - 1,
    Number(parts.day),
    Number(parts.hour),
    Number(parts.minute),
    Number(parts.second)
  );
  // offset = how far ahead of UTC tzName is at that instant
  var offset = asTzMs - provisional.getTime();
  return new Date(provisional.getTime() - offset).toISOString();
}

// Format a UTC ISO string for display in event-local time, showing only time (HH:mm)
export function formatTimeInEventTz(utcIso, timezone) {
  if (!utcIso) return '';
  var date = new Date(utcIso);
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: timezone || 'UTC',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date);
}

// Return YYYY-MM-DD in event timezone from a UTC ISO string
export function utcToEventLocalDate(utcIso, timezone) {
  return eventLocalDateKey(utcIso, timezone);
}

// Return HH:mm in event timezone from a UTC ISO string
export function utcToEventLocalTime(utcIso, timezone) {
  if (!utcIso) return '';
  var date = new Date(utcIso);
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: timezone || 'UTC',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date);
}
