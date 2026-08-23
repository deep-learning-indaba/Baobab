import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../../services/documents';
import { Button } from '../../../components/ui/button';
import TagExpressionBuilder from './TagExpressionBuilder';
import TranslatableFieldGroup from '../../formEditor/components/TranslatableFieldGroup';

const FIELD = 'w-full rounded-lg border border-border px-3 py-2 text-sm';
const LABEL = 'block text-sm font-semibold text-foreground mb-1';

function translationValues(template, field, languages) {
  return languages.reduce((acc, lang) => {
    acc[lang.code] = (template && template.translations[lang.code] && template.translations[lang.code][field]) || '';
    return acc;
  }, {});
}

const DetailsTab = ({ template, isNew, eventId, languages, autoTranslateEnabled, tags, onCreated, onSaved }) => {
  const { t } = useTranslation();
  const [key, setKey] = useState(template ? template.key : '');
  const [name, setName] = useState(() => translationValues(template, 'name', languages));
  const [description, setDescription] = useState(() => translationValues(template, 'description', languages));
  const [instructions, setInstructions] = useState(() => translationValues(template, 'instructions', languages));
  const [selfService, setSelfService] = useState(template ? template.self_service : false);
  const [deliveryMode, setDeliveryMode] = useState(template ? template.delivery_mode : 'attachment');
  const [emailTemplateKey, setEmailTemplateKey] = useState(template ? template.email_template_key || '' : '');
  const [filenamePattern, setFilenamePattern] = useState(template ? template.filename_pattern || '' : '');
  const [allowBlankValues, setAllowBlankValues] = useState(template ? template.allow_blank_values : false);
  const [eligibilityExpression, setEligibilityExpression] = useState(template ? template.eligibility_expression : null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const primaryLang = languages[0] && languages[0].code;

  const buildPayload = () => {
    const translations = {};
    languages.forEach((lang) => {
      translations[lang.code] = {
        name: (name[lang.code] || '').trim() || (lang.code === primaryLang ? key.trim() : name[primaryLang]),
        description: (description[lang.code] || '').trim(),
        instructions: (instructions[lang.code] || '').trim(),
      };
    });
    return {
      key: key.trim(),
      self_service: selfService,
      delivery_mode: deliveryMode,
      email_template_key: emailTemplateKey.trim() || null,
      filename_pattern: filenamePattern.trim() || null,
      allow_blank_values: allowBlankValues,
      eligibility_expression: eligibilityExpression,
      translations,
    };
  };

  const handleSave = () => {
    if (!key.trim()) {
      setError(t('A key is required.'));
      return;
    }
    if (!(name[primaryLang] || '').trim()) {
      setError(t('A name is required.'));
      return;
    }
    setSaving(true);
    setError(null);

    const payload = buildPayload();
    const call = isNew
      ? documentsService.createTemplate(eventId, payload)
      : documentsService.updateTemplate(template.id, payload);

    call.then((result) => {
      setSaving(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      if (isNew) {
        onCreated(result.data);
      } else {
        onSaved(result.data);
      }
    });
  };

  return (
    <div className="space-y-2 max-w-3xl">
      {error && (
        <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      )}

      <div className="mb-6">
        <label className={LABEL}>{t('Key')}</label>
        <input className={FIELD} value={key} onChange={(e) => setKey(e.target.value)}
               placeholder="invitation-letter" />
        <p className="text-xs text-muted-foreground mt-1">
          {t('A short, stable identifier. Not shown to attendees.')}
        </p>
      </div>

      <TranslatableFieldGroup
        label={t('Name')}
        fieldName="name"
        values={name}
        languages={languages}
        onChange={(lang, value) => setName((prev) => ({ ...prev, [lang]: value }))}
        required
        autoTranslateEnabled={autoTranslateEnabled}
      />

      <TranslatableFieldGroup
        label={t('Description')}
        fieldName="description"
        values={description}
        languages={languages}
        onChange={(lang, value) => setDescription((prev) => ({ ...prev, [lang]: value }))}
        multiline
        autoTranslateEnabled={autoTranslateEnabled}
      />

      <TranslatableFieldGroup
        label={t('Instructions shown to the attendee')}
        fieldName="instructions"
        values={instructions}
        languages={languages}
        onChange={(lang, value) => setInstructions((prev) => ({ ...prev, [lang]: value }))}
        multiline
        autoTranslateEnabled={autoTranslateEnabled}
        placeholder={t('e.g. Your letter will be addressed to the embassy named in your registration form.')}
      />

      <div className="flex items-center gap-2 mt-4">
        <input type="checkbox" id="self_service" checked={selfService} onChange={(e) => setSelfService(e.target.checked)} />
        <label htmlFor="self_service" className="text-sm text-foreground">
          {t('Attendees can request this themselves')}
        </label>
      </div>
      <p className="text-xs text-muted-foreground ml-6 mb-4">
        {t('Turn this off for documents an admin generates on the attendee\'s behalf, like a certificate issued after the event.')}
      </p>

      <div className="mb-6">
        <label className={LABEL}>{t('Delivery')}</label>
        <select className={FIELD} value={deliveryMode} onChange={(e) => setDeliveryMode(e.target.value)}>
          <option value="attachment">{t('Email as an attachment')}</option>
          <option value="none">{t('Download only, no email')}</option>
        </select>
      </div>

      {deliveryMode === 'attachment' && (
        <div className="mb-6">
          <label className={LABEL}>{t('Email template key')}</label>
          <input className={FIELD} value={emailTemplateKey} onChange={(e) => setEmailTemplateKey(e.target.value)}
                 placeholder="generated-document" />
          <p className="text-xs text-muted-foreground mt-1">
            {t('Matches the key of an Email Template configured for this event. Leave blank to use the default.')}
          </p>
        </div>
      )}

      <div className="mb-6">
        <label className={LABEL}>{t('Filename pattern')}</label>
        <input className={FIELD} value={filenamePattern} onChange={(e) => setFilenamePattern(e.target.value)}
               placeholder="{lastname}_{firstname}_Certificate.pdf" />
      </div>

      <div className="flex items-center gap-2 mb-6">
        <input type="checkbox" id="allow_blank" checked={allowBlankValues} onChange={(e) => setAllowBlankValues(e.target.checked)} />
        <label htmlFor="allow_blank" className="text-sm text-foreground">
          {t('Allow blank values instead of failing when a placeholder has no value for someone')}
        </label>
      </div>

      <div className="mb-6">
        <label className={LABEL}>{t('Who can receive this document')}</label>
        <p className="text-xs text-muted-foreground mb-2">
          {t('Leave empty to make it available to everyone.')}
        </p>
        <TagExpressionBuilder expression={eligibilityExpression} onChange={setEligibilityExpression} tags={tags} />
      </div>

      <div className="pt-2">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? t('Saving...') : (isNew ? t('Create document') : t('Save changes'))}
        </Button>
      </div>
    </div>
  );
};

export default DetailsTab;
