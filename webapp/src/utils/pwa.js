var deferredPrompt = null;

export function initInstallPrompt() {
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    window.dispatchEvent(new Event('pwa-installable'));
  });
  window.addEventListener('appinstalled', function () {
    deferredPrompt = null;
    if (window.__emitEngagement) window.__emitEngagement('pwa_installed', { platform: navigator.platform });
  });
}

export function canInstall() { return deferredPrompt !== null; }

export function promptInstall() {
  if (deferredPrompt === null) return Promise.resolve('unavailable');
  var p = deferredPrompt;
  deferredPrompt = null;
  p.prompt();
  return p.userChoice.then(function (choice) { return choice.outcome; });
}

export function isIos() {
  return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
}

export function isInStandaloneMode() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}
