import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { Card } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import TagExpressionBuilder from './TagExpressionBuilder';

// `body` is a function rather than a plain string for the three statuses whose
// remediation normally involves sharing with the service account: when this
// environment has none configured (see google_client.describe_configured_identity),
// "share it with the address below" would dangle - there's no address shown.
const ACCESS_COPY = {
  not_found: {
    title: "Baobab can't open this document.",
    body: (hasServiceAccount) => (hasServiceAccount
      ? 'Share it with Baobab\'s service account (Viewer is enough), or set link sharing to "Anyone with the link → Viewer", then check again.'
      : 'Set link sharing to "Anyone with the link → Viewer", then check again.'),
  },
  no_permission: {
    title: "Baobab doesn't have permission to open this document.",
    body: (hasServiceAccount) => (hasServiceAccount
      ? 'Share it with the service account address below, or set link sharing to "Anyone with the link → Viewer". If it\'s in a Shared Drive, the service account needs to be a member of that drive.'
      : 'Set link sharing to "Anyone with the link → Viewer", then check again.'),
  },
  copy_disabled: {
    title: 'This document has copying turned off for viewers.',
    body: (hasServiceAccount) => (hasServiceAccount
      ? 'Share it with the service account as Editor, or untick "Viewers can\'t copy" in Share → Settings.'
      : 'Untick "Viewers can\'t copy" in Share → Settings.'),
  },
  wrong_type: {
    title: "This isn't a Google Doc or Slides file.",
    body: () => 'If it was uploaded (e.g. a .docx or .pptx), open it and choose File → "Save as Google Docs" or "Save as Google Slides", then paste the new link.',
  },
  error: {
    title: 'Something went wrong checking this document.',
    body: () => 'Try again in a moment.',
  },
};

