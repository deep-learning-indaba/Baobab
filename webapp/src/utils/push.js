import { announcementService } from '../services/eventApp/announcement.service';

var VAPID_PUBLIC_KEY = process.env.REACT_APP_VAPID_PUBLIC_KEY;

function urlBase64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  var raw = window.atob(base64);
  var arr = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

// True if this browser/device can do Web Push and we have a VAPID key to use.
export function isPushSupported() {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window &&
    !!VAPID_PUBLIC_KEY
  );
}

// 'granted' | 'denied' | 'default' | 'unsupported'
export function getNotificationPermission() {
  if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported';
  return Notification.permission;
}

// Does an existing subscription use the VAPID key we're configured with?
// A mismatch (e.g. the server key was rotated) makes the subscription undeliverable.
function keyMatches(subscription, expectedKey) {
  try {
    var existing = subscription.options && subscription.options.applicationServerKey;
    if (!existing) return false;
    var actual = new Uint8Array(existing);
    if (actual.length !== expectedKey.length) return false;
    for (var i = 0; i < actual.length; i++) {
      if (actual[i] !== expectedKey[i]) return false;
    }
    return true;
  } catch (e) {
    return false;
  }
}

// Ensure a browser push subscription exists. Idempotent and safe to call repeatedly.
//
// options.requestPermission: when true, may show the OS permission prompt — so
// this MUST be called from a user gesture (a click/tap). When false, we only
// proceed if permission was already granted, and never prompt.
//
// Resolves to { ok, reason, subscription }. `reason` is one of:
//   'unsupported' | 'no-service-worker' | 'default' | 'denied' | 'subscribe-failed'
export function ensurePushSubscription(options) {
  var opts = options || {};
  if (!isPushSupported()) return Promise.resolve({ ok: false, reason: 'unsupported' });

  return navigator.serviceWorker.ready
    .catch(function () { return null; })
    .then(function (reg) {
      if (!reg) return { ok: false, reason: 'no-service-worker' };

      var permission = Notification.permission;
      var permissionPromise;
      if (permission === 'granted') {
        permissionPromise = Promise.resolve('granted');
      } else if (permission === 'default' && opts.requestPermission) {
        permissionPromise = Notification.requestPermission().catch(function () { return 'default'; });
      } else {
        // 'denied', or 'default' without an explicit request — don't prompt.
        return { ok: false, reason: permission };
      }

      return permissionPromise.then(function (perm) {
        if (perm !== 'granted') return { ok: false, reason: perm };

        var appServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
        return reg.pushManager.getSubscription().then(function (existing) {
          if (existing && !keyMatches(existing, appServerKey)) {
            // Stale subscription from a previous VAPID key — drop it and re-subscribe.
            return existing.unsubscribe()
              .catch(function () {})
              .then(function () { return null; });
          }
          return existing;
        }).then(function (existing) {
          if (existing) return existing;
          return reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: appServerKey,
          });
        }).then(function (sub) {
          return { ok: true, subscription: sub };
        }).catch(function (e) {
          return { ok: false, reason: 'subscribe-failed', error: e };
        });
      });
    });
}

// Ensure a subscription exists AND is synced to the backend. Safe to call on
// every authenticated load — the backend upserts on endpoint, so repeats are
// harmless. Pass { requestPermission: true } only from a user gesture.
export function registerPushSubscription(options) {
  return ensurePushSubscription(options).then(function (result) {
    if (!result.ok) {
      // 'default'/'unsupported' are normal (user hasn't opted in / can't) — stay quiet.
      if (result.reason !== 'default' && result.reason !== 'unsupported') {
        console.warn('[push] not registered:', result.reason, result.error || '');
      }
      return result;
    }
    return announcementService.subscribePush(result.subscription).then(function (resp) {
      if (resp && resp.error) {
        console.warn('[push] failed to sync subscription to server:', resp.error);
        return { ok: false, reason: 'server-error', error: resp.error, subscription: result.subscription };
      }
      return { ok: true, subscription: result.subscription };
    });
  });
}
