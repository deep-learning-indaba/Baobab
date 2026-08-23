import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { profileService } from '../../../services/profilelist';
import { Card } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';

const PlaceholdersTab = ({ template, eventId, onReload }) => {
  const { t } = useTranslation();
  const [analysing, setAnalysing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const [profiles, setProfiles] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [previewing, setPreviewing] = useState(false);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    profileService.getProfilesList(eventId).then((result) => {
      setProfiles(result.List || []);
    });
  }, [eventId]);

  const handleAnalyse = () => {
    setAnalysing(true);
    setError(null);
    documentsService.analyseTemplate(template.id).then((result) => {
      setAnalysing(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setAnalysis(result.data);
      onReload();
    });
  };

  const handlePreview = () => {
    if (!selectedUserId) return;
    setPreviewing(true);
    setPreview(null);
    documentsService.previewTemplate(template.id, parseInt(selectedUserId, 10)).then((result) => {
      setPreviewing(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setPreview(result.data);
    });
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {error && <div className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>}

      <Card className="p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-heading font-semibold text-foreground">{t('Placeholders')}</h3>
          <Button variant="secondary" size="sm" onClick={handleAnalyse} disabled={analysing}>
            {analysing ? t('Scanning...') : t('Rescan template files')}
          </Button>
        </div>

        {!analysis && (
          <p className="text-sm text-muted-foreground">
            {t('Rescan to see every placeholder used across this document\'s template files and where each one resolves from.')}
          </p>
        )}

        {analysis && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4">{t('Placeholder')}</th>
                  <th className="py-2 pr-4">{t('Tried in order')}</th>
                  <th className="py-2">{t('Status')}</th>
                </tr>
              </thead>
              <tbody>
                {analysis.placeholders.map((p) => (
                  <tr key={p.raw} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-mono text-xs">{`{${p.raw}}`}</td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {p.chain && p.chain.length > 0 ? p.chain.join(' → ') : t('(not from a linked form)')}
                    </td>
                    <td className="py-2">
                      {p.defined ? (
                        <span className="text-success">✅ {t('Resolvable')}</span>
                      ) : (
                        <span className="text-error">⛔ {t('Nothing defines this key')}</span>
                      )}
                    </td>
                  </tr>
                ))}
                {analysis.placeholders.length === 0 && (
                  <tr><td colSpan={3} className="py-3 text-muted-foreground">{t('No placeholders found in the active template files.')}</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Test with a real person')}</h3>
        <p className="text-xs text-muted-foreground mb-3">
          {t('Nothing is generated, stored, or emailed - this only shows what would happen.')}
        </p>
        <div className="flex gap-2 items-center">
          <select
            className="flex-1 rounded-lg border border-border px-3 py-2 text-sm"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
          >
            <option value="">{t('Choose a person...')}</option>
            {profiles.map((p) => (
              <option key={p.user_id} value={p.user_id}>{p.firstname} {p.lastname} ({p.email})</option>
            ))}
          </select>
          <Button onClick={handlePreview} disabled={!selectedUserId || previewing}>
            {previewing ? t('Checking...') : t('Preview')}
          </Button>
        </div>

        {preview && (
          <div className="mt-4 space-y-3 text-sm">
            <p>
              {t('Eligible')}: {preview.eligible ? '✅' : '⛔'}
              {preview.variant && <> — {t('would use variant')} <strong>{preview.variant.name}</strong></>}
              {preview.variant_error && <span className="text-error"> — {preview.variant_error}</span>}
            </p>

            {preview.blockers && preview.blockers.length > 0 && (
              <div className="rounded-lg border border-error/30 bg-error/5 p-3">
                <p className="font-semibold text-error mb-1">{t('Blocked')}:</p>
                {preview.blockers.map((b) => (
                  <p key={b.form_id} className="text-muted-foreground">{b.message || `${t('Must complete')} ${b.form_name}`}</p>
                ))}
              </div>
            )}
            {preview.prompts && preview.prompts.length > 0 && (
              <div className="rounded-lg border border-warning/30 bg-warning/5 p-3">
                <p className="font-semibold text-foreground mb-1">{t('Recommended (not blocking)')}:</p>
                {preview.prompts.map((p) => (
                  <p key={p.form_id} className="text-muted-foreground">{p.message || p.form_name}</p>
                ))}
              </div>
            )}

            {preview.resolution && (
              <div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted-foreground border-b border-border">
                      <th className="py-1 pr-4">{t('Key')}</th>
                      <th className="py-1 pr-4">{t('Value')}</th>
                      <th className="py-1">{t('Source')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(preview.resolution.values || {}).map(([key, info]) => (
                      <tr key={key} className="border-b border-border/50">
                        <td className="py-1 pr-4 font-mono text-xs">{key}</td>
                        <td className="py-1 pr-4">{info.value || <span className="text-muted-foreground italic">{t('blank')}</span>}</td>
                        <td className="py-1 text-muted-foreground">{info.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {preview.resolution.errors && preview.resolution.errors.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {preview.resolution.errors.map((e, i) => (
                      <p key={i} className="text-error text-xs">⛔ {e.message}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};

export default PlaceholdersTab;
