import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { QRCodeCanvas } from 'qrcode.react';
import { checkinService } from '../../services/eventApp/checkin.service';
import { attendanceService } from '../../services/attendance/attendance.service';

const POLL_INTERVAL_MS = 5000;
// Keep polling this long after check-in so a badge linked slightly after check-in
// still swaps the QR live; then stop to avoid indefinite background requests.
const POLL_AFTER_CHECKIN_MS = 120000;

function MyTicket(props) {
  const event = props.event;
  const eventId = event && event.id;
  const { t } = useTranslation();

  const [ticket, setTicket] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Indemnity form state
  const [indemnityFormText, setIndemnityFormText] = useState(null);
  const [indemnityLoading, setIndemnityLoading] = useState(false);
  const [indemnityError, setIndemnityError] = useState(null);
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Load ticket on mount
  useEffect(function() {
    if (!eventId) {
      setIsLoading(false);
      setError(t('No event found.'));
      return;
    }
    checkinService.getMyTicket(eventId).then(function(result) {
      if (result.error) {
        setError(result.error);
      } else {
        setTicket(result.data);
      }
      setIsLoading(false);
    });
  }, [eventId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load indemnity form text when the gate is active
  const needsIndemnity = ticket && ticket.has_indemnity_form && !ticket.indemnity_signed;
  useEffect(function() {
    if (!needsIndemnity || !eventId) return;
    setIndemnityLoading(true);
    attendanceService.getIndemnityForm(eventId).then(function(result) {
      setIndemnityLoading(false);
      if (result.error) {
        setIndemnityError(result.error);
      } else {
        setIndemnityFormText(result.data.indemnity_form);
      }
    });
  }, [needsIndemnity, eventId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Poll every 5 s (while the tab is visible) to reflect two things a registration
  // volunteer may change from their side, without the attendee reloading: getting
  // checked in, and having a blank badge linked (which swaps the ticket token/QR).
  // Before check-in we poll indefinitely; after check-in we keep polling for a
  // short window so a badge linked just after check-in is still picked up live.
  const checkedIn = ticket ? ticket.checked_in : false;
  useEffect(function() {
    if (!eventId) return;
    var interval = setInterval(function() {
      if (document.hidden) return;
      checkinService.getMyTicket(eventId).then(function(result) {
        if (!result.data) return;
        setTicket(function(prev) {
          if (!prev) return result.data;
          if (result.data.checked_in !== prev.checked_in || result.data.token !== prev.token) {
            return result.data;
          }
          return prev;
        });
      });
    }, POLL_INTERVAL_MS);
    var stopTimeout = null;
    if (checkedIn) {
      stopTimeout = setTimeout(function() { clearInterval(interval); }, POLL_AFTER_CHECKIN_MS);
    }
    return function() {
      clearInterval(interval);
      if (stopTimeout) clearTimeout(stopTimeout);
    };
  }, [eventId, checkedIn]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSignIndemnity = useCallback(function(e) {
    e.preventDefault();
    setSubmitting(true);
    attendanceService.postIndemnity(eventId).then(function(result) {
      setSubmitting(false);
      if (result.error) {
        setIndemnityError(result.error);
      } else {
        setTicket(function(prev) { return Object.assign({}, prev, { indemnity_signed: true }); });
      }
    });
  }, [eventId]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="spinner-border" role="status">
          <span className="sr-only">{t('Loading...')}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="alert alert-danger mt-4">{error}</div>;
  }

  if (!ticket) {
    return <div className="alert alert-warning mt-4">{t('Ticket not found.')}</div>;
  }

  // Indemnity gate
  if (needsIndemnity) {
    return (
      <div className="max-w-lg mx-auto py-8 px-4 space-y-5">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center mx-auto">
            <i className="fas fa-file-signature text-xl text-amber-600" />
          </div>
          <h2 className="text-xl font-bold text-foreground">{t('Indemnity form required')}</h2>
          <p className="text-sm text-muted-foreground">
            {t('Please read and sign the indemnity form below to access your ticket.')}
          </p>
        </div>

        {indemnityLoading && (
          <div className="flex justify-center py-6">
            <div className="spinner-border" role="status">
              <span className="sr-only">{t('Loading...')}</span>
            </div>
          </div>
        )}

        {indemnityError && (
          <div className="alert alert-danger">{indemnityError}</div>
        )}

        {indemnityFormText && (
          <form onSubmit={handleSignIndemnity} className="space-y-4">
            <div className="bg-white rounded-2xl border border-border shadow-sm p-5 max-h-72 overflow-y-auto text-sm text-foreground leading-relaxed whitespace-pre-wrap">
              {indemnityFormText}
            </div>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary"
                checked={agreed}
                onChange={function(e) { setAgreed(e.target.checked); }}
                required
              />
              <span className="text-sm text-foreground">
                {t('I agree with the terms outlined in the indemnity form above.')}
              </span>
            </label>

            <button
              type="submit"
              disabled={!agreed || submitting}
              className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {submitting && (
                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              )}
              {submitting ? t('Signing...') : t('Sign and view my ticket')}
            </button>
          </form>
        )}
      </div>
    );
  }

  // Ticket view
  return (
    <div className="max-w-sm mx-auto py-8 px-4">
      <div className="bg-white rounded-2xl shadow-md border border-border p-6 flex flex-col items-center gap-4 print-badge">
        <h1 className="text-2xl font-bold text-foreground text-center">{ticket.event_name}</h1>

        <div className="my-2">
          <QRCodeCanvas value={ticket.qr_url} size={220} includeMargin={true} />
        </div>

        <div className="text-center">
          <p className="text-xl font-semibold text-foreground">{ticket.fullname}</p>
          <p className="text-sm text-foreground/60 mt-1">{ticket.role}</p>
        </div>

        {checkedIn ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            <i className="fas fa-check text-xs" />
            {t('Checked In')}
            {ticket.checked_in_at && (
              <span className="text-xs font-normal opacity-75">
                &nbsp;{new Date(ticket.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </span>
        ) : (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
            {t('Not Yet Checked In')}
          </span>
        )}

        <button
          className="mt-4 w-full px-4 py-2 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all no-print"
          onClick={function() { window.print(); }}
        >
          {t('Print Ticket')}
        </button>
      </div>

      <style>{`
        @media print {
          body * { visibility: hidden; }
          .print-badge, .print-badge * { visibility: visible; }
          .print-badge { position: fixed; left: 0; top: 0; width: 100%; }
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}

export default MyTicket;
