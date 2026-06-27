import React, { createContext, useContext, useState, useEffect } from 'react';

const DISMISSED_KEY = 'pwa-install-dismissed';
const CONSENT_COOKIE = 'baobab-cookie-consent';

function hasCookieConsent() {
  return document.cookie.split(';').some(c => c.trim().startsWith(CONSENT_COOKIE + '='));
}

const InstallContext = createContext(null);

export function InstallProvider({ children }) {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isIOS, setIsIOS] = useState(false);
  const [installed, setInstalled] = useState(false);
  const [dismissed, setDismissed] = useState(() => !!localStorage.getItem(DISMISSED_KEY));
  const [consentGiven, setConsentGiven] = useState(hasCookieConsent);

  useEffect(() => {
    const isStandalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true;
    if (isStandalone) { setInstalled(true); return; }

    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const safari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
    if (ios && safari) { setIsIOS(true); return; }

    const onPrompt = e => { e.preventDefault(); setDeferredPrompt(e); };
    const onInstalled = () => setInstalled(true);
    window.addEventListener('beforeinstallprompt', onPrompt);
    window.addEventListener('appinstalled', onInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  useEffect(() => {
    if (consentGiven) return;
    const id = setInterval(() => { if (hasCookieConsent()) setConsentGiven(true); }, 500);
    return () => clearInterval(id);
  }, [consentGiven]);

  const install = async () => {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    if (outcome === 'accepted') setInstalled(true);
    return outcome === 'accepted';
  };

  const dismiss = () => {
    localStorage.setItem(DISMISSED_KEY, '1');
    setDismissed(true);
  };

  const promptReady = isIOS || !!deferredPrompt;

  return (
    <InstallContext.Provider value={{
      // Show the full banner: consent given, not dismissed, not installed, prompt available
      bannerVisible: !installed && !dismissed && consentGiven && promptReady,
      // Show the subtle link: dismissed (or banner already shown), not installed, prompt available
      linkVisible: !installed && dismissed && promptReady,
      isIOS,
      install,
      dismiss,
    }}>
      {children}
    </InstallContext.Provider>
  );
}

export function useInstall() {
  return useContext(InstallContext);
}
