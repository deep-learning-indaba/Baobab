import React from 'react';
import { useTranslation } from 'react-i18next';
import { useInstall } from '../context/InstallContext';

export default function InstallBanner() {
  const { t } = useTranslation();
  const { bannerVisible, isIOS, install, dismiss } = useInstall();

  if (!bannerVisible) return null;

  return (
    <>
      <style>{`
        @media (min-width: 768px) { .install-banner { display: none !important; } }
      `}</style>
      <div className="install-banner" style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1050,
        background: 'var(--clr-primary)',
        color: 'var(--clr-on-primary)',
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
        boxShadow: '0 -2px 16px rgba(0,0,0,0.18)',
      }}>
        <i className="fas fa-mobile-alt" style={{ fontSize: 22, marginTop: 1, flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: 0, fontWeight: 600, fontSize: 14, lineHeight: 1.3 }}>
            {t('Add Baobab to your home screen')}
          </p>
          {isIOS ? (
            <p style={{ margin: '5px 0 0', fontSize: 13, opacity: 0.92, lineHeight: 1.4 }}>
              {t('Tap')} <i className="fas fa-share-square" /> {t('then')}{' '}
              <strong>{t('Add to Home Screen')}</strong>
            </p>
          ) : (
            <button
              onClick={install}
              style={{
                marginTop: 8,
                padding: '6px 16px',
                background: 'var(--clr-on-primary)',
                color: 'var(--clr-primary)',
                border: 'none',
                borderRadius: 6,
                fontWeight: 700,
                fontSize: 13,
                cursor: 'pointer',
              }}
            >
              {t('Install')}
            </button>
          )}
        </div>
        <button
          onClick={dismiss}
          aria-label={t('Dismiss')}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--clr-on-primary)',
            fontSize: 20,
            cursor: 'pointer',
            padding: '0 0 0 8px',
            opacity: 0.75,
            flexShrink: 0,
            lineHeight: 1,
          }}
        >
          <i className="fas fa-times" />
        </button>
      </div>
    </>
  );
}
