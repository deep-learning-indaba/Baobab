import React, { useState, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import QrScanner from '../../components/QrScanner';
import { checkinService } from '../../services/eventApp/checkin.service';

const SCAN_DEBOUNCE_MS = 3000;

// Minimum set of colours a CHECKIN tag's name can reference (e.g. "Yellow T-shirt").
// Text colour is picked per-background for contrast against that background.
const TAG_COLORS = {
  black: { bg: '#000000', text: '#ffffff' },
  purple: { bg: '#9333ea', text: '#ffffff' },
  red: { bg: '#dc2626', text: '#ffffff' },
  yellow: { bg: '#facc15', text: '#111827' },
  green: { bg: '#16a34a', text: '#ffffff' },
  blue: { bg: '#2563eb', text: '#ffffff' },
  orange: { bg: '#f97316', text: '#111827' },
  white: { bg: '#ffffff', text: '#111827' },
};

function getTagColorStyle(tagName) {
  const lower = tagName.toLowerCase();
  for (const color of Object.keys(TAG_COLORS)) {
    if (new RegExp('\\b' + color + '\\b').test(lower)) {
      return TAG_COLORS[color];
    }
  }
  return null;
}

function TagChips(props) {
  const tags = props.tags;
  if (!tags || tags.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map(function(tagName) {
        const colorStyle = getTagColorStyle(tagName);
        return (
          <span
            key={tagName}
            className={
              'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold' +
              (colorStyle ? ' border border-black/10' : ' bg-slate-100 text-muted-foreground border border-border')
            }
            style={colorStyle ? { backgroundColor: colorStyle.bg, color: colorStyle.text } : undefined}
          >
            {tagName}
          </span>
        );
      })}
    </div>
  );
}

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

  // Blank-badge linking. linkTarget holds the attendee we're assigning a badge
  // to; while it's set the scanner reads blank badges instead of doing check-in.
  const [linkTarget, setLinkTarget] = useState(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkResult, setLinkResult] = useState(null);

  const lastScannedTokenRef = useRef(null);
  const lastScannedAtRef = useRef(0);
  const linkingRef = useRef(false);

  const resetToScanner = useCallback(function() {
    setPreview(null);
    setResult(null);
    setPreviewLoading(false);
    setLinkTarget(null);
    setLinkResult(null);
    setLinkLoading(false);
    linkingRef.current = false;
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
      const data = res.data;
      if (data && data.already_checked_in) {
        setResult({ type: 'already', message: t('{{name}} is already checked in', { name: data.fullname }), badgeNotPrinted: !data.badge_exported, userId: data.user_id, fullname: data.fullname, tags: data.tags });
      } else if (res.error) {
        setResult({ type: 'error', message: res.error });
      } else {
        setResult({ type: 'success', message: t('Checked in {{name}}', { name: data && data.fullname }), badgeNotPrinted: !(data && data.badge_exported), userId: data && data.user_id, fullname: data && data.fullname, tags: data && data.tags });
      }
    });
  }, [event && event.id, t]); // eslint-disable-line react-hooks/exhaustive-deps

  // Enter link mode: the next scan is treated as a blank badge to assign to this
  // attendee. Reset the scan debounce so an immediately-repeated code still fires.
  const startLink = useCallback(function(userId, fullname) {
    setPreview(null);
    setResult(null);
    setLinkResult(null);
    linkingRef.current = false;
    lastScannedTokenRef.current = null;
    lastScannedAtRef.current = 0;
    setLinkTarget({ userId: userId, fullname: fullname });
  }, []);

  const handleLinkScan = useCallback(function(decodedText) {
    if (linkingRef.current || !linkTarget) return;
    const token = extractToken(decodedText);
    linkingRef.current = true;
    setLinkLoading(true);
    const eventId = event && event.id;
    checkinService.linkBadge(eventId, linkTarget.userId, token).then(function(res) {
      setLinkLoading(false);
      linkingRef.current = false;
      if (res.error) {
        setLinkResult({ type: 'error', message: res.error });
      } else {
        setLinkResult({ type: 'success', message: t('Blank badge linked to {{name}}. Hand them this badge.', { name: linkTarget.fullname }) });
      }
    });
  }, [event && event.id, linkTarget, t]); // eslint-disable-line react-hooks/exhaustive-deps

  const retryLink = useCallback(function() {
    setLinkResult(null);
    linkingRef.current = false;
    lastScannedTokenRef.current = null;
    lastScannedAtRef.current = 0;
  }, []);

  const showScanner = !previewLoading && !preview && !result && !linkTarget;
  const indemnityBlocked = preview && preview.has_indemnity_form && !preview.indemnity_signed;
  const badgeNotPrinted = preview && !preview.badge_exported;
  const showLinkScanner = linkTarget && !linkLoading && !linkResult;

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
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-sm font-semibold bg-primary/10 text-primary border border-primary/20">
            {preview.role}
          </span>
          <TagChips tags={preview.tags} />
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
              {t('No badge was printed for this attendee — link a blank badge to them below.')}
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
          <button
            className={
              'w-full px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ' +
              (badgeNotPrinted
                ? 'bg-amber-500 text-white hover:bg-amber-600'
                : 'border border-border text-foreground hover:bg-surface-low')
            }
            onClick={function() { startLink(preview.user_id, preview.fullname); }}
          >
            {t('Link a blank badge')}
          </button>
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
          {result.type !== 'error' && <TagChips tags={result.tags} />}
          {result.type !== 'error' && result.badgeNotPrinted && (
            <div className="space-y-3">
              <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-800 font-medium">
                {t('No badge was printed for this attendee — link a blank badge to them.')}
              </div>
              <button
                onClick={function() { startLink(result.userId, result.fullname); }}
                className="w-full py-3 rounded-xl bg-amber-500 text-white font-semibold text-sm hover:bg-amber-600 transition-all"
              >
                {t('Link a blank badge')}
              </button>
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

      {linkTarget && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-3">
          <p className="text-sm font-medium text-foreground">
            {t('Linking a blank badge to')} <span className="font-bold">{linkTarget.fullname}</span>
          </p>

          {showLinkScanner && (
            <>
              <p className="text-sm text-muted-foreground">{t('Scan the QR code on a blank badge.')}</p>
              <QrScanner onScan={handleLinkScan} />
              <button
                className="w-full px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
                onClick={resetToScanner}
              >
                {t('Cancel')}
              </button>
            </>
          )}

          {linkLoading && (
            <div className="flex justify-center py-8">
              <div className="spinner-border" role="status">
                <span className="sr-only">{t('Loading...')}</span>
              </div>
            </div>
          )}

          {linkResult && (
            <div className="space-y-3">
              <div className={linkResult.type === 'success' ? 'alert alert-success rounded-xl' : 'alert alert-danger rounded-xl'}>
                {linkResult.message}
              </div>
              {linkResult.type === 'error' && (
                <button
                  onClick={retryLink}
                  className="w-full py-3 rounded-xl bg-amber-500 text-white font-semibold text-sm hover:bg-amber-600 transition-all"
                >
                  {t('Scan a different badge')}
                </button>
              )}
              <button
                onClick={resetToScanner}
                className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
              >
                {t('Done')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CheckinConsole;
