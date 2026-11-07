import React, { Component, Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { ErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "react-error-boundary";
import i18nInit from './i18n';
import Loading from "./components/Loading";
import { organisationService } from "./services/organisation/organisation.service";
import ContextProvider from './context/ContextProvider';
import { applyBranding } from './utils/branding';
import { getImage } from './utils/images';

// Retry lazy-loaded chunks to avoid stale-deploy chunk errors
const lazyRetry = function(componentImport) {
  return new Promise((resolve, reject) => {
      const hasRefreshed = JSON.parse(
          window.sessionStorage.getItem('retry-lazy-refreshed') || 'false'
      );
      componentImport().then((component) => {
          window.sessionStorage.setItem('retry-lazy-refreshed', 'false');
          resolve(component);
      }).catch((error) => {
          if (!hasRefreshed) {
              window.sessionStorage.setItem('retry-lazy-refreshed', 'true');
              return window.location.reload();
          }
          reject(error);
      });
  });
};

const App = React.lazy(() => lazyRetry(() => import('./App')));

class Bootstrap extends Component {
  constructor(props) {
    super(props);

    this.state = {
      organisation: null,
      loading: true
    };
  }

  componentDidMount() {
    organisationService.getOrganisation().then(response => {
      this.setState({
        organisation: response.organisation,
        error: response.error,
        loading: false
      });
      if (response.organisation) {
        const org = response.organisation;
        document.title = org.system_name + " | " + org.name;
        i18nInit(org);
        applyBranding(org);
        this._injectOrgManifest(org);
      }
    });
  }

  _injectOrgManifest(org) {
    // A manifest served from a blob: URL has no base to resolve relative URLs
    // against, so every URL in it must be absolute.
    const absolute = path => new URL(path, window.location.origin).href;

    const icon192 = getImage(org.pwa_icon_192);
    const icon512 = getImage(org.pwa_icon_512);
    const icons = [];
    if (icon192) {
      icons.push({ src: absolute(icon192), sizes: '192x192', type: 'image/png', purpose: 'any' });
    }
    if (icon512) {
      icons.push({ src: absolute(icon512), sizes: '512x512', type: 'image/png', purpose: 'any' });
    }
    // Fall back to shared icons if org hasn't configured PWA-specific ones
    if (icons.length === 0) {
      icons.push(
        { src: absolute('/favicon/android-icon-192x192.png'), sizes: '192x192', type: 'image/png', purpose: 'any' },
        { src: absolute('/favicon/icon-512x512.png'), sizes: '512x512', type: 'image/png', purpose: 'any' }
      );
    }

    const manifest = {
      id: absolute('/'),
      name: org.system_name,
      short_name: org.system_name,
      description: 'Your companion app for community events: check-in, programme, networking and announcements.',
      start_url: absolute('/'),
      scope: absolute('/'),
      display: 'standalone',
      orientation: 'portrait',
      background_color: '#ffffff',
      theme_color: org.primary_colour || '#0f172a',
      icons,
    };

    const blob = new Blob([JSON.stringify(manifest)], { type: 'application/manifest+json' });
    const blobUrl = URL.createObjectURL(blob);
    const link = document.querySelector('link[rel="manifest"]');
    if (link) link.href = blobUrl;

    const appleTitle = document.querySelector('meta[name="apple-mobile-web-app-title"]');
    if (appleTitle) appleTitle.content = org.system_name;
  }

  render() {
    if (this.state.loading) {
      return <Loading/>
    }

    return <Suspense fallback={<Loading />}>
      <App organisation={this.state.organisation}/>
    </Suspense>
  }
}

const root = createRoot(document.getElementById("root"));
root.render(
  <ErrorBoundary FallbackComponent={ErrorPage}>
    <ContextProvider>
      <Bootstrap />
    </ContextProvider>
  </ErrorBoundary>
);

if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js').catch(function (err) {
      console.error('SW registration failed', err);
    });
  });
}

// Capture beforeinstallprompt as early as possible — it can fire before React mounts.
window.__pwaInstallPrompt = null;
window.addEventListener('beforeinstallprompt', function (e) {
  e.preventDefault();
  window.__pwaInstallPrompt = e;
});
