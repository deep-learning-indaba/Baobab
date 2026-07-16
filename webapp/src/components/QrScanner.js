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

// TEMP DEBUG: on-screen readout to diagnose the iOS camera-switch issue.
// Remove once the flip is confirmed working.
const QR_DEBUG = true;

export default function QrScanner({ onScan }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState('requesting');
  const [canFlip, setCanFlip] = useState(false);
  const [facingMode, setFacingMode] = useState('environment');
  const [debug, setDebug] = useState('');

  const instanceRef = useRef(null);
  const elementId = useRef('qr-el-' + (++_idCounter)).current;
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;

  const stopScanner = useCallback(async () => {
    const inst = instanceRef.current;
    instanceRef.current = null;

    // iOS/WebKit keeps the camera held (and paints the next capture as a frozen
    // grey frame) unless we detach the MediaStream from the <video> ourselves.
    // The library removes the element on stop() but never pauses it or nulls
    // srcObject, so do that first.
    const el = document.getElementById(elementId);
    const video = el && el.querySelector('video');
    if (video) {
      try { video.pause(); } catch (_) {}
      video.srcObject = null;
    }

    if (inst) {
      try { await inst.stop(); } catch (_) {}
    }
    if (el) el.innerHTML = '';
  }, [elementId]);

  const startScanner = useCallback(async (facing) => {
    const hadPreviousCamera = !!instanceRef.current;
    await stopScanner();
    setStatus('requesting');

    // After releasing a camera, iOS needs a moment before the next capture will
    // actually paint — starting immediately gives a live-but-grey video.
    if (hadPreviousCamera) {
      await new Promise((resolve) => setTimeout(resolve, 400));
    }

    const instance = new Html5Qrcode(elementId);
    instanceRef.current = instance;

    try {
      await instance.start(
        { facingMode: facing },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        (text) => onScanRef.current(text),
        () => {}
      );

      // The library sets srcObject then calls video.play() without awaiting or
      // retrying. On iOS that play() is dropped right after a camera switch, so
      // the video never fires "playing" and shows a blank frame. Nudge it.
      const el = document.getElementById(elementId);
      const video = el && el.querySelector('video');
      if (video) {
        for (let i = 0; i < 3 && instanceRef.current === instance; i++) {
          if (!video.paused && video.readyState >= 2) break;
          try { await video.play(); } catch (_) {}
          await new Promise((resolve) => setTimeout(resolve, 150));
        }
      }

      setStatus('scanning');
      Html5Qrcode.getCameras().then((cams) => {
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
    startScanner('environment');
    return () => { stopScanner(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // TEMP DEBUG: poll the live <video> + track state so a screenshot pins down
  // which stage of the camera switch is failing. Remove with QR_DEBUG.
  useEffect(() => {
    if (!QR_DEBUG) return;
    const id = setInterval(() => {
      const el = document.getElementById(elementId);
      const video = el && el.querySelector('video');
      if (!video) {
        setDebug('status=' + status + ' facing=' + facingMode + ' | no <video>');
        return;
      }
      const stream = video.srcObject;
      const track = stream && stream.getVideoTracks && stream.getVideoTracks()[0];
      const s = track && track.getSettings ? track.getSettings() : {};
      setDebug(
        'status=' + status + ' want=' + facingMode +
        ' paused=' + video.paused + ' rs=' + video.readyState +
        ' vid=' + video.videoWidth + 'x' + video.videoHeight +
        ' | track=' + (track ? track.readyState : 'none') +
        ' facing=' + (s.facingMode || '?') +
        ' lbl=' + (track ? String(track.label).slice(0, 24) : '-')
      );
    }, 500);
    return () => clearInterval(id);
  }, [elementId, status, facingMode]);

  const handleFlip = useCallback(async () => {
    const next = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(next);
    await startScanner(next);
  }, [facingMode, startScanner]);

  const handleRetry = useCallback(() => {
    startScanner(facingMode);
  }, [facingMode, startScanner]);

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

      {QR_DEBUG && (
        <div className="absolute top-1 left-1 right-1 z-20 bg-black/80 text-green-300 text-[10px] leading-tight font-mono p-1.5 rounded break-all pointer-events-none">
          {debug || 'debug…'}
        </div>
      )}
    </div>
  );
}
