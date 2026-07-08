import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  isPushSupported,
  getNotificationPermission,
  registerPushSubscription,
} from '../utils/push';
import { announcementService } from '../services/eventApp/announcement.service';

var VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY;

// A self-contained control to opt into (or check the status of) push
// notifications. Safe to drop anywhere the user is authenticated — it always
// gives the user a way back even if they dismissed the install banner earlier.
export default function PushNotificationToggle() {
  const { t } = useTranslation();
  const supported = isPushSupported();
  const [permission, setPermission] = useState(getNotificationPermission());
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [testing, setTesting] = useState(false);

  // If already granted, silently make sure the server has our subscription.
  useEffect(() => {
    if (supported && permission === 'granted') {
      registerPushSubscription({ requestPermission: false });
    }
  }, [supported, permission]);

  const enable = useCallback(() => {
    setBusy(true);
    setFeedback(null);
    registerPushSubscription({ requestPermission: true }).then((result) => {
      setPermission(getNotificationPermission());
      setBusy(false);
      if (result.ok) {
        setFeedback({ type: 'success', text: t('Notifications are on.') });
      } else if (result.reason === 'denied') {
        setFeedback({ type: 'error', text: t('Notifications are blocked. Allow notifications for this site in your browser settings, then try again.') });
      } else {
        // Include the reason code so it can be reported if something's off.
        setFeedback({ type: 'error', text: t('Could not enable notifications. Please try again.') + ' (' + (result.reason || 'unknown') + ')' });
      }
    });
  }, [t]);

  // Send a test push to this user's own devices and report what happened.
  const sendTest = useCallback(() => {
    setTesting(true);
    setFeedback(null);
    // Make sure the server has a current subscription before testing.
    registerPushSubscription({ requestPermission: false }).then(() => {
      return announcementService.testPush();
    }).then((res) => {
      setTesting(false);
      const d = res && res.data;
      if (!d) {
        setFeedback({ type: 'error', text: t('Could not reach the server. Please try again.') });
        return;
      }
      // A successful send is the ground truth: it proves the server's private
      // key is correctly paired with this device's subscription. Check it first.
      if (d.sent > 0) {
        setFeedback({ type: 'success', text: t('Test notification sent. It should appear on your device shortly.') });
        return;
      }
      if (!d.vapid_private_key_configured) {
        setFeedback({ type: 'error', text: t('The server is missing its notification key (VAPID_PRIVATE_KEY). Ask an administrator to configure it.') });
        return;
      }
      if (d.subscriptions === 0) {
        setFeedback({ type: 'error', text: t('No subscription is registered for your account on the server. Try turning notifications off and on again.') });
        return;
      }
      // Delivery was attempted but every send failed — surface the server's
      // reason, and add a key-mismatch hint only as a possible cause.
      var norm = function (k) { return (k || '').trim().replace(/=+$/, ''); };
      var detail = (d.errors && d.errors.length) ? ' (' + d.errors[0] + ')' : '';
      var hint = (d.vapid_public_key && VAPID_PUBLIC_KEY && norm(d.vapid_public_key) !== norm(VAPID_PUBLIC_KEY))
        ? ' ' + t('The app and server notification keys may not match.')
        : '';
      setFeedback({ type: 'error', text: t('The server could not deliver the notification.') + detail + hint });
    });
  }, [t]);

  if (!supported) {
    return (
      <div className="bg-white rounded-2xl border border-border p-5">
        <h2 className="text-sm font-semibold text-foreground mb-1">{t('Notifications')}</h2>
        <p className="text-sm text-foreground/60">
          {t('On iPhone, add the app to your home screen first to receive notifications. On other devices, notifications are not supported by this browser.')}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-border p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-foreground mb-1">{t('Notifications')}</h2>
          <p className="text-sm text-foreground/60">
            {t('Get announcements from organisers even when the app is closed.')}
          </p>
        </div>
        {permission === 'granted' ? (
          <span className="shrink-0 inline-flex items-center gap-1.5 text-sm font-medium text-primary">
            <i className="fas fa-check-circle" />
            {t('On')}
          </span>
        ) : (
          <button
            onClick={enable}
            disabled={busy}
            className="shrink-0 px-4 py-2 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all disabled:opacity-60"
          >
            {busy ? t('Enabling...') : t('Enable notifications')}
          </button>
        )}
      </div>
      {permission === 'granted' && (
        <button
          onClick={sendTest}
          disabled={testing}
          className="mt-3 text-sm font-medium text-blue-600 hover:underline disabled:opacity-60"
        >
          {testing ? t('Sending...') : t('Send a test notification')}
        </button>
      )}
      {feedback && (
        <p className={'mt-3 text-sm ' + (feedback.type === 'success' ? 'text-primary' : 'text-red-600')}>
          {feedback.text}
        </p>
      )}
    </div>
  );
}
