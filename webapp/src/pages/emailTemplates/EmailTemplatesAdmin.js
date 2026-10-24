import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { emailTemplatesService } from '../../services/emailTemplates';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Loading from '../../components/Loading';
import { emailScope, emailSettingsPath } from './util';

const GROUP_ORDER = [
  'account', 'applications', 'references', 'reviews', 'outcomes', 'registration', 'guests',
  'attendance', 'documents', 'messages',
];

const GROUP_LABELS = {
  account: 'Accounts',
  applications: 'Applications',
  references: 'References',
  reviews: 'Reviews',
  outcomes: 'Outcomes and offers',
  registration: 'Registration',
  guests: 'Invited guests',
  attendance: 'Attendance',
  documents: 'Documents',
  messages: 'Messages',
};

function StatusBadge({ status, level, t }) {
  const customisedHere = status.source === level;
  const customisedAbove = status.source === 'organisation' && level === 'event';
  const className = customisedHere
    ? 'bg-action/10 text-action'
    : customisedAbove ? 'bg-primary/10 text-primary' : 'bg-surface-high text-muted-foreground';
  const label = customisedHere ? t('Customised') : customisedAbove ? t('Organisation') : t('Standard');
  return (
    <span className={`text-xs font-semibold rounded-full px-2 py-0.5 ${className}`}>{label}</span>
  );
}

/**
 * Every email this event (or, with no event, the organisation) sends, grouped
 * by area, with whether each language uses the standard text or a customised one.
 */
const EmailTemplatesAdmin = (props) => {
  const { t, i18n } = useTranslation();
  const { event } = props;
  const scope = useMemo(() => emailScope(event), [event]);
  const basePath = emailSettingsPath(event);
  const level = event ? 'event' : 'organisation';

  const [types, setTypes] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    emailTemplatesService.getEmailTypes(scope, i18n.language).then((result) => {
      setTypes(result.data || []);
      setError(result.error || null);
    });
  }, [scope, i18n.language]);

  const groups = useMemo(() => {
    const byGroup = {};
    (types || []).forEach((type) => { (byGroup[type.group] = byGroup[type.group] || []).push(type); });
    return GROUP_ORDER.filter((group) => byGroup[group]).map((group) => [group, byGroup[group]]);
  }, [types]);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div className="min-w-0">
          <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Emails')}</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            {event
              ? t('The emails this event sends. Customise any of them; anything you leave alone uses the standard text.')
              : t('Organisation-wide versions of every email. Events use these unless they customise their own.')}
          </p>
        </div>
        <Button variant="secondary" onClick={() => props.history.push(`${basePath}/design`)}>
          <i className="fas fa-palette" style={{ fontSize: 13 }} />
          {t('Email design')}
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      )}

      {types === null ? <Loading /> : (
        <div className="space-y-8">
          {groups.map(([group, groupTypes]) => (
            <section key={group}>
              <h2 className="font-heading !text-xs !font-semibold uppercase tracking-wide !text-muted-foreground !mb-2 !mt-0">
                {t(GROUP_LABELS[group] || group)}
              </h2>
              <Card className="p-0 overflow-hidden divide-y divide-border">
                {groupTypes.map((type) => (
                  <button
                    key={type.key}
                    type="button"
                    onClick={() => props.history.push(`${basePath}/edit/${type.key}`)}
                    className="w-full text-left px-5 py-4 flex flex-wrap items-center justify-between gap-3 hover:bg-surface-low cursor-pointer"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-foreground">{type.name}</span>
                        {type.sensitive && (
                          <span className="text-xs text-muted-foreground" title={t('Contains a login or reset link, so its content is not kept after sending.')}>
                            <i className="fas fa-lock" style={{ fontSize: 11 }} />
                          </span>
                        )}
                        {type.is_document_email && (
                          <span className="text-xs font-mono text-muted-foreground">{type.key}</span>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground mt-0.5">{type.description}</div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {Object.entries(type.languages).map(([language, status]) => (
                        <span key={language} className="inline-flex items-center gap-1">
                          <span className="text-xs font-semibold text-muted-foreground">{language.toUpperCase()}</span>
                          <StatusBadge status={status} level={level} t={t} />
                        </span>
                      ))}
                      <i className="fas fa-chevron-right text-muted-foreground ml-1" style={{ fontSize: 12 }} />
                    </div>
                  </button>
                ))}
              </Card>
            </section>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmailTemplatesAdmin;
