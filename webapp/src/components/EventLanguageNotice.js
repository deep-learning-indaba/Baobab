import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getEventLanguages, isEventInLanguage } from '../utils/eventLanguages';
import { changeSiteLanguage } from '../utils/siteLanguage';

function dismissKey(event, uiLanguage) {
  return `eventLanguageNotice:${event.id}:${uiLanguage}`;
}

function isDismissed(key) {
  try {
    return localStorage.getItem(key) === '1';
  } catch (e) {
    return false;
  }
}

// Tells a viewer that the event's content is not available in their site
// language and will be shown in the event's primary language instead.
const EventLanguageNotice = ({ event, organisation }) => {
  const { t, i18n } = useTranslation();
  const uiLanguage = (i18n.language || '').slice(0, 2);
  const key = event ? dismissKey(event, uiLanguage) : null;
  const [dismissed, setDismissed] = useState(() => (key ? isDismissed(key) : true));

  if (!event || dismissed || isEventInLanguage(event, uiLanguage, organisation)) {
    return null;
  }

  const languages = getEventLanguages(event, organisation);
  const primary = languages[0];
  const languageList = languages.map((l) => t(l.description)).join(', ');
  // The organisation must offer the language for the site to be switched to it.
  const canSwitch = !!(organisation && organisation.languages
    && organisation.languages.some((l) => l.code === primary.code));

  const dismiss = () => {
    try {
      localStorage.setItem(key, '1');
    } catch (e) {
      // Storage can be unavailable (private mode); dismissing still works for this view.
    }
    setDismissed(true);
  };

  return (
    <div
      role="status"
      className="mb-6 flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl border border-action/20 bg-action/5 px-4 py-3 text-sm text-foreground"
    >
      <i className="fas fa-globe text-action shrink-0" aria-hidden="true" />
      <p className="flex-1 min-w-0">
        {languages.length > 1
          ? t('This event is only available in {{languages}}. Its content is shown in {{language}}.', {
            languages: languageList,
            language: t(primary.description),
          })
          : t('This event is only available in {{language}}.', { language: t(primary.description) })}
      </p>
      <div className="flex items-center gap-2 shrink-0">
        {canSwitch && (
          <button
            type="button"
            className="rounded-lg bg-white border border-border px-3 py-1.5 font-medium text-foreground hover:bg-surface-low transition-colors"
            onClick={() => changeSiteLanguage(primary.code)}
          >
            {t('Switch site to {{language}}', { language: t(primary.description) })}
          </button>
        )}
        <button
          type="button"
          className="rounded-lg p-1.5 text-foreground/60 hover:bg-surface-high hover:text-foreground transition-colors"
          onClick={dismiss}
          aria-label={t('Dismiss')}
        >
          <i className="fas fa-times" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};

export default EventLanguageNotice;
