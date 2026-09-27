// An event's content is authored in a fixed subset of its organisation's
// languages (event.languages, primary language first). The site's interface
// language is independent: a French-speaking viewer of an English-only event
// keeps a French interface and sees the event's content in English.

const LANGUAGE_NAMES = { en: 'English', fr: 'French' };

// Entries are usually {code, description}, but some organisations store bare codes.
function organisationLanguages(organisation) {
  return ((organisation && organisation.languages) || []).map((l) => (
    typeof l === 'string' ? { code: l, description: LANGUAGE_NAMES[l] || l.toUpperCase() } : l
  ));
}

// The event's languages as [{code, description}], primary first. Falls back to
// the organisation's languages for an event that doesn't carry its own.
export function getEventLanguages(event, organisation) {
  const orgLanguages = organisationLanguages(organisation);
  const codes = event && event.languages && event.languages.length
    ? event.languages
    : orgLanguages.map((l) => l.code);
  return codes.map((code) => {
    const known = orgLanguages.find((l) => l.code === code);
    return { code, description: known ? known.description : (LANGUAGE_NAMES[code] || code.toUpperCase()) };
  });
}

export function languageName(code, organisation) {
  const known = organisationLanguages(organisation).find((l) => l.code === code);
  return known ? known.description : (LANGUAGE_NAMES[code] || (code || '').toUpperCase());
}

// The language to show the event's content in for a viewer whose interface is
// in uiLanguage: uiLanguage when the event supports it, else its primary language.
export function resolveContentLanguage(event, uiLanguage, organisation) {
  const codes = getEventLanguages(event, organisation).map((l) => l.code);
  const requested = (uiLanguage || '').slice(0, 2);
  if (codes.includes(requested)) return requested;
  return codes[0] || requested || 'en';
}

export function isEventInLanguage(event, uiLanguage, organisation) {
  return resolveContentLanguage(event, uiLanguage, organisation) === (uiLanguage || '').slice(0, 2);
}

// Picks from a {languageCode: value} map, preferring `language`, then the given
// fallbacks, then any non-empty value.
export function pickTranslation(map, language, ...fallbacks) {
  if (!map || typeof map !== 'object') return map;
  for (const code of [language, ...fallbacks]) {
    if (code && map[code]) return map[code];
  }
  const any = Object.values(map).find((v) => v);
  return any === undefined ? '' : any;
}
