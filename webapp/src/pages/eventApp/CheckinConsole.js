import React, { useState, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import QrScanner from '../../components/QrScanner';
import { checkinService } from '../../services/eventApp/checkin.service';

const SCAN_DEBOUNCE_MS = 3000;

function extractToken(decodedText) {
  try {
    const url = new URL(decodedText);
    const t = url.searchParams.get('t');
    if (t) return t;
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

  const lastScannedTokenRef = useRef(null);
  const lastScannedAtRef = useRef(0);

  const resetToScanner = useCallback(function() {
    setPreview(null);
    setResult(null);
    setPreviewLoading(false);
    lastScannedTokenRef.current = null;
    lastScannedAtRef.current = 0;
  }, []);

  const handleScan = useCallback(function(decodedText) {
    const token = extractToken(decodedText);
    const now = Date.now();
    if (token === lastScannedTokenRef.current && now - lastScannedAtRef.current < SCAN_DEBOUNCE_MS) {
      return;
    }
    lastScannedTokenRef.current = token;
    lastScannedAtRef.current = now;

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
  }, [event && event.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const confirmCheckin = useCallback(function() {
    const eventId = event && event.id;
    const token = lastScannedTokenRef.current;
    setCheckinLoading(true);
    checkinService.checkin({ eventId: eventId, token: token, method: 'scan' }).then(function(res) {
      setCheckinLoading(false);
      setPreview(null);
      if (res.data && res.data.already_checked_in) {
        setResult({ type: 'already', message: t('{{name}} is already checked in', { name: res.data.fullname }), badgeNotPrinted: !res.data.badge_exported });
      } else if (res.error) {
        setResult({ type: 'error', message: res.error });
      } else {
        setResult({ type: 'success', message: t('Checked in {{name}}', { name: res.data && res.data.fullname }), badgeNotPrinted: !(res.data && res.data.badge_exported) });
      }
    });
  }, [event && event.id, t]); // eslint-disable-line react-hooks/exhaustive-deps

  const showScanner = !previewLoading && !preview && !result;
  const indemnityBlocked = preview && preview.has_indemnity_form && !preview.indemnity_signed;
  const badgeNotPrinted = preview && !preview.badge_exported;

  return (
    <div className="max-w-lg mx-auto py-6 px-4 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">{t('Check-in Console')}</h1>

      {!navigator.onLine && (
        <div className="alert alert-danger">
          {t('No connection — check-in needs internet. Try again when connected.')}
        </div>
      )}

      {showScanner && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-4">
          <QrScanner onScan={handleScan} />
        </div>
      )}

      {previewLoading && (
        <div className="flex justify-center py-8">
          <div className="spinner-border" role="status">
            <span className="sr-only">{t('Loading...')}</span>
          </div>
        </div>
      )}

      {preview && !result && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-3">
          <p className="text-lg font-semibold text-foreground">{preview.fullname}</p>
          <p className="text-sm text-foreground/60">{preview.role}</p>
          {preview.already_checked_in && (
            <p className="text-sm text-amber-700 font-medium">{t('Already checked in today.')}</p>
          )}
          {indemnityBlocked && (
            <p className="text-sm text-red-700 font-medium">
              {t('Indemnity form not signed — check-in cannot proceed until the attendee signs.')}
            </p>
          )}
          {badgeNotPrinted && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800 font-medium">
              {t('No badge was printed for this attendee — don\'t waste time searching for one; direct them to the registration desk.')}
            </div>
          )}
          <div className="flex gap-3 pt-2">
            <button
              className="flex-1 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              onClick={confirmCheckin}
              disabled={checkinLoading || indemnityBlocked}
            >
              {checkinLoading ? t('Checking in...') : t('Confirm Check-in')}
            </button>
            <button
              className="px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
              onClick={resetToScanner}
            >
              {t('Cancel')}
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className={
            result.type === 'success'
              ? 'alert alert-success rounded-xl'
              : result.type === 'already'
              ? 'alert alert-warning rounded-xl'
              : 'alert alert-danger rounded-xl'
          }>
            {result.message}
          </div>
          {result.type !== 'error' && result.badgeNotPrinted && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800 font-medium">
              {t('No badge was printed for this attendee — don\'t waste time searching for one; direct them to the registration desk.')}
            </div>
          )}
          <button
            onClick={resetToScanner}
            className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
          >
            {t('Scan next attendee')}
          </button>
        </div>
      )}
    </div>
  );
}

export default CheckinConsole;
