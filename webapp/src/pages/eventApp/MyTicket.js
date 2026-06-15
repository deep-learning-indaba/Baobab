import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { QRCodeCanvas } from 'qrcode.react';
import { checkinService } from '../../services/eventApp/checkin.service';

function MyTicket(props) {
  const event = props.event;
  const { t } = useTranslation();

  const [ticket, setTicket] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(function() {
    const eventId = event && event.id;
    if (!eventId) {
      setIsLoading(false);
      setError('No event found.');
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
  }, [event && event.id]);

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center py-8">
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

        {ticket.checked_in ? (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
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
