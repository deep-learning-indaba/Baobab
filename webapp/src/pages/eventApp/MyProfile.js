import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Select from 'react-select';
import { profileService } from '../../services/eventApp/profile.service';

function MyProfile(props) {
  const event = props.event;
  const { t } = useTranslation();

  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [availableInterests, setAvailableInterests] = useState([]);

  const [headline, setHeadline] = useState('');
  const [about, setAbout] = useState('');
  const [pronouns, setPronouns] = useState('');
  const [namePronunciation, setNamePronunciation] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');
  const [affiliation, setAffiliation] = useState('');
  const [visibility, setVisibility] = useState('community');
  const [selectedInterests, setSelectedInterests] = useState([]);
  const [links, setLinks] = useState({ linkedin: '', twitter: '', scholar: '', website: '' });

  const eventId = event && event.id;

  useEffect(function() {
    if (!eventId) {
      setIsLoading(false);
      return;
    }
    Promise.all([
      profileService.getMyProfile(eventId),
      profileService.getInterests(eventId),
    ]).then(function(results) {
      const profileResult = results[0];
      const interestsResult = results[1];
      if (profileResult.error) {
        setError(profileResult.error);
      } else {
        const p = profileResult.data;
        setProfile(p);
        setHeadline(p.headline || '');
        setAbout(p.about || '');
        setPronouns(p.pronouns || '');
        setNamePronunciation(p.name_pronunciation || '');
        setCity(p.city || '');
        setCountry(p.country || '');
        setAffiliation(p.affiliation || '');
        setVisibility(p.visibility || 'community');
        setSelectedInterests((p.interests || []).map(function(i) {
          return { value: i.id, label: i.name };
        }));
        setLinks(Object.assign({ linkedin: '', twitter: '', scholar: '', website: '' }, p.links || {}));
      }
      if (!interestsResult.error) {
        setAvailableInterests((interestsResult.data || []).map(function(i) {
          return { value: i.id, label: i.name };
        }));
      }
      setIsLoading(false);
    });
  }, [eventId]);

  const handleLinkChange = useCallback(function(key, value) {
    setLinks(function(prev) {
      return Object.assign({}, prev, { [key]: value });
    });
  }, []);

  const handleInterestCreate = useCallback(function(inputValue) {
    profileService.createInterest(eventId, inputValue).then(function(result) {
      if (!result.error) {
        const newOpt = { value: result.data.id, label: result.data.name };
        setAvailableInterests(function(prev) { return prev.concat([newOpt]); });
        setSelectedInterests(function(prev) { return prev.concat([newOpt]); });
      }
    });
  }, [eventId]);

  const handleSave = useCallback(function() {
    setIsSaving(true);
    setSaveSuccess(false);
    setError(null);
    const linksClean = {};
    Object.keys(links).forEach(function(k) {
      if (links[k]) {
        linksClean[k] = links[k];
      }
    });
    const payload = {
      event_id: eventId,
      headline: headline,
      about: about,
      pronouns: pronouns,
      name_pronunciation: namePronunciation,
      city: city,
      country: country,
      affiliation: affiliation,
      visibility: visibility,
      interest_ids: selectedInterests.map(function(o) { return o.value; }),
      links: linksClean,
    };
    profileService.updateMyProfile(payload).then(function(result) {
      setIsSaving(false);
      if (result.error) {
        setError(result.error);
      } else {
        setProfile(result.data);
        setSaveSuccess(true);
        setTimeout(function() { setSaveSuccess(false); }, 3000);
      }
    });
  }, [eventId, headline, about, pronouns, namePronunciation, city, country, affiliation, visibility, selectedInterests, links]);

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center py-8">
        <div className="spinner-border" role="status">
          <span className="sr-only">{t('Loading...')}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-6 px-4 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">{t('My Profile')}</h1>

      {profile && (
        <div className="bg-white rounded-2xl border border-border p-4 text-sm text-foreground/70">
          <p className="font-medium text-foreground">{profile.firstname} {profile.lastname}</p>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-border p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Headline')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            maxLength={160}
            value={headline}
            onChange={function(e) { setHeadline(e.target.value); }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('About me')}</label>
          <textarea
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            rows={4}
            maxLength={2000}
            value={about}
            onChange={function(e) { setAbout(e.target.value); }}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">{t('Pronouns')}</label>
            <input
              className="w-full border border-border rounded-lg px-3 py-2 text-sm"
              maxLength={40}
              value={pronouns}
              onChange={function(e) { setPronouns(e.target.value); }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">{t('Name pronunciation')}</label>
            <input
              className="w-full border border-border rounded-lg px-3 py-2 text-sm"
              maxLength={120}
              value={namePronunciation}
              onChange={function(e) { setNamePronunciation(e.target.value); }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">{t('City')}</label>
            <input
              className="w-full border border-border rounded-lg px-3 py-2 text-sm"
              maxLength={120}
              value={city}
              onChange={function(e) { setCity(e.target.value); }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">{t('Country')}</label>
            <input
              className="w-full border border-border rounded-lg px-3 py-2 text-sm"
              maxLength={120}
              value={country}
              onChange={function(e) { setCountry(e.target.value); }}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Affiliation')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            maxLength={255}
            value={affiliation}
            onChange={function(e) { setAffiliation(e.target.value); }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">{t('Interests')}</label>
          <Select
            isMulti
            options={availableInterests}
            value={selectedInterests}
            onChange={function(opts) { setSelectedInterests(opts || []); }}
            onCreateOption={handleInterestCreate}
            placeholder={t('Add interest')}
            classNamePrefix="react-select"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-foreground">{t('LinkedIn')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            placeholder="https://linkedin.com/in/..."
            value={links.linkedin}
            onChange={function(e) { handleLinkChange('linkedin', e.target.value); }}
          />
          <label className="block text-sm font-medium text-foreground">{t('Twitter/X')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            placeholder="https://x.com/..."
            value={links.twitter}
            onChange={function(e) { handleLinkChange('twitter', e.target.value); }}
          />
          <label className="block text-sm font-medium text-foreground">{t('Google Scholar')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            placeholder="https://scholar.google.com/..."
            value={links.scholar}
            onChange={function(e) { handleLinkChange('scholar', e.target.value); }}
          />
          <label className="block text-sm font-medium text-foreground">{t('Website')}</label>
          <input
            className="w-full border border-border rounded-lg px-3 py-2 text-sm"
            placeholder="https://..."
            value={links.website}
            onChange={function(e) { handleLinkChange('website', e.target.value); }}
          />
        </div>

        <div className="flex items-center gap-3">
          <input
            id="visibility-toggle"
            type="checkbox"
            className="rounded"
            checked={visibility === 'community'}
            onChange={function(e) { setVisibility(e.target.checked ? 'community' : 'hidden'); }}
          />
          <label htmlFor="visibility-toggle" className="text-sm text-foreground">
            {t('Show my profile to other attendees')}
          </label>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {saveSuccess && <div className="alert alert-success">{t('Profile saved')}</div>}

      <button
        className="w-full px-5 py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container transition-all"
        onClick={handleSave}
        disabled={isSaving}
      >
        {isSaving ? t('Saving...') : t('Save profile')}
      </button>
    </div>
  );
}

export default MyProfile;
