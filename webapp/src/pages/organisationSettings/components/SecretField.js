import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * A write-only secret. `value` is undefined to keep the stored secret, null to
 * clear it, or the string typed to replace it. The stored secret is never shown.
 */
const SecretField = ({ id, label, isSet, value, onChange, error }) => {
  const { t } = useTranslation();
  const clearing = value === null;
  return (
    <div className="text-sm">
      <label htmlFor={id} className="font-medium text-foreground">{label}</label>
      <div className="mt-1 flex items-center gap-2">
        <input
          id={id}
          type="password"
          autoComplete="new-password"
          className="w-full max-w-md rounded-lg border border-border px-3 py-2 text-sm"
          value={typeof value === 'string' ? value : ''}
          onChange={(e) => onChange(e.target.value === '' ? undefined : e.target.value)}
          placeholder={isSet && !clearing ? t('•••• set') : t('Not set')}
          disabled={clearing}
          aria-invalid={!!error}
        />
        {clearing ? (
          <button type="button" className="text-xs text-action hover:underline cursor-pointer"
            onClick={() => onChange(undefined)}>
            {t('Undo')}
          </button>
        ) : (isSet || typeof value === 'string') && (
          <button type="button" className="text-xs text-action hover:underline cursor-pointer"
            onClick={() => onChange(isSet ? null : undefined)}>
            {t('Clear')}
          </button>
        )}
      </div>
      {clearing && <span className="block text-xs text-muted-foreground mt-1">{t('This key will be removed when you save.')}</span>}
      {error && <span className="block text-xs text-error mt-1">{error}</span>}
    </div>
  );
};

export default SecretField;
