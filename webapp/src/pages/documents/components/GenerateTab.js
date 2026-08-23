import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { profileService } from '../../../services/profilelist';
import { Card } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';

const STATUS_LABEL = {
  pending: 'Pending',
  generating: 'Generating...',
  generated: 'Generated',
  failed: 'Failed',
};

const GenerateTab = ({ template, eventId }) => {
  const { t } = useTranslation();
  const [profiles, setProfiles] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [overrideEligibility, setOverrideEligibility] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);

  useEffect(() => {
    profileService.getProfilesList(eventId).then((result) => {
      setProfiles(result.List || []);
    });
  }, [eventId]);

  const loadDocuments = useCallback(() => {
    setLoadingDocuments(true);
    documentsService.getGeneratedDocuments(eventId, template.id).then((result) => {
      setDocuments(result.data || []);
      setLoadingDocuments(false);
    });
  }, [eventId, template.id]);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  const handleGenerate = () => {
    if (!selectedUserId) return;
    setGenerating(true);
    setError(null);
    documentsService.generateDocument(template.id, parseInt(selectedUserId, 10), {
      override_eligibility: overrideEligibility,
    }).then((result) => {
      setGenerating(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      loadDocuments();
    });
  };

  const handleDownload = (doc) => {
    documentsService.downloadDocument(doc.id, doc.filename);
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <Card className="p-5">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Generate for someone')}</h3>
        {error && <p className="text-sm text-error mb-3">{error}</p>}
        <div className="flex gap-2 items-center flex-wrap">
          <select
            className="flex-1 min-w-[220px] rounded-lg border border-border px-3 py-2 text-sm"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
          >
            <option value="">{t('Choose a person...')}</option>
            {profiles.map((p) => (
              <option key={p.user_id} value={p.user_id}>{p.firstname} {p.lastname} ({p.email})</option>
            ))}
          </select>
          <Button onClick={handleGenerate} disabled={!selectedUserId || generating}>
            {generating ? t('Generating...') : t('Generate')}
          </Button>
        </div>
        <label className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
          <input type="checkbox" checked={overrideEligibility} onChange={(e) => setOverrideEligibility(e.target.checked)} />
          {t('Generate even if this person doesn\'t match the eligibility rule')}
        </label>
      </Card>

      <Card className="p-5">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Generated documents')}</h3>
        {loadingDocuments ? (
          <p className="text-sm text-muted-foreground">{t('Loading...')}</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('Nothing generated yet.')}</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border">
                <th className="py-2 pr-4">{t('Filename')}</th>
                <th className="py-2 pr-4">{t('Status')}</th>
                <th className="py-2 pr-4">{t('Created')}</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-border/50">
                  <td className="py-2 pr-4">{doc.filename || '—'}</td>
                  <td className="py-2 pr-4">
                    {doc.status === 'failed' ? (
                      <span className="text-error" title={doc.error_detail}>{t(STATUS_LABEL[doc.status])}</span>
                    ) : (
                      t(STATUS_LABEL[doc.status] || doc.status)
                    )}
                  </td>
                  <td className="py-2 pr-4 text-muted-foreground">
                    {doc.created_at ? new Date(doc.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="py-2">
                    {doc.status === 'generated' && (
                      <Button variant="ghost" size="sm" onClick={() => handleDownload(doc)}>{t('Download')}</Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
};

export default GenerateTab;
