function urlBase64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  var raw = window.atob(base64);
  var arr = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export function subscribeToPush() {
  var vapidPublic = process.env.REACT_APP_VAPID_PUBLIC_KEY;
  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !vapidPublic) {
    return Promise.resolve({ ok: false, reason: 'unsupported' });
  }
  return navigator.serviceWorker.ready.then(function (reg) {
    return Notification.requestPermission().then(function (perm) {
      if (perm !== 'granted') return { ok: false, reason: 'denied' };
      return reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublic)
      }).then(function (sub) {
        return { ok: true, subscription: sub };
      });
    });
  });
}
