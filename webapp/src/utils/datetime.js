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
