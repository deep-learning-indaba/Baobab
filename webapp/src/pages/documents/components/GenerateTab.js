import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { profileService } from '../../../services/profilelist';
import { tagsService } from '../../../services/tags';
import { formServices } from '../../../services/form';
import { Card } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';

const STATUS_LABEL = {
  pending: 'Pending',
  generating: 'Generating...',
  generated: 'Generated',
  failed: 'Failed',
};

const FAILURE_REASON_LABEL = {
  required_form_not_submitted: 'Required form not submitted',
  no_matching_variant: "No template variant matches this person's tags",
  placeholder_resolution_failed: 'A placeholder could not be resolved',
};

function formName(form, t) {
  if (!form.name) return t('Untitled form');
  if (typeof form.name === 'string') return form.name;
  return form.name.en || Object.values(form.name)[0] || t('Untitled form');
}

const GenerateTab = ({ template, eventId }) => {
  const { t } = useTranslation();
  const [profiles, setProfiles] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [overrideEligibility, setOverrideEligibility] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [actionError, setActionError] = useState(null);
  const [busyDocumentId, setBusyDocumentId] = useState(null);

  // Bulk generation
  const [tags, setTags] = useState([]);
  const [forms, setForms] = useState([]);
  const [recipientType, setRecipientType] = useState('everyone');
  const [recipientTagId, setRecipientTagId] = useState('');
  const [recipientFormId, setRecipientFormId] = useState('');
  const [recipientEmails, setRecipientEmails] = useState('');
  const [bulkOverrideEligibility, setBulkOverrideEligibility] = useState(false);
  const [preflight, setPreflight] = useState(null);
  const [preflighting, setPreflighting] = useState(false);
  const [bulkGenerating, setBulkGenerating] = useState(false);
  const [bulkError, setBulkError] = useState(null);
  const [activeJob, setActiveJob] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => {
    profileService.getProfilesList(eventId).then((result) => {
      setProfiles(result.List || []);
    });
    tagsService.getTagList(eventId, 'en').then((result) => {
      setTags((result.tags || []).filter((tag) => tag.active));
    });
    formServices.getFormList(eventId).then((result) => {
      setForms(result.forms || []);
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

  // Poll the active job's status every 3s until it's no longer running, then
  // refresh the results table so newly-generated rows show up without a
  // manual reload.
  useEffect(() => {
    if (!activeJob) return undefined;
    const isDone = activeJob.status === 'completed' || activeJob.status === 'completed_with_errors';
    if (isDone) {
      loadDocuments();
      return undefined;
    }
    pollRef.current = setTimeout(() => {
      documentsService.getGenerationJob(activeJob.id).then((result) => {
        if (!result.error) setActiveJob(result.data);
      });
    }, 3000);
    return () => clearTimeout(pollRef.current);
  }, [activeJob, loadDocuments]);

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

  const buildRecipientSelection = () => {
    if (recipientType === 'everyone') return { type: 'everyone' };
    if (recipientType === 'tag') return { type: 'tag', tag_id: parseInt(recipientTagId, 10) };
    if (recipientType === 'form_submitted') return { type: 'form_submitted', form_id: parseInt(recipientFormId, 10) };
    if (recipientType === 'emails') {
      return { type: 'emails', emails: recipientEmails.split(/[\n,]/).map((e) => e.trim()).filter(Boolean) };
    }
    return { type: 'everyone' };
  };

  const recipientSelectionIsReady = () => {
    if (recipientType === 'tag') return !!recipientTagId;
    if (recipientType === 'form_submitted') return !!recipientFormId;
    if (recipientType === 'emails') return recipientEmails.trim().length > 0;
    return true;
  };

  const handlePreflight = () => {
    setPreflighting(true);
    setBulkError(null);
    setPreflight(null);
    documentsService.preflightGenerate(template.id, buildRecipientSelection(), {
      override_eligibility: bulkOverrideEligibility,
    }).then((result) => {
      setPreflighting(false);
      if (result.error) {
        setBulkError(result.error);
        return;
      }
      setPreflight(result.data);
    });
  };

  const handleBulkGenerate = () => {
    setBulkGenerating(true);
    setBulkError(null);
    documentsService.bulkGenerate(template.id, buildRecipientSelection(), {
      override_eligibility: bulkOverrideEligibility,
    }).then((result) => {
      setBulkGenerating(false);
      if (result.error) {
        setBulkError(result.error);
        return;
      }
      setActiveJob(result.data);
      setPreflight(null);
    });
  };

  const handleDownload = (doc) => {
    documentsService.downloadDocument(doc.id, doc.filename);
  };

  const handleResend = (doc) => {
    setActionError(null);
    setBusyDocumentId(doc.id);
    documentsService.resendDocument(doc.id).then((result) => {
      setBusyDocumentId(null);
      if (result.error) setActionError(result.error);
    });
  };

  const handleRegenerate = (doc) => {
    setActionError(null);
    setBusyDocumentId(doc.id);
    documentsService.regenerateDocument(doc.id).then((result) => {
      setBusyDocumentId(null);
      if (result.error) {
        setActionError(result.error);
        return;
      }
      loadDocuments();
    });
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
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Generate for many')}</h3>
        {bulkError && <p className="text-sm text-error mb-3">{bulkError}</p>}

        <div className="flex gap-2 items-center flex-wrap mb-2">
          <select
            className="rounded-lg border border-border px-3 py-2 text-sm"
            value={recipientType}
            onChange={(e) => { setRecipientType(e.target.value); setPreflight(null); }}
          >
            <option value="everyone">{t('Everyone eligible')}</option>
            <option value="tag">{t('By tag')}</option>
            <option value="form_submitted">{t('Who submitted a form')}</option>
            <option value="emails">{t('Specific people (paste emails)')}</option>
          </select>

          {recipientType === 'tag' && (
            <select
              className="rounded-lg border border-border px-3 py-2 text-sm min-w-[180px]"
              value={recipientTagId}
              onChange={(e) => { setRecipientTagId(e.target.value); setPreflight(null); }}
            >
              <option value="">{t('Choose a tag...')}</option>
              {tags.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
            </select>
          )}

          {recipientType === 'form_submitted' && (
            <select
              className="rounded-lg border border-border px-3 py-2 text-sm min-w-[180px]"
              value={recipientFormId}
              onChange={(e) => { setRecipientFormId(e.target.value); setPreflight(null); }}
            >
              <option value="">{t('Choose a form...')}</option>
              {forms.map((form) => <option key={form.id} value={form.id}>{formName(form, t)}</option>)}
            </select>
          )}
        </div>

        {recipientType === 'emails' && (
          <textarea
            className="w-full rounded-lg border border-border px-3 py-2 text-sm mb-2"
            rows={3}
            placeholder={t('One email per line, or comma-separated')}
            value={recipientEmails}
            onChange={(e) => { setRecipientEmails(e.target.value); setPreflight(null); }}
          />
        )}

        <label className="flex items-center gap-2 mb-3 text-xs text-muted-foreground">
          <input type="checkbox" checked={bulkOverrideEligibility}
                 onChange={(e) => { setBulkOverrideEligibility(e.target.checked); setPreflight(null); }} />
          {t('Include people who don\'t match the eligibility rule')}
        </label>

        <div className="flex items-center gap-2 mb-4">
          <Button variant="secondary" onClick={handlePreflight} disabled={preflighting || !recipientSelectionIsReady()}>
            {preflighting ? t('Checking...') : t('Check who will get a document')}
          </Button>
          {preflight && (
            <Button
              onClick={handleBulkGenerate}
              disabled={bulkGenerating || preflight.will_succeed_count === 0}
            >
              {bulkGenerating ? t('Starting...') : t('Generate {{count}} documents', { count: preflight.will_succeed_count })}
            </Button>
          )}
        </div>

        {preflight && (
          <div className="rounded-lg border border-border p-4 text-sm space-y-2 mb-4">
            <p>{preflight.total_candidates} {t('people selected.')}</p>
            <p className="text-success">✅ {preflight.will_succeed_count} {t('will succeed')}</p>
            {preflight.will_fail_count > 0 && (
              <div>
                <p className="text-error">⛔ {preflight.will_fail_count} {t('will fail')}</p>
                <ul className="list-disc list-inside text-xs text-muted-foreground ml-2">
                  {Object.entries(
                    preflight.failures.reduce((acc, f) => {
                      acc[f.reason] = (acc[f.reason] || 0) + 1;
                      return acc;
                    }, {})
                  ).map(([reason, count]) => (
                    <li key={reason}>{count} {t(FAILURE_REASON_LABEL[reason] || reason)}</li>
                  ))}
                </ul>
              </div>
            )}
            {preflight.excluded_ineligible_count > 0 && (
              <p className="text-xs text-muted-foreground">
                {t('{{count}} excluded as ineligible (not counted as failures).', { count: preflight.excluded_ineligible_count })}
              </p>
            )}
            {preflight.recommended_incomplete_count > 0 && (
              <p className="text-xs text-muted-foreground">
                ℹ️ {t('{{count}} have not completed a recommended form (will not block).', { count: preflight.recommended_incomplete_count })}
              </p>
            )}
          </div>
        )}

        {activeJob && (
          <div className="rounded-lg border border-border p-4 text-sm">
            <p className="font-semibold text-foreground mb-1">
              {t('Job')} #{activeJob.id} — {t(activeJob.status)}
            </p>
            <p className="text-muted-foreground">
              {activeJob.succeeded_count} {t('succeeded')}, {activeJob.failed_count} {t('failed')}, {activeJob.pending_count} {t('pending')}
              {' '}({t('of')} {activeJob.total_count})
            </p>
          </div>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Generated documents')}</h3>
        {actionError && <p className="text-sm text-error mb-3">{actionError}</p>}
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
                    <div className="flex items-center gap-1 justify-end">
                      {doc.status === 'generated' && (
                        <>
                          <Button variant="ghost" size="sm" onClick={() => handleDownload(doc)}>{t('Download')}</Button>
                          <Button variant="ghost" size="sm" disabled={busyDocumentId === doc.id}
                                  onClick={() => handleResend(doc)}>{t('Resend')}</Button>
                        </>
                      )}
                      {(doc.status === 'generated' || doc.status === 'failed') && (
                        <Button variant="ghost" size="sm" disabled={busyDocumentId === doc.id}
                                onClick={() => handleRegenerate(doc)}>{t('Regenerate')}</Button>
                      )}
                    </div>
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
