/* Baobab Event App service worker. Plain JS, no bundling. */
/* global self, caches, clients */
const SHELL_CACHE = 'baobab-shell-v1';
const RUNTIME_CACHE = 'baobab-runtime-v1';
const SHELL_ASSETS = ['/', '/index.html', '/manifest.webmanifest', '/offline.html'];

self.addEventListener('install', function (event) {
  event.waitUntil(caches.open(SHELL_CACHE).then(function (c) { return c.addAll(SHELL_ASSETS); }));
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== SHELL_CACHE && k !== RUNTIME_CACHE; })
            .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

// Network-first for navigations (so deploys are picked up); cache fallback for offline.
// Stale-while-revalidate for whitelisted GET API reads (programme / profile / announcements).
self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  var isNavigation = req.mode === 'navigate';
  var isCacheableApi = /\/api\/v1\/(programme|announcement|profile)/.test(url.pathname);

  if (isNavigation) {
    event.respondWith(
      fetch(req).catch(function () {
        return caches.match(req).then(function (r) { return r || caches.match('/offline.html'); });
      })
    );
    return;
  }
  if (isCacheableApi) {
    event.respondWith(
      caches.open(RUNTIME_CACHE).then(function (cache) {
        return fetch(req)
          .then(function (res) { cache.put(req, res.clone()); return res; })
          .catch(function () { return cache.match(req); });
      })
    );
  }
});

// ---- Web Push ----
self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }
  var title = data.title || 'New announcement';
  var options = {
    body: data.body || '',
    icon: '/favicon/android-icon-192x192.png',
    badge: '/favicon/favicon-96x96.png',
    data: { url: data.url || '/' },
    tag: data.tag || undefined
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if ('focus' in client) { client.navigate(target); return client.focus(); }
      }
      if (self.clients.openWindow) return self.clients.openWindow(target);
    })
  );
});
