import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Shows a rendered email. The HTML goes in a sandboxed iframe with no
 * permissions at all (no scripts, no same-origin access), so whatever a
 * template produces can't touch this page.
 */
export default function EmailPreview({ subject, html, text, loading, error }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState('html');

  return (
    <div className="rounded-xl border border-border bg-white overflow-hidden flex flex-col min-w-0">
      <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-border bg-surface-low">
        <div className="min-w-0 text-sm">
          <span className="text-muted-foreground">{t('Subject')}: </span>
          <span className="font-semibold text-foreground break-words">{subject || '—'}</span>
        </div>
        <div className="flex shrink-0 rounded-lg border border-border overflow-hidden text-xs" role="tablist">
          {[['html', t('Formatted')], ['text', t('Plain text')]].map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={mode === value}
              onClick={() => setMode(value)}
              className={'px-3 py-1.5 cursor-pointer ' + (mode === value ? 'bg-primary text-white' : 'bg-white text-foreground')}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="relative" style={{ minHeight: 520 }}>
        {error ? (
          <div className="m-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
        ) : mode === 'html' ? (
          <iframe
            title={t('Email preview')}
            sandbox=""
            srcDoc={html || ''}
            className="w-full border-0 block"
            style={{ height: 620 }}
          />
        ) : (
          <pre className="p-4 text-sm whitespace-pre-wrap break-words font-sans text-foreground">{text}</pre>
        )}
        {loading && (
          <div className="absolute top-2 right-3 text-xs text-muted-foreground">{t('Updating…')}</div>
        )}
      </div>
    </div>
  );
}
