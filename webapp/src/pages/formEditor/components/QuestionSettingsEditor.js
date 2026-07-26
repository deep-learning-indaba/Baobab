import React from 'react';

const inputCls = "w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring";
const labelCls = "block text-sm font-medium text-foreground mb-1";
const fieldCls = "mb-4";

// Declared at module scope, not inside the component. When this lived inside
// QuestionSettingsEditor it was a brand new component type on every render, so
// React unmounted and remounted the whole settings subtree on each keystroke -
// which blew away input focus and dropped characters mid-typing.
const Wrapper = ({ title, children }) => (
  <div className="mt-4 p-4 bg-surface rounded-lg border border-border">
    <h4 className="text-sm font-semibold text-foreground mb-3">{title}</h4>
    {children}
  </div>
);

// Number inputs are kept as free text until they parse. Coercing on every
// keystroke (`parseInt(e.target.value) || fallback`) made the field impossible
// to clear and snapped half-typed values back to the default.
const NumberField = ({ label, value, onChange, min, max, step, placeholder, hint }) => (
  <div className={fieldCls}>
    <label className={labelCls}>{label}</label>
    <input
      type="number"
      min={min}
      max={max}
      step={step}
      value={value === undefined || value === null ? '' : value}
      onChange={(e) => {
        const raw = e.target.value;
        if (raw === '') {
          onChange(undefined);
          return;
        }
        const parsed = step && String(step).includes('.') ? parseFloat(raw) : parseInt(raw, 10);
        onChange(Number.isNaN(parsed) ? undefined : parsed);
      }}
      placeholder={placeholder}
      className={inputCls}
    />
    {hint && <span className="text-xs text-muted-foreground mt-1 block">{hint}</span>}
  </div>
);

const QuestionSettingsEditor = ({ type, settings, onChange, languages, t, includeReviewTypes = false }) => {
  const current = settings || {};

  const handleChange = (field, value) => {
    const next = { ...current };
    // Drop the key entirely when cleared, so "no maximum" round-trips as an
    // absent setting rather than an explicit undefined that JSON discards.
    if (value === undefined || value === '') {
      delete next[field];
    } else {
      next[field] = value;
    }
    onChange(next);
  };

  const handleArrayChange = (field, valueString) => {
    const values = valueString
      .split(',')
      .map(v => v.trim())
      .filter(v => v)
      // Extensions must start with a dot; normalise instead of failing
      // validation later and making the admin guess why.
      .map(v => (v.startsWith('.') ? v : `.${v}`))
      .map(v => v.toLowerCase());
    handleChange(field, values.length > 0 ? values : undefined);
  };

  const minMaxError = (minKey, maxKey) => {
    const min = current[minKey];
    const max = current[maxKey];
    if (min !== undefined && max !== undefined && Number(min) > Number(max)) {
      return t('Minimum must be less than or equal to maximum');
    }
    return null;
  };

  if (type === 'file' || type === 'multi-file') {
    return (
      <Wrapper title={t('File Settings')}>
        <div className={fieldCls}>
          <label className={labelCls}>{t('Accepted Extensions')}</label>
          <input
            type="text"
            defaultValue={(current.accepted_extensions || []).join(', ')}
            onBlur={(e) => handleArrayChange('accepted_extensions', e.target.value)}
            placeholder={t('e.g., .pdf, .doc, .docx')}
            className={inputCls}
          />
          <span className="text-xs text-muted-foreground mt-1 block">
            {t('Separate multiple extensions with commas. Leave blank to accept any file type.')}
          </span>
        </div>
        <NumberField
          label={t('Maximum File Size (MB)')}
          value={current.max_file_size_mb}
          onChange={(v) => handleChange('max_file_size_mb', v)}
          min="1"
          max="100"
          placeholder="10"
        />
        {type === 'multi-file' && (
          <NumberField
            label={t('Maximum Number of Files')}
            value={current.max_files}
            onChange={(v) => handleChange('max_files', v)}
            min="1"
            max="20"
            placeholder="5"
          />
        )}
      </Wrapper>
    );
  }

  if (type === 'numeric') {
    const error = minMaxError('min_value', 'max_value');
    return (
      <Wrapper title={t('Numeric Settings')}>
        <div className="flex gap-4">
          <div className="flex-1">
            <NumberField
              label={t('Minimum Value')}
              value={current.min_value}
              onChange={(v) => handleChange('min_value', v)}
              step="0.01"
              placeholder={t('No minimum')}
            />
          </div>
          <div className="flex-1">
            <NumberField
              label={t('Maximum Value')}
              value={current.max_value}
              onChange={(v) => handleChange('max_value', v)}
              step="0.01"
              placeholder={t('No maximum')}
            />
          </div>
        </div>
        {error && <p className="text-error text-xs mb-3">{error}</p>}
        <NumberField
          label={t('Decimal Places')}
          value={current.decimal_places}
          onChange={(v) => handleChange('decimal_places', v)}
          min="0"
          max="10"
          placeholder="0"
        />
        {includeReviewTypes && (
          <NumberField
            label={t('Score Weight')}
            value={current.weight}
            onChange={(v) => handleChange('weight', v)}
            min="0"
            step="0.1"
            placeholder={t('Optional')}
            hint={t('Multiplier applied to this answer when calculating the review score.')}
          />
        )}
      </Wrapper>
    );
  }

  if (type === 'short-text' || type === 'long-text' || type === 'markdown') {
    const error = minMaxError('min_words', 'max_words');
    return (
      <Wrapper title={t('Length Settings')}>
        <div className="flex gap-4">
          <div className="flex-1">
            <NumberField
              label={t('Minimum Words')}
              value={current.min_words}
              onChange={(v) => handleChange('min_words', v)}
              min="0"
              placeholder={t('No minimum')}
            />
          </div>
          <div className="flex-1">
            <NumberField
              label={t('Maximum Words')}
              value={current.max_words}
              onChange={(v) => handleChange('max_words', v)}
              min="0"
              placeholder={t('No maximum')}
            />
          </div>
        </div>
        {error && <p className="text-error text-xs mb-1">{error}</p>}
        <span className="text-xs text-muted-foreground block">
          {t('Word limits are enforced when the response is submitted.')}
        </span>
      </Wrapper>
    );
  }

  if (type === 'reference') {
    const error = minMaxError('min_referrals', 'max_referrals');
    return (
      <Wrapper title={t('Reference Settings')}>
        <div className="flex gap-4">
          <div className="flex-1">
            <NumberField
              label={t('Minimum Referrals')}
              value={current.min_referrals}
              onChange={(v) => handleChange('min_referrals', v)}
              min="0"
              placeholder="1"
            />
          </div>
          <div className="flex-1">
            <NumberField
              label={t('Maximum Referrals')}
              value={current.max_referrals}
              onChange={(v) => handleChange('max_referrals', v)}
              min="1"
              placeholder="3"
            />
          </div>
        </div>
        {error && <p className="text-error text-xs">{error}</p>}
      </Wrapper>
    );
  }

  return null;
};

export default QuestionSettingsEditor;
