import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { profileService } from '../../services/eventApp/profile.service';

function ViewMemberProfile(props) {
  const event = props.event;
  const userId = props.match && props.match.params && props.match.params.userId;
  const { t } = useTranslation();

  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

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
          {profile.photo_url && (
            <img src={profile.photo_url} alt="" className="w-20 h-20 rounded-full object-cover" />
          )}
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
        {profile.photo_url && (
          <img src={profile.photo_url} alt="" className="w-24 h-24 rounded-full object-cover" />
        )}
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
            <a href={profile.links.linkedin} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              LinkedIn
            </a>
          )}
          {profile.links.twitter && (
            <a href={profile.links.twitter} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              Twitter/X
            </a>
          )}
          {profile.links.scholar && (
            <a href={profile.links.scholar} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              {t('Google Scholar')}
            </a>
          )}
          {profile.links.website && (
            <a href={profile.links.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-primary hover:underline">
              {t('Website')}
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default ViewMemberProfile;
