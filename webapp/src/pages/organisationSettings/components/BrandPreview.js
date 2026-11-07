import React from 'react';
import { useTranslation } from 'react-i18next';
import { contrastRatio, readableForeground } from '../../../utils/branding';

const HEX = /^#[0-9a-fA-F]{6}$/;
const DEFAULT_PRIMARY = '#0f5238';
const DEFAULT_ACCENT = '#0132c5';

const hardToRead = (colour) =>
  HEX.test(colour) && contrastRatio(colour, readableForeground(colour)) < 4.5;

/** Shows the chosen colours on a header bar, two buttons and a link. */
const BrandPreview = ({ primary, accent }) => {
  const { t } = useTranslation();
  const p = HEX.test(primary || '') ? primary : DEFAULT_PRIMARY;
  const a = HEX.test(accent || '') ? accent : DEFAULT_ACCENT;
  return (
    <div>
      <div className="text-sm font-medium text-foreground mb-1">{t('Preview')}</div>
      <div className="rounded-lg border border-border overflow-hidden" data-testid="brand-preview">
        <div className="px-4 py-2 text-sm font-semibold" style={{ background: p, color: readableForeground(p) }}>
          {t('Header bar')}
        </div>
        <div className="flex flex-wrap items-center gap-3 p-4 bg-white">
          <span className="rounded-lg px-4 py-2 text-sm font-semibold"
            style={{ background: p, color: readableForeground(p) }}>{t('Primary button')}</span>
          <span className="rounded-lg px-4 py-2 text-sm font-semibold"
            style={{ background: a, color: readableForeground(a) }}>{t('Accent button')}</span>
          <span className="text-sm underline" style={{ color: a }}>{t('A link')}</span>
        </div>
      </div>
      {hardToRead(primary) && (
        <p role="alert" className="text-xs text-warning mt-1">
          {t('Primary colour')}: {t('Text on this colour may be hard to read.')}
        </p>
      )}
      {hardToRead(accent) && (
        <p role="alert" className="text-xs text-warning mt-1">
          {t('Accent colour')}: {t('Text on this colour may be hard to read.')}
        </p>
      )}
    </div>
  );
};

export default BrandPreview;
