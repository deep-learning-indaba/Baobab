import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { profileService } from '../../services/profilelist';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Loading from '../../components/Loading';

/**
 * Admin-assigned key/value data per attendee (design section 9.8) - the
 * source for placeholders no form asks about, e.g. a room allocation. A
 * simple table for phase 1; CSV import for bulk allocation is a follow-up.
 */
const UserDataAdmin = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);

  const [rows, setRows] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newUserId, setNewUserId] = useState('');
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    if (!event) return;
    setLoading(true);
    documentsService.getUserEventData(event.id).then((result) => {
      setRows(result.data || []);
      setError(result.error || null);
      setLoading(false);
    });
  }, [event]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (event) profileService.getProfilesList(event.id).then((result) => setProfiles(result.List || []));
  }, [event]);

  const profileFor = (userId) => profiles.find((p) => p.user_id === userId);

  const handleAdd = () => {
    if (!newUserId || !newKey.trim()) return;
    setSaving(true);
    documentsService.setUserEventData(event.id, [
      { user_id: parseInt(newUserId, 10), key: newKey.trim(), value: newValue },
    ]).then((result) => {
      setSaving(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setNewKey('');
      setNewValue('');
      load();
    });
  };

  const handleEditValue = (row, value) => {
    documentsService.setUserEventData(event.id, [
      { user_id: row.user_id, key: row.key, value },
    ]).then((result) => {
      if (!result.error) load();
    });
  };

  if (!event) return <Loading />;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <button
        className="text-sm text-action hover:underline mb-2"
        onClick={() => props.history.push(`/${eventKey}/documentsAdmin`)}
      >
        ← {t('Back to Documents')}
      </button>
      <h1 className="font-heading text-2xl font-semibold text-foreground mb-1">{t('Attendee data')}</h1>
      <p className="text-sm text-muted-foreground mb-6">
        {t('Key/value facts about an attendee that no form asks for - e.g. a room allocation - referenced in document templates as {data.key}.')}
      </p>

      {error && <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>}

      <Card className="p-5 mb-6">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Add a value')}</h3>
        <div className="flex gap-2 flex-wrap items-center">
          <select
            className="rounded-lg border border-border px-3 py-2 text-sm min-w-[200px]"
            value={newUserId}
            onChange={(e) => setNewUserId(e.target.value)}
          >
            <option value="">{t('Choose a person...')}</option>
            {profiles.map((p) => (
              <option key={p.user_id} value={p.user_id}>{p.firstname} {p.lastname} ({p.email})</option>
            ))}
          </select>
          <input
            className="rounded-lg border border-border px-3 py-2 text-sm w-32"
            placeholder={t('key, e.g. hostel')}
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
          />
          <input
            className="rounded-lg border border-border px-3 py-2 text-sm flex-1 min-w-[160px]"
            placeholder={t('value')}
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
          />
          <Button onClick={handleAdd} disabled={saving || !newUserId || !newKey.trim()}>
            {t('Save')}
          </Button>
        </div>
      </Card>

      {loading ? (
        <Loading />
      ) : rows.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">{t('No attendee data set yet.')}</Card>
      ) : (
        <Card className="p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border bg-surface-low">
                <th className="py-2 px-4">{t('Person')}</th>
                <th className="py-2 px-4">{t('Key')}</th>
                <th className="py-2 px-4">{t('Value')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const profile = profileFor(row.user_id);
                return (
                  <tr key={row.id} className="border-b border-border/50">
                    <td className="py-2 px-4">{profile ? `${profile.firstname} ${profile.lastname}` : row.user_id}</td>
                    <td className="py-2 px-4 font-mono text-xs">{row.key}</td>
                    <td className="py-2 px-4">
                      <input
                        className="rounded-md border border-border px-2 py-1 text-sm w-full"
                        defaultValue={row.value || ''}
                        onBlur={(e) => {
                          if (e.target.value !== (row.value || '')) handleEditValue(row, e.target.value);
                        }}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};

export default UserDataAdmin;
