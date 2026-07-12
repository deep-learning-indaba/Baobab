import React from 'react';

const QuestionSettingsEditor = ({ type, settings, onChange, languages, t }) => {
  const handleChange = (field, value) => onChange({ ...settings, [field]: value });

  const handleArrayChange = (field, valueString) => {
    const values = valueString.split(',').map(v => v.trim()).filter(v => v);
    handleChange(field, values);
  };

  const inputCls = "w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring";
  const labelCls = "block text-sm font-medium text-foreground mb-1";
  const fieldCls = "mb-4";

  const Wrapper = ({ title, children }) => (
    <div className="mt-4 p-4 bg-surface rounded-lg border border-border">
      <h4 className="text-sm font-semibold text-foreground mb-3">{title}</h4>
      {children}
    </div>
  );

  if (type === 'file' || type === 'multi-file') {
    return (
      <Wrapper title={t('File Settings')}>
        <div className={fieldCls}>
          <label className={labelCls}>{t('Accepted Extensions')}</label>
          <input
            type="text"
            value={(settings.accepted_extensions || []).join(', ')}
            onChange={(e) => handleArrayChange('accepted_extensions', e.target.value)}
            placeholder={t('e.g., .pdf, .doc, .docx')}
            className={inputCls}
          />
          <span className="text-xs text-muted-foreground mt-1 block">{t('Separate multiple extensions with commas')}</span>
        </div>
        <div className={fieldCls}>
          <label className={labelCls}>{t('Maximum File Size (MB)')}</label>
          <input
            type="number"
            min="1"
            max="100"
            value={settings.max_file_size_mb || 10}
            onChange={(e) => handleChange('max_file_size_mb', parseInt(e.target.value) || 10)}
            className={inputCls}
          />
        </div>
        {type === 'multi-file' && (
          <div className={fieldCls}>
            <label className={labelCls}>{t('Maximum Number of Files')}</label>
            <input
              type="number"
              min="1"
              max="20"
              value={settings.max_files || 5}
              onChange={(e) => handleChange('max_files', parseInt(e.target.value) || 5)}
              className={inputCls}
            />
          </div>
        )}
      </Wrapper>
    );
  }

  if (type === 'numeric') {
    return (
      <Wrapper title={t('Numeric Settings')}>
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className={labelCls}>{t('Minimum Value')}</label>
            <input
              type="number"
              value={settings.min_value ?? ''}
              onChange={(e) => handleChange('min_value', e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder={t('No minimum')}
              className={inputCls}
            />
          </div>
          <div className="flex-1">
            <label className={labelCls}>{t('Maximum Value')}</label>
            <input
              type="number"
              value={settings.max_value ?? ''}
              onChange={(e) => handleChange('max_value', e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder={t('No maximum')}
              className={inputCls}
            />
          </div>
        </div>
        <div className={fieldCls}>
          <label className={labelCls}>{t('Decimal Places')}</label>
          <input
            type="number"
            min="0"
            max="10"
            value={settings.decimal_places ?? 0}
            onChange={(e) => handleChange('decimal_places', parseInt(e.target.value) || 0)}
            className={inputCls}
          />
        </div>
        <div className={fieldCls}>
          <label className={labelCls}>{t('Score Weight (for review questions)')}</label>
          <input
            type="number"
            min="0"
            step="0.1"
            value={settings.weight ?? ''}
            onChange={(e) => handleChange('weight', e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder={t('Optional')}
            className={inputCls}
          />
        </div>
      </Wrapper>
    );
  }

  if (type === 'long-text' || type === 'markdown') {
    return (
      <Wrapper title={t('Text Length Settings')}>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className={labelCls}>{t('Minimum Words')}</label>
            <input
              type="number"
              min="0"
              value={settings.min_words ?? ''}
              onChange={(e) => handleChange('min_words', e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder={t('No minimum')}
              className={inputCls}
            />
          </div>
          <div className="flex-1">
            <label className={labelCls}>{t('Maximum Words')}</label>
            <input
              type="number"
              min="0"
              value={settings.max_words ?? ''}
              onChange={(e) => handleChange('max_words', e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder={t('No maximum')}
              className={inputCls}
            />
          </div>
        </div>
      </Wrapper>
    );
  }

  if (type === 'reference') {
    return (
      <Wrapper title={t('Reference Settings')}>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className={labelCls}>{t('Minimum Referrals')}</label>
            <input
              type="number"
              min="0"
              value={settings.min_referrals ?? 1}
              onChange={(e) => handleChange('min_referrals', parseInt(e.target.value) || 1)}
              className={inputCls}
            />
          </div>
          <div className="flex-1">
            <label className={labelCls}>{t('Maximum Referrals')}</label>
            <input
              type="number"
              min="1"
              value={settings.max_referrals ?? 3}
              onChange={(e) => handleChange('max_referrals', parseInt(e.target.value) || 3)}
              className={inputCls}
            />
          </div>
        </div>
      </Wrapper>
    );
  }

  return null;
};

export default QuestionSettingsEditor;
