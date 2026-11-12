import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { profileService } from '../../services/eventApp/profile.service';
import { connectionService } from '../../services/eventApp/connection.service';
import Avatar from '../../components/Avatar';

function withProtocol(url) {
  if (!url) return url;
  return /^https?:\/\//i.test(url) ? url : `https://${url}`;
}

function ViewMemberProfile(props) {
  const event = props.event;
  const userId = props.match && props.match.params && props.match.params.userId;
  const { t } = useTranslation();

  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const [reportCategory, setReportCategory] = useState(null);
  const [reportReason, setReportReason] = useState('');
  const [reportError, setReportError] = useState(null);
  const [reportSending, setReportSending] = useState(false);
  const [reported, setReported] = useState(false);

  const eventId = event && event.id;

  useEffect(function() {
    if (!eventId || !userId) {
      setIsLoading(false);
      setError(t('Invalid profile link.'));
      return;
    }
    profileService.viewProfile(eventId, userId).then(function(result) {
      setIsLoading(false);
      if (result.error) {
        setError(result.error);
      } else {
        setProfile(result.data);
      }
    });
  }, [eventId, userId]);

  const currentUserId = props.user && props.user.id;
  const isOwnProfile = currentUserId != null && String(currentUserId) === String(userId);

  function openReport() {
    setReportCategory(profile.photo_url ? 'photo' : 'profile');
    setReportError(null);
    setShowReport(true);
  }

  function sendReport() {
    setReportSending(true);
    setReportError(null);
    connectionService.report(eventId, profile.user_id || Number(userId), reportReason, reportCategory).then(function(result) {
      setReportSending(false);
      if (result.error) {
        setReportError(result.error);
      } else {
        setShowReport(false);
        setReported(true);
      }
    });
  }

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

  if (!profile) {
    return <div className="alert alert-warning mt-4">{t('Profile not found.')}</div>;
  }

  if (profile.hidden) {
    return (
      <div className="max-w-lg mx-auto py-8 px-4">
        <div className="bg-white rounded-2xl border border-border shadow-sm p-6 flex flex-col items-center gap-3">
          <Avatar photoUrl={profile.photo_url} firstname={profile.firstname} lastname={profile.lastname} size="lg" />
          <h2 className="text-xl font-bold text-foreground">{profile.firstname} {profile.lastname}</h2>
          {profile.role && <p className="text-sm text-foreground/60">{profile.role}</p>}
          <p className="text-sm text-foreground/50 italic">{t('This member has hidden their profile.')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto py-8 px-4 space-y-4">
      <div className="bg-white rounded-2xl border border-border shadow-sm p-6 flex flex-col items-center gap-3">
        <Avatar photoUrl={profile.photo_url} firstname={profile.firstname} lastname={profile.lastname} size="xl" />
        <h2 className="text-2xl font-bold text-foreground">{profile.firstname} {profile.lastname}</h2>
        {profile.role && <p className="text-sm font-medium text-foreground/60">{profile.role}</p>}
        {profile.pronouns && <p className="text-xs text-foreground/50">{profile.pronouns}</p>}
      </div>

      {(profile.headline || profile.about) && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-5 space-y-2">
          {profile.headline && <p className="font-semibold text-foreground">{profile.headline}</p>}
          {profile.about && <p className="text-sm text-foreground/80 whitespace-pre-line">{profile.about}</p>}
        </div>
      )}

      {(profile.affiliation || profile.country || profile.city) && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-4 text-sm text-foreground/70 space-y-1">
          {profile.affiliation && <p>{profile.affiliation}</p>}
          {profile.city && profile.country
            ? <p>{profile.city}, {profile.country}</p>
            : <p>{profile.city || profile.country}</p>}
        </div>
      )}

      {profile.interests && profile.interests.length > 0 && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-4">
          <p className="text-xs font-semibold text-foreground/50 uppercase tracking-wide mb-2">{t('Interests')}</p>
          <div className="flex flex-wrap gap-2">
            {profile.interests.map(function(i) {
              return (
                <span key={i.id} className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                  {i.name}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {profile.links && Object.keys(profile.links).length > 0 && (
        <div className="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-1 text-sm">
          {profile.links.linkedin && (
            <a href={withProtocol(profile.links.linkedin)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              LinkedIn
            </a>
          )}
          {profile.links.twitter && (
            <a href={withProtocol(profile.links.twitter)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              Twitter/X
            </a>
          )}
          {profile.links.scholar && (
            <a href={withProtocol(profile.links.scholar)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              {t('Google Scholar')}
            </a>
          )}
          {profile.links.website && (
            <a href={withProtocol(profile.links.website)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              {t('Website')}
            </a>
          )}
        </div>
      )}

      {!isOwnProfile && !reported && !showReport && (
        <div className="text-center">
          <button
            onClick={openReport}
            className="text-xs text-muted-foreground/60 hover:text-destructive transition-colors"
          >
            {t('Report profile')}
          </button>
        </div>
      )}
      {!isOwnProfile && showReport && (
        <div className="space-y-2 pt-2 border-t border-border">
          <fieldset className="space-y-1">
            <legend className="text-sm font-medium text-foreground">{t("What's the problem?")}</legend>
            {profile.photo_url && (
              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="radio"
                  name="report-category"
                  checked={reportCategory === 'photo'}
                  onChange={function() { setReportCategory('photo'); }}
                />
                {t('Photo')}
              </label>
            )}
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="report-category"
                checked={reportCategory === 'profile'}
                onChange={function() { setReportCategory('profile'); }}
              />
              {t('Profile content')}
            </label>
          </fieldset>
          <textarea
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            rows={2}
            maxLength={1000}
            placeholder={t('Optional: describe the issue')}
            aria-label={t('Reason')}
            value={reportReason}
            onChange={function(e) { setReportReason(e.target.value); }}
          />
          {reportError && <p className="text-sm text-destructive">{reportError}</p>}
          <div className="flex gap-2">
            <button
              onClick={sendReport}
              disabled={reportSending}
              className="flex-1 py-1.5 rounded-lg bg-destructive text-white text-sm font-medium disabled:opacity-50"
            >
              {t('Send report')}
            </button>
            <button
              onClick={function() { setShowReport(false); }}
              disabled={reportSending}
              className="flex-1 py-1.5 rounded-lg border border-border text-sm text-foreground"
            >
              {t('Cancel')}
            </button>
          </div>
        </div>
      )}
      {reported && (
        <p className="text-xs text-muted-foreground text-center">{t("Thanks. The event's moderators will review this.")}</p>
      )}
    </div>
  );
}

export default ViewMemberProfile;