const VariantsTab = ({ template, eventId, onReload, tags }) => {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [checking, setChecking] = useState(false);
  const [checkResult, setCheckResult] = useState(null);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);

  const handleCheck = () => {
    if (!url.trim()) return;
    setChecking(true);
    setCheckResult(null);
    setError(null);
    documentsService.validateSource(eventId, url.trim()).then((result) => {
      setChecking(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setCheckResult(result.data);
    });
  };

  const handleAdd = () => {
    setAdding(true);
    setError(null);
    documentsService.addVariant(template.id, {
      google_file_url: url.trim(),
      name: name.trim() || (checkResult && checkResult.file_name) || 'Default',
    }).then((result) => {
      setAdding(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setUrl('');
      setName('');
      setCheckResult(null);
      onReload();
    });
  };

  const handleVariantChange = (variant, field, value) => {
    documentsService.updateVariant(template.id, variant.id, { [field]: value }).then((result) => {
      if (!result.error) onReload();
    });
  };

  const handleDeleteVariant = (variant) => {
    documentsService.deleteVariant(template.id, variant.id).then((result) => {
      if (!result.error) onReload();
    });
  };

  const activeVariants = (template.variants || []).filter((v) => v.is_active);
  const hasCatchAll = activeVariants.some((v) => !v.selection_expression);

  return (
    <div className="space-y-6 max-w-3xl">
      <Card className="p-5">
        <h3 className="font-heading font-semibold text-foreground mb-3">{t('Add a template file')}</h3>
        <div className="flex gap-2">
          <input
            className="flex-1 rounded-lg border border-border px-3 py-2 text-sm"
            placeholder={t('Paste a Google Docs or Slides link')}
            value={url}
            onChange={(e) => { setUrl(e.target.value); setCheckResult(null); }}
          />
          <Button variant="secondary" onClick={handleCheck} disabled={checking || !url.trim()}>
            {checking ? t('Checking...') : t('Check')}
          </Button>
        </div>

        {error && <p className="text-sm text-error mt-3">{error}</p>}

        {checkResult && checkResult.status !== 'ok' && (
          <div className="mt-4 rounded-lg border border-warning/30 bg-warning/5 p-4 text-sm space-y-2">
            <p className="font-semibold text-foreground">{t(ACCESS_COPY[checkResult.status]?.title || 'Baobab can\'t use this document.')}</p>
            <p className="text-muted-foreground">
              {t(ACCESS_COPY[checkResult.status]?.body(checkResult.has_configured_service_account) || '')}
            </p>
            {checkResult.service_account_email && (
              <div className="flex items-center gap-2">
                <code className="text-xs bg-surface-low rounded px-2 py-1">{checkResult.service_account_email}</code>
                <Button
                  variant="ghost" size="sm"
                  onClick={() => navigator.clipboard && navigator.clipboard.writeText(checkResult.service_account_email)}
                >
                  {t('Copy')}
                </Button>
              </div>
            )}
            {!checkResult.has_configured_service_account && (
              <p className="text-xs text-muted-foreground italic">
                {t('No dedicated service account is configured in this environment - access checks are using whatever local Google credentials happen to be available, which usually can\'t see your documents. This is expected in local development; it will use a real service account once deployed.')}
              </p>
            )}
            <Button variant="secondary" size="sm" onClick={handleCheck}>{t('Check again')}</Button>
          </div>
        )}

        {checkResult && checkResult.status === 'ok' && (
          <div className="mt-4 rounded-lg border border-success/30 bg-success/5 p-4 text-sm space-y-3">
            <p className="text-foreground">
              ✅ {t('Connected to')} <strong>{checkResult.file_name}</strong> ({checkResult.file_type === 'presentation' ? t('Google Slides') : t('Google Docs')})
              {' — '}{(checkResult.detected_placeholders || []).length} {t('placeholder(s) found')}
            </p>
            {checkResult.detected_placeholders && checkResult.detected_placeholders.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {checkResult.detected_placeholders.map((p) => `{${p}}`).join(', ')}
              </p>
            )}
            <div className="flex gap-2 items-center">
              <input
                className="flex-1 rounded-lg border border-border px-3 py-2 text-sm"
                placeholder={t('Variant name, e.g. "Travel + accommodation"')}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <Button onClick={handleAdd} disabled={adding}>
                {adding ? t('Adding...') : t('Add as a variant')}
              </Button>
            </div>
          </div>
        )}
      </Card>

      {!hasCatchAll && activeVariants.length > 0 && (
        <div className="rounded-lg border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-warning">
          {t('No fallback variant. Attendees whose tags match none of the rules below will get an error when they request this document.')}
        </div>
      )}

      <div className="space-y-3">
        {(template.variants || []).map((variant) => (
          <Card key={variant.id} className={'p-4 ' + (variant.is_active ? '' : 'opacity-60')}>
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground">{variant.name}</span>
                  <span className={'text-xs rounded-full px-2 py-0.5 ' + (variant.access_status === 'ok' ? 'bg-success/10 text-success' : 'bg-error/10 text-error')}>
                    {variant.access_status === 'ok' ? t('Accessible') : t('Access issue')}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{variant.google_file_name || variant.google_file_id}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => handleVariantChange(variant, 'is_active', !variant.is_active)}>
                  {variant.is_active ? t('Deactivate') : t('Activate')}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDeleteVariant(variant)}>{t('Remove')}</Button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-foreground mb-1">{t('Language')}</label>
                <select
                  className="w-full rounded-md border border-border px-2 py-1.5 text-sm"
                  value={variant.language || ''}
                  onChange={(e) => handleVariantChange(variant, 'language', e.target.value || null)}
                >
                  <option value="">{t('Any language')}</option>
                  <option value="en">{t('English')}</option>
                  <option value="fr">{t('French')}</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-foreground mb-1">{t('Priority (higher tried first)')}</label>
                <input
                  type="number"
                  className="w-full rounded-md border border-border px-2 py-1.5 text-sm"
                  value={variant.priority}
                  onChange={(e) => handleVariantChange(variant, 'priority', parseInt(e.target.value, 10) || 0)}
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-xs font-semibold text-foreground mb-1">{t('Who gets this variant')}</label>
              <TagExpressionBuilder
                expression={variant.selection_expression}
                onChange={(expr) => handleVariantChange(variant, 'selection_expression', expr)}
                tags={tags}
              />
            </div>

            {variant.detected_placeholders && variant.detected_placeholders.length > 0 && (
              <p className="text-xs text-muted-foreground mt-3">
                {t('Placeholders')}: {variant.detected_placeholders.map((p) => `{${p}}`).join(', ')}
              </p>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};

export default VariantsTab;
