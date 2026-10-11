// Where an edit applies: one event, or (no event) the whole organisation.
export function emailScope(event) {
  return event ? { eventId: event.id } : {};
}

export function emailSettingsPath(event) {
  return event ? `/${event.key}/emailTemplates` : '/emailSettings';
}

const SOURCE_LABELS = {
  event: 'event',
  organisation: 'organisation',
  default: 'standard',
};

// Not translated here: callers pass the result through t().
export function sourceLabel(source) {
  return SOURCE_LABELS[source] || 'standard';
}
