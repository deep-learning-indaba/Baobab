import React from 'react';
import { useTranslation } from 'react-i18next';

const DEFAULT_SWATCH = '#0f5238';

/** A colour input plus a hex text field; an empty value means the Baobab default. */
const ColourField = ({ id, label, hint, value, onChange, error }) => {
  const { t } = useTranslation();
  const valid = /^#[0-9a-fA-F]{6}$/.test(value || '');
  return (
    <div className="text-sm">
      <label htmlFor={id} className="font-medium text-foreground">{label}</label>
      <div className="mt-1 flex items-center gap-2">
        <input
          type="color"
          aria-label={label}
          value={valid ? value : DEFAULT_SWATCH}
          onChange={(e) => onChange(e.target.value)}
          className="h-9 w-12 rounded border border-border cursor-pointer"
        />
        <input
          id={id}
          className="w-32 rounded-lg border border-border px-3 py-2 text-sm font-mono"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#0f5238"
          aria-invalid={!!error}
        />
        {value && (
          <button type="button" className="text-xs text-action hover:underline cursor-pointer"
            onClick={() => onChange('')}>
            {t('Reset to default')}
          </button>
        )}
      </div>
      {error && <span className="block text-xs text-error mt-1">{error}</span>}
      {hint && <span className="block text-xs text-muted-foreground mt-1">{hint}</span>}
    </div>
  );
};

export default ColourField;
