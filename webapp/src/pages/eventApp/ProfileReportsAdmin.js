import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { connectionService } from '../../services/eventApp/connection.service';
import { formatInEventTz } from '../../utils/datetime';
import Avatar from '../../components/Avatar';

var ABOUT_EXCERPT_LENGTH = 300;

function excerpt(text) {
  if (!text) return '';
  return text.length > ABOUT_EXCERPT_LENGTH ? text.slice(0, ABOUT_EXCERPT_LENGTH) + '…' : text;
}

function ProfileReportsAdmin(props) {
  var event = props.event;
  var { t } = useTranslation();
  var eventId = event && event.id;
  var eventKey = event && event.key;
  var timezone = (event && event.timezone) || 'UTC';

  var [reports, setReports] = useState([]);
  var [loading, setLoading] = useState(true);
  var [error, setError] = useState(null);
  var [actionError, setActionError] = useState(null);
  var [busy, setBusy] = useState(false);

  function load() {
    if (!eventId) { setLoading(false); return; }
    return connectionService.listReports(eventId).then(function (r) {
      setLoading(false);
      if (r.error) setError(r.error); else setReports(r.data || []);
    });
  }
  useEffect(function () { load(); }, [eventId]);

  function act(request) {
    setBusy(true);
    setActionError(null);
    request.then(function (r) {
      if (r.error) setActionError(r.error);
      return load();
    }).then(function () { setBusy(false); });
  }

  function handleDismiss(reportId) {
    act(connectionService.dismissReport(eventId, reportId));
  }

  function handleRemovePhoto(reportId) {
    if (!window.confirm(t('Remove this photo?'))) return;
    act(connectionService.removePhoto(eventId, reportId));
  }

  function categoryLabel(category) {
    if (category === 'photo') return t('Photo');
    if (category === 'profile') return t('Profile content');
    return t('Person');
  }

  if (loading) return <div className="w-full pt-6 text-center text-muted-foreground">{t('Loading')}</div>;
  if (error) return <div className="w-full pt-6 text-center text-destructive">{t('Access denied')}</div>;

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <h1 className="font-heading text-2xl font-bold text-foreground">{t('Reported people')}</h1>

      {actionError && <p className="text-sm text-destructive">{actionError}</p>}

      {reports.length === 0 && (
        <p className="text-sm text-muted-foreground py-8 text-center">{t('No reported people.')}</p>
      )}

      <div className="space-y-3">
        {reports.map(function (r) {
          var reportedName = r.reported.firstname + ' ' + r.reported.lastname;
          var showCurrent = r.photo_changed && r.reported.photo_url;
          return (
            <div key={r.report_id} className="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1 space-y-1">
                  <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                    {categoryLabel(r.category)}
                  </span>
                  <p className="text-xs text-muted-foreground">
                    {t('Reported by')} {r.reporter.firstname} {r.reporter.lastname} ·{' '}
                    {formatInEventTz(r.created_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
                  </p>
                  {r.reason && <p className="text-sm text-foreground">{t('Reason')}: {r.reason}</p>}
                </div>
                <div className="flex flex-col gap-2 flex-shrink-0">
                  {r.reported.photo_url && (
                    <button
                      disabled={busy}
                      onClick={function () { handleRemovePhoto(r.report_id); }}
                      className="px-3 py-1.5 rounded-lg border border-destructive text-destructive text-xs font-semibold hover:bg-destructive/5 disabled:opacity-50"
                    >
                      {t('Remove photo')}
                    </button>
                  )}
                  <button
                    disabled={busy}
                    onClick={function () { handleDismiss(r.report_id); }}
                    className="px-3 py-1.5 rounded-lg border border-border text-foreground text-xs font-semibold hover:bg-muted/40 disabled:opacity-50"
                  >
                    {t('Dismiss')}
                  </button>
                </div>
              </div>

              <div className="flex items-start gap-4 p-3 bg-muted/30 rounded-lg border border-border">
                <Avatar
                  photoUrl={r.reported_photo_url}
                  firstname={r.reported.firstname}
                  lastname={r.reported.lastname}
                  size="lg"
                  alt={t('Profile photo of {{name}}', { name: reportedName })}
                />
                {showCurrent && (
                  <div className="flex flex-col items-center gap-1">
                    <Avatar
                      photoUrl={r.reported.photo_url}
                      firstname={r.reported.firstname}
                      lastname={r.reported.lastname}
                      size="lg"
                      alt={t('Current photo')}
                    />
                    <span className="text-xs text-muted-foreground">{t('Current photo')}</span>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-foreground">{reportedName}</p>
                  {r.reported.headline && <p className="text-sm text-foreground/80">{r.reported.headline}</p>}
                  {r.reported.about && (
                    <p className="text-sm text-foreground/70 mt-1 whitespace-pre-line">{excerpt(r.reported.about)}</p>
                  )}
                  <Link
                    to={'/' + eventKey + '/app/profile/' + r.reported.user_id}
                    className="inline-block mt-2 text-xs text-primary hover:underline"
                  >
                    {t('View profile')}
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ProfileReportsAdmin;
