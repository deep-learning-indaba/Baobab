import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { profileService } from '../../services/eventApp/profile.service';

function ProfileBrowser(props) {
  const event = props.event;
  const { t } = useTranslation();

  const [profiles, setProfiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [filterInterest, setFilterInterest] = useState('');

  const eventId = event && event.id;
  const eventKey = event && event.key;

  useEffect(function() {
    if (!eventId) {
      setIsLoading(false);
      return;
    }
    profileService.listProfiles(eventId).then(function(result) {
      setIsLoading(false);
      if (result.error) {
        setError(result.error);
      } else {
        setProfiles(result.data || []);
      }
    });
  }, [eventId]);

  const allInterests = [];
  const interestSeen = {};
  profiles.forEach(function(p) {
    (p.interests || []).forEach(function(i) {
      if (!interestSeen[i.id]) {
        interestSeen[i.id] = true;
        allInterests.push(i);
      }
    });
  });

  const filtered = profiles.filter(function(p) {
    const name = (p.firstname + ' ' + p.lastname).toLowerCase();
    const matchesSearch = !search || name.indexOf(search.toLowerCase()) !== -1;
    const matchesInterest = !filterInterest || (p.interests || []).some(function(i) {
      return String(i.id) === filterInterest;
    });
    return matchesSearch && matchesInterest;
  });

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

  return (
    <div className="w-full max-w-5xl mx-auto pt-6 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">{t('Browse attendees')}</h1>

      <div className="flex gap-3 flex-wrap">
        <input
          className="flex-1 min-w-48 border border-border rounded-lg px-3 py-2 text-sm"
          placeholder={t('Search by name...')}
          value={search}
          onChange={function(e) { setSearch(e.target.value); }}
        />
        <select
          className="border border-border rounded-lg px-3 py-2 text-sm"
          value={filterInterest}
          onChange={function(e) { setFilterInterest(e.target.value); }}
        >
          <option value="">{t('Filter by interest')}</option>
          {allInterests.map(function(i) {
            return <option key={i.id} value={String(i.id)}>{i.name}</option>;
          })}
        </select>
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-foreground/60 py-4">{t('No attendees found.')}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {filtered.map(function(p) {
          return (
            <Link
              key={p.user_id}
              to={'/' + eventKey + '/app/profile/' + p.user_id}
              className="bg-white rounded-2xl border border-border shadow-sm p-4 flex gap-4 items-start hover:border-primary/50 transition-all"
            >
              {p.photo_url ? (
                <img src={p.photo_url} alt="" className="w-12 h-12 rounded-full object-cover flex-shrink-0" />
              ) : (
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 text-primary font-bold text-lg">
                  {p.firstname ? p.firstname[0] : '?'}
                </div>
              )}
              <div className="min-w-0">
                <p className="font-semibold text-foreground truncate">{p.firstname} {p.lastname}</p>
                {p.role && <p className="text-xs text-foreground/60">{p.role}</p>}
                {p.affiliation && <p className="text-xs text-foreground/50 truncate">{p.affiliation}</p>}
                {p.headline && <p className="text-xs text-foreground/70 mt-1 truncate">{p.headline}</p>}
                {p.interests && p.interests.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {p.interests.slice(0, 3).map(function(i) {
                      return (
                        <span key={i.id} className="px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary">
                          {i.name}
                        </span>
                      );
                    })}
                    {p.interests.length > 3 && (
                      <span className="text-xs text-foreground/40">+{p.interests.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default ProfileBrowser;
