import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { connectionService } from '../../services/eventApp/connection.service';

const SCAN_DEBOUNCE_MS = 3000;

function extractToken(decodedText) {
  try {
    var url = new URL(decodedText);
    var t = url.searchParams.get('t');
    if (t) return t;
  } catch (e) {}
  return decodedText;
}

function Avatar({ photoUrl, firstname, lastname }) {
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt={firstname + ' ' + lastname}
        className="w-20 h-20 rounded-full object-cover ring-2 ring-primary/20"
      />
    );
  }
  var initials = (firstname || '?')[0].toUpperCase() + (lastname || '?')[0].toUpperCase();
  return (
    <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center text-2xl font-bold text-primary">
      {initials}
    </div>
  );
}

function ConnectionCard({ target, connectionState, eventKey, eventId, onStateChange, t }) {
  var [busy, setBusy] = useState(false);
  var [localState, setLocalState] = useState(connectionState);
  var [error, setError] = useState(null);
  var [showReport, setShowReport] = useState(false);
  var [reportReason, setReportReason] = useState('');
  var [reported, setReported] = useState(false);

  useEffect(function() { setLocalState(connectionState); }, [connectionState]);

  function doConnect() {
    setBusy(true);
    setError(null);
    connectionService.connect(eventId, target.user_id).then(function(res) {
      setBusy(false);
      if (res.error) { setError(res.error); return; }
      setLocalState('outgoing_pending');
      onStateChange && onStateChange('outgoing_pending');
    });
  }

  function doWithdraw() {
    setBusy(true);
    connectionService.withdraw(eventId, target.user_id).then(function(res) {
      setBusy(false);
      if (res.error) { setError(res.error); return; }
      setLocalState('none');
      onStateChange && onStateChange('none');
    });
  }

  function doReport() {
    connectionService.report(eventId, target.user_id, reportReason).then(function() {
      setReported(true);
      setShowReport(false);
    });
  }

  return (
    <div className="bg-white rounded-2xl border border-border shadow-sm p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Avatar photoUrl={target.photo_url} firstname={target.firstname} lastname={target.lastname} />
        <div className="min-w-0 flex-1">
          <p className="text-lg font-bold text-foreground">{target.firstname} {target.lastname}</p>
          {target.role && <p className="text-sm text-primary font-medium">{target.role}</p>}
          {!target.hidden && target.headline && (
            <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">{target.headline}</p>
          )}
          {!target.hidden && target.affiliation && (
            <p className="text-xs text-muted-foreground">{target.affiliation}</p>
          )}
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="space-y-2">
        {localState === 'none' && (
          <button
            onClick={doConnect}
            disabled={busy}
            className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm disabled:opacity-50 hover:bg-primary-container transition-colors"
          >
            {busy ? t('Connecting...') : t('Save / Connect')}
          </button>
        )}
        {localState === 'outgoing_pending' && (
          <div className="space-y-2">
            <div className="w-full py-2.5 rounded-xl bg-muted text-muted-foreground font-semibold text-sm text-center">
              {t('Request sent')}
            </div>
            <button
              onClick={doWithdraw}
              disabled={busy}
              className="w-full py-2 rounded-xl border border-border text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('Withdraw request')}
            </button>
          </div>
        )}
        {localState === 'incoming_pending' && (
          <p className="text-sm text-muted-foreground text-center py-2">
            {t('They sent you a request — accept it in Connections.')}
          </p>
        )}
        {localState === 'connected' && (
          <div className="flex items-center justify-center gap-2 py-2 text-green-700 font-semibold text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            {t('Connected')}
          </div>
        )}
        {localState === 'blocked' && (
          <p className="text-sm text-muted-foreground text-center py-2">{t('Unable to send a request.')}</p>
        )}

        {!target.hidden && (
          <a
            href={'/' + eventKey + '/app/profile/' + target.user_id}
            className="block w-full py-2 rounded-xl border border-border text-sm text-center text-foreground hover:bg-muted/50 transition-colors"
          >
            {t('View full profile')}
          </a>
        )}
      </div>

      {!reported && !showReport && localState !== 'blocked' && (
        <button
          onClick={function() { setShowReport(true); }}
          className="text-xs text-muted-foreground/60 hover:text-destructive transition-colors"
        >
          {t('Report or block')}
        </button>
      )}
      {showReport && (
        <div className="space-y-2 pt-2 border-t border-border">
          <p className="text-sm font-medium text-foreground">{t('Report this person')}</p>
          <textarea
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            rows={2}
            placeholder={t('Optional: describe the issue')}
            value={reportReason}
            onChange={function(e) { setReportReason(e.target.value); }}
          />
          <div className="flex gap-2">
            <button
              onClick={doReport}
              className="flex-1 py-1.5 rounded-lg bg-destructive text-white text-sm font-medium"
            >
              {t('Send report')}
            </button>
            <button
              onClick={function() { setShowReport(false); }}
              className="flex-1 py-1.5 rounded-lg border border-border text-sm text-foreground"
            >
              {t('Cancel')}
            </button>
          </div>
        </div>
      )}
      {reported && (
        <p className="text-xs text-muted-foreground">{t("Thanks — the organising team has been notified.")}</p>
      )}
    </div>
  );
}

