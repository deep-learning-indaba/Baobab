import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { profileService } from '../services/eventApp/profile.service';

const CONSENT_TYPE = 'longitudinal_use';
const CONSENT_VERSION = '2026-01';
const STORAGE_KEY = 'consent_dismissed_' + CONSENT_VERSION;

function ConsentGate(props) {
  const event = props.event;
  const { t } = useTranslation();

  const [show, setShow] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const eventId = event && event.id;

  useEffect(function() {
    if (!eventId) {
      return;
    }
    const dismissed = sessionStorage.getItem(STORAGE_KEY);
    if (dismissed) {
      return;
    }
    profileService.getConsent(eventId).then(function(result) {
      if (result.error) {
        return;
      }
      const rows = result.data || [];
      const latest = rows.find(function(r) { return r.consent_type === CONSENT_TYPE; });
      if (!latest || latest.consent_version !== CONSENT_VERSION) {
        setShow(true);
      }
    });
  }, [eventId]);

  function handleDecision(granted) {
    setSubmitting(true);
    profileService.setConsent({
      event_id: eventId,
      consent_type: CONSENT_TYPE,
      granted: granted,
    }).then(function() {
      setSubmitting(false);
      setShow(false);
      sessionStorage.setItem(STORAGE_KEY, '1');
    });
  }

  function handleDismiss() {
    setShow(false);
    sessionStorage.setItem(STORAGE_KEY, '1');
  }

  if (!show) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4">
        <h2 className="text-lg font-bold text-foreground">{t('Data consent')}</h2>
        <p className="text-sm text-foreground/80">
          {t('We use event data to improve the community. Your participation data may be used for longitudinal analysis to understand the impact of the programme. You can change this at any time in your profile.')}
        </p>
        <div className="flex gap-3">
          <button
            className="flex-1 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
            onClick={function() { handleDecision(true); }}
            disabled={submitting}
          >
            {t('Agree')}
          </button>
          <button
            className="flex-1 px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
            onClick={function() { handleDecision(false); }}
            disabled={submitting}
          >
            {t('Not now')}
          </button>
        </div>
        <button
          className="w-full text-xs text-foreground/40 hover:text-foreground/70"
          onClick={handleDismiss}
        >
          {t('Dismiss')}
        </button>
      </div>
    </div>
  );
}

export default ConsentGate;
