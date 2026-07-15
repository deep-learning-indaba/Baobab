import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { useTranslation } from 'react-i18next';

function CameraFlipIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 7h-9" />
      <path d="M14 17H5" />
      <circle cx="17" cy="17" r="3" />
      <circle cx="7" cy="7" r="3" />
      <path d="M17 14v6" />
      <path d="M7 4v6" />
    </svg>
  );
}

let _idCounter = 0;

export default function QrScanner({ onScan }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState('requesting');
  const [canFlip, setCanFlip] = useState(false);

  const instanceRef = useRef(null);
  const elementId = useRef('qr-el-' + (++_idCounter)).current;
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;

  // Cameras discovered so far, and the deviceId of whichever one is currently
  // running. Once we know deviceIds we flip by deviceId rather than by
  // re-requesting a facingMode constraint.
  const camerasRef = useRef([]);
  const activeCameraIdRef = useRef(null);
  const facingModeRef = useRef('environment');

  const stopScanner = useCallback(async () => {
    const inst = instanceRef.current;
    instanceRef.current = null;
    if (inst) {
      try { await inst.stop(); } catch (_) {}
    }
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = '';
  }, [elementId]);

  const startScanner = useCallback(async (cameraIdOrConfig) => {
    await stopScanner();
    setStatus('requesting');

    const instance = new Html5Qrcode(elementId);
    instanceRef.current = instance;

    try {
      await instance.start(
        cameraIdOrConfig,
        { fps: 10, qrbox: { width: 250, height: 250 } },
        (text) => onScanRef.current(text),
        () => {}
      );
      setStatus('scanning');

      try {
        const settings = instance.getRunningTrackSettings();
        if (settings && settings.deviceId) activeCameraIdRef.current = settings.deviceId;
      } catch (_) {}

      Html5Qrcode.getCameras().then((cams) => {
        camerasRef.current = cams;
        setCanFlip(cams.length > 1);
      }).catch(() => {});
    } catch (err) {
      instanceRef.current = null;
      const msg = String(err?.message ?? err ?? '');
      const isDenied =
        msg.toLowerCase().includes('permission') ||
        msg.toLowerCase().includes('notallowed') ||
        msg.toLowerCase().includes('denied') ||
        err?.name === 'NotAllowedError';
      setStatus(isDenied ? 'denied' : 'error');
    }
  }, [elementId, stopScanner]);

  useEffect(() => {
    startScanner({ facingMode: 'environment' });
    return () => { stopScanner(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFlip = useCallback(async () => {
    const cams = camerasRef.current;
    const activeId = activeCameraIdRef.current;

    if (cams.length > 1) {
      // Re-requesting a facingMode constraint on iOS Safari after a camera
      // has already been streaming reliably yields a live-but-frozen grey
      // frame for the back camera, so target the next camera by deviceId.
      const idx = activeId ? cams.findIndex((c) => c.id === activeId) : -1;
      const next = cams[idx === -1 ? 0 : (idx + 1) % cams.length];
      await startScanner(next.id);
    } else {
      const next = facingModeRef.current === 'environment' ? 'user' : 'environment';
      facingModeRef.current = next;
      await startScanner({ facingMode: next });
    }
  }, [startScanner]);

  const handleRetry = useCallback(() => {
    startScanner(activeCameraIdRef.current || { facingMode: facingModeRef.current });
  }, [startScanner]);

  return (
    <div className="relative min-h-[300px]">
      <div id={elementId} className="w-full" />

      {status === 'requesting' && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-white rounded-xl">
          <div className="w-8 h-8 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">{t('Starting camera...')}</p>
        </div>
      )}

      {status === 'denied' && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 bg-white rounded-xl px-6 text-center">
          <div className="w-16 h-16 rounded-full bg-surface-low flex items-center justify-center">
            <i className="fas fa-camera text-2xl text-muted-foreground" />
          </div>
          <div>
            <p className="font-semibold text-foreground">{t('Camera access needed')}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {t('Allow camera access to scan QR codes.')}
            </p>
          </div>
          <button
            onClick={handleRetry}
            className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
          >
            {t('Allow Camera Access')}
          </button>
          <p className="text-xs text-muted-foreground/70">
            {t('If blocked, enable camera in your browser settings.')}
          </p>
        </div>
      )}

      {status === 'error' && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-white rounded-xl px-6 text-center">
          <i className="fas fa-exclamation-triangle text-2xl text-amber-500" />
          <p className="text-sm text-foreground">{t('Could not start camera.')}</p>
          <button
            onClick={handleRetry}
            className="px-5 py-2 rounded-lg border border-border text-sm text-foreground hover:bg-surface-low transition-all"
          >
            {t('Try again')}
          </button>
        </div>
      )}

      {status === 'scanning' && canFlip && (
        <button
          onClick={handleFlip}
          aria-label={t('Switch camera')}
          className="absolute bottom-3 right-3 z-10 w-11 h-11 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition-all shadow-lg"
        >
          <CameraFlipIcon />
        </button>
      )}
    </div>
  );
}
