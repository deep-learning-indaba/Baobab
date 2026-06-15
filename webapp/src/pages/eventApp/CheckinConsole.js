import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { checkinService } from '../../services/eventApp/checkin.service';

const SCAN_DEBOUNCE_MS = 3000;

function extractToken(decodedText) {
  try {
    const url = new URL(decodedText);
    const t = url.searchParams.get('t');
    if (t) {
      return t;
    }
  } catch (e) {}
  return decodedText;
}

function CheckinConsole(props) {
  const event = props.event;
  const { t } = useTranslation();

  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [result, setResult] = useState(null);

  const scannerRef = useRef(null);
  const scannerInstanceRef = useRef(null);
  const lastScannedTokenRef = useRef(null);
  const lastScannedAtRef = useRef(0);

  const loadPreview = useCallback(function(token) {
    const eventId = event && event.id;
    setPreviewLoading(true);
    setPreview(null);
    setResult(null);
    checkinService.resolveToken(eventId, token).then(function(res) {
      setPreviewLoading(false);
      if (res.error) {
        setResult({ type: 'error', message: res.error });
      } else {
        setPreview(res.data);
      }
    });
  }, [event && event.id]);

  useEffect(function() {
    if (!scannerRef.current) {
      return;
    }
    const scanner = new Html5QrcodeScanner(
      'qr-scanner-region',
      { fps: 10, qrbox: { width: 250, height: 250 } },
      false
    );
    scannerInstanceRef.current = scanner;
    scanner.render(function(decodedText) {
      const token = extractToken(decodedText);
      const now = Date.now();
      if (token === lastScannedTokenRef.current && now - lastScannedAtRef.current < SCAN_DEBOUNCE_MS) {
        return;
      }
      lastScannedTokenRef.current = token;
      lastScannedAtRef.current = now;
      loadPreview(token);
    }, function() {});
    return function() {
      scanner.clear().catch(function() {});
    };
  }, [loadPreview]);

  const confirmCheckin = useCallback(function() {
    const eventId = event && event.id;
    const token = lastScannedTokenRef.current;
    setCheckinLoading(true);
    checkinService.checkin({ eventId: eventId, token: token, method: 'scan' }).then(function(res) {
      setCheckinLoading(false);
      setPreview(null);
      if (res.data && res.data.already_checked_in) {
        setResult({ type: 'already', message: t('{{name}} is already checked in', { name: res.data.fullname }) });
      } else if (res.error) {
        setResult({ type: 'error', message: res.error });
      } else {
        setResult({ type: 'success', message: t('Checked in {{name}}', { name: res.data && res.data.fullname }) });
        setTimeout(function() { setResult(null); }, 2500);
      }
    });
  }, [event && event.id, t]);

  const cancelPreview = useCallback(function() {
    setPreview(null);
    setResult(null);
    lastScannedTokenRef.current = null;
  }, []);

  return (
    <div className="max-w-lg mx-auto py-6 px-4 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">{t('Check-in Console')}</h1>

      {!navigator.onLine && (
        <div className="alert alert-danger">
          {t('No connection — check-in needs internet. Try again when connected.')}
        </div>
      )}

      <div className="bg-white rounded-2xl border border-border shadow-sm p-4">
        <div id="qr-scanner-region" ref={scannerRef} />
      </div>

      {previewLoading && (
        <div className="flex justify-center py-4">
          <div className="spinner-border" role="status">
            <span className="sr-only">{t('Loading...')}</span>
          </div>
        </div>
      )}

      {preview && !result && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-3">
          <p className="text-lg font-semibold text-foreground">{preview.fullname}</p>
          <p className="text-sm text-foreground/60">{preview.role}</p>
          {!preview.indemnity_signed && (
            <p className="text-sm text-yellow-700 font-medium">{t('Indemnity not signed — please note for help desk.')}</p>
          )}
          {preview.already_checked_in && (
            <p className="text-sm text-amber-700 font-medium">{t('Already checked in today.')}</p>
          )}
          <div className="flex gap-3 pt-2">
            <button
              className="flex-1 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
              onClick={confirmCheckin}
              disabled={checkinLoading}
            >
              {checkinLoading ? t('Checking in...') : t('Confirm Check-in')}
            </button>
            <button
              className="px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
              onClick={cancelPreview}
            >
              {t('Cancel')}
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className={
          result.type === 'success'
            ? 'alert alert-success rounded-xl'
            : result.type === 'already'
            ? 'alert alert-warning rounded-xl'
            : 'alert alert-danger rounded-xl'
        }>
          {result.message}
        </div>
      )}
    </div>
  );
}

export default CheckinConsole;