function ScanConnect(props) {
  var event = props.event;
  var history = props.history;
  var location = props.location;
  var { t } = useTranslation();

  var eventId = event && event.id;
  var eventKey = event && event.key;

  var [resolved, setResolved] = useState(null);
  var [isResolving, setIsResolving] = useState(false);
  var [resolveError, setResolveError] = useState(null);
  var [scannerReady, setScannerReady] = useState(false);

  var scannerRef = useRef(null);
  var scannerInstanceRef = useRef(null);
  var lastScannedRef = useRef(null);
  var lastScannedAtRef = useRef(0);

  function resolveToken(token) {
    if (!eventId) return;
    setIsResolving(true);
    setResolved(null);
    setResolveError(null);
    connectionService.resolve(eventId, token).then(function(res) {
      setIsResolving(false);
      if (res.error) { setResolveError(res.error); return; }
      if (res.data.is_self) {
        history.push('/' + eventKey + '/app/profile');
        return;
      }
      setResolved(res.data);
    });
  }

  // If ?t= is present on load, skip camera and resolve directly
  useEffect(function() {
    if (!eventId) return;
    var params = new URLSearchParams(location && location.search);
    var t_param = params.get('t');
    if (t_param) {
      resolveToken(t_param);
    } else {
      setScannerReady(true);
    }
  }, [eventId]);

  useEffect(function() {
    if (!scannerReady || !scannerRef.current) return;
    var scanner = new Html5QrcodeScanner(
      'qr-scan-connect-region',
      { fps: 10, qrbox: { width: 250, height: 250 } },
      false
    );
    scannerInstanceRef.current = scanner;
    scanner.render(function(decodedText) {
      var token = extractToken(decodedText);
      var now = Date.now();
      if (token === lastScannedRef.current && now - lastScannedAtRef.current < SCAN_DEBOUNCE_MS) return;
      lastScannedRef.current = token;
      lastScannedAtRef.current = now;
      resolveToken(token);
    }, function() {});
    return function() { scanner.clear().catch(function() {}); };
  }, [scannerReady]);

  return (
    <div className="w-full max-w-lg mx-auto pt-6 space-y-4">
      <h1 className="font-heading text-2xl font-bold text-foreground text-left">{t('Scan Badge')}</h1>

      {/* Camera scanner */}
      {scannerReady && !resolved && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-4">
          <p className="text-sm text-muted-foreground mb-3 text-left">{t('Point your camera at another attendee\'s badge QR code.')}</p>
          <div id="qr-scan-connect-region" ref={scannerRef} />
        </div>
      )}

      {isResolving && (
        <p className="text-center text-muted-foreground py-8">{t('Loading profile...')}</p>
      )}

      {resolveError && (
        <div className="bg-destructive/10 border border-destructive/30 rounded-xl p-4 text-sm text-destructive">
          {resolveError}
        </div>
      )}

      {resolved && (
        <div className="space-y-3">
          <ConnectionCard
            target={resolved.target}
            connectionState={resolved.connection.state}
            eventKey={eventKey}
            eventId={eventId}
            onStateChange={null}
            t={t}
          />
          {resolveError === null && (
            <button
              onClick={function() { setResolved(null); setScannerReady(true); setResolveError(null); }}
              className="w-full py-2 rounded-xl border border-border text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('Scan another badge')}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default ScanConnect;
