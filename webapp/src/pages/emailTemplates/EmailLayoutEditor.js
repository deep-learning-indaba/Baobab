import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { emailTemplatesService } from '../../services/emailTemplates';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import Loading from '../../components/Loading';
import LiquidEditor from './components/LiquidEditor';
import EmailPreview from './components/EmailPreview';
import { emailScope, emailSettingsPath } from './util';

const FIELDS = ['logo_url', 'brand_colour', 'header_markdown', 'footer_markdown'];
const COLOUR_RE = /^#[0-9a-fA-F]{6}$/;

// The header and footer can use the organisation and (for an event) the event.
function layoutSchema(event, t) {
  const organisation = {
    label: t('Organisation'),
    fields: {
      name: { type: 'string', description: t('Organisation name') },
      system_name: { type: 'string', description: t('Name of this system') },
      url: { type: 'url', description: t("Organisation's website") },
      system_url: { type: 'url', description: t('Link to this system') },
      email_from: { type: 'string', description: t('Address emails are sent from') },
    },
  };
  if (!event) return { organisation };
  return {
    organisation,
    event: {
      label: t('Event'),
      fields: {
        name: { type: 'string', description: t('Event name') },
        url: { type: 'url', description: t("Event's page in this system") },
        website_url: { type: 'url', description: t("Event's own website") },
        email_from: { type: 'string', description: t("Event's contact address") },
        start_date: { type: 'date', description: t('First day of the event') },
        end_date: { type: 'date', description: t('Last day of the event') },
      },
    },
  };
}

/** Branding around every email: logo, colour, header and footer. */
const EmailLayoutEditor = (props) => {
  const { t } = useTranslation();
  const { event } = props;
  const scope = useMemo(() => emailScope(event), [event]);
  const basePath = emailSettingsPath(event);
  const schema = useMemo(() => layoutSchema(event, t), [event, t]);

  const [data, setData] = useState(null);
  const [language, setLanguage] = useState(null);
  const [values, setValues] = useState({});
  const [dirty, setDirty] = useState(false);
  const [preview, setPreview] = useState({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const footerEditor = useRef(null);

  const load = useCallback((lang) => {
    emailTemplatesService.getLayout(scope, lang).then((result) => {
      if (result.error) {
        setError(result.error);
        return;
      }
      setData(result.data);
      setLanguage(result.data.language);
      const own = result.data.layout || {};
      setValues(Object.fromEntries(FIELDS.map((field) => [field, own[field] || ''])));
      setDirty(false);
      setError(null);
    });
  }, [scope]);

  useEffect(() => { load(null); }, [load]);

  useEffect(() => {
    if (!data) return undefined;
    setPreviewLoading(true);
    const timer = setTimeout(() => {
      emailTemplatesService.previewLayout(scope, language, values).then((result) => {
        setPreviewLoading(false);
        if (result.error) setError(result.error);
        else {
          setPreview({ subject: t('Example email'), ...result.data });
          setError(null);
        }
      });
    }, 400);
    return () => clearTimeout(timer);
  }, [scope, language, values, data, t]);

  const update = (field, value) => {
    setValues((v) => ({ ...v, [field]: value }));
    setDirty(true);
    setMessage(null);
  };

  const save = () => {
    emailTemplatesService.saveLayout(scope, language, values).then((result) => {
      if (result.error) setError(result.error);
      else {
        setData(result.data);
        setDirty(false);
        setMessage(t('Saved. New emails will use this design.'));
      }
    });
  };

  const changeLanguage = (lang) => {
    if (dirty && !window.confirm(t('You have unsaved changes. Discard them?'))) return;
    load(lang);
  };

  if (!data) return error ? (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
    </div>
  ) : <Loading />;

  const inherited = data.inherited || {};
  const colourValid = !values.brand_colour || COLOUR_RE.test(values.brand_colour);
  const shownColour = COLOUR_RE.test(values.brand_colour) ? values.brand_colour : inherited.brand_colour;

  return (
    <div className="max-w-[1300px] mx-auto py-6 px-4">
      <button
        type="button"
        onClick={() => props.history.push(basePath)}
        className="text-sm text-action hover:underline cursor-pointer mb-3"
      >
        <i className="fas fa-arrow-left mr-1.5" style={{ fontSize: 11 }} />
        {t('All emails')}
      </button>
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div className="min-w-0">
          <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Email design')}</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            {event
              ? t('The logo, colour, header and footer around every email this event sends. Anything left blank uses the organisation\'s design.')
              : t('The logo, colour, header and footer around every email. Events can override any of these.')}
          </p>
        </div>
        <Button onClick={save} disabled={!dirty || !colourValid}>{t('Save')}</Button>
      </div>

      {data.languages.length > 1 && (
        <div className="flex gap-1 mb-4" role="tablist" aria-label={t('Language')}>
          {data.languages.map((lang) => (
            <button
              key={lang}
              type="button"
              role="tab"
              aria-selected={lang === language}
              onClick={() => changeLanguage(lang)}
              className={'px-3 py-1.5 rounded-lg text-sm font-semibold cursor-pointer ' +
                (lang === language ? 'bg-primary text-white' : 'bg-surface-low text-foreground hover:bg-surface-high')}
            >
              {lang.toUpperCase()}
            </button>
          ))}
        </div>
      )}

      {message && (
        <div className="mb-3 rounded-lg border border-success/30 bg-success/5 px-4 py-2.5 text-sm text-success">{message}</div>
      )}
      {error && (
        <div className="mb-3 rounded-lg border border-error/30 bg-error/5 px-4 py-2.5 text-sm text-error">{error}</div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card className="p-4 space-y-4 min-w-0 self-start">
          <label className="block text-sm">
            <span className="font-medium text-foreground">{t('Logo')}</span>
            <input
              className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm"
              value={values.logo_url}
              onChange={(e) => update('logo_url', e.target.value)}
              placeholder={inherited.logo_url || 'https://…/logo.png'}
            />
            <span className="text-xs text-muted-foreground">
              {t('A link to a PNG or JPG image, shown 48 pixels tall. It must be publicly reachable.')}
            </span>
          </label>

          <div className="text-sm">
            <span className="font-medium text-foreground">{t('Brand colour')}</span>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="color"
                aria-label={t('Brand colour')}
                value={shownColour || '#0f5238'}
                onChange={(e) => update('brand_colour', e.target.value)}
                className="h-9 w-12 rounded border border-border cursor-pointer"
              />
              <input
                className="w-32 rounded-lg border border-border px-3 py-2 text-sm font-mono"
                value={values.brand_colour}
                onChange={(e) => update('brand_colour', e.target.value)}
                placeholder={inherited.brand_colour}
              />
              {values.brand_colour && (
                <button type="button" className="text-xs text-action hover:underline cursor-pointer"
                  onClick={() => update('brand_colour', '')}>
                  {t('Use inherited')}
                </button>
              )}
            </div>
            {!colourValid && <span className="text-xs text-error">{t('Use a colour like #0f5238')}</span>}
            <span className="block text-xs text-muted-foreground mt-1">{t('Used for buttons, links and the line along the top.')}</span>
          </div>

          <div className="text-sm">
            <span className="font-medium text-foreground">{t('Header')}</span>
            <span className="block text-xs text-muted-foreground mb-1">{t('Shown under the logo. Usually left empty.')}</span>
            <LiquidEditor
              key={`header-${language}`}
              value={values.header_markdown}
              onChange={(v) => update('header_markdown', v)}
              schema={schema}
              placeholder={inherited.header_markdown || ''}
              ariaLabel={t('Header')}
              minHeight={60}
            />
          </div>

          <div className="text-sm">
            <span className="font-medium text-foreground">{t('Footer')}</span>
            <span className="block text-xs text-muted-foreground mb-1">
              {t('Small print below every email: who it is from, an address, how to get in touch.')}
            </span>
            <LiquidEditor
              key={`footer-${language}`}
              ref={footerEditor}
              value={values.footer_markdown}
              onChange={(v) => update('footer_markdown', v)}
              schema={schema}
              placeholder={inherited.footer_markdown || ''}
              ariaLabel={t('Footer')}
              minHeight={100}
            />
            <div className="flex flex-wrap gap-2 mt-1.5">
              {(event ? ['event.name', 'event.email_from', 'organisation.name'] : ['organisation.name', 'organisation.url'])
                .map((path) => (
                  <button key={path} type="button"
                    className="text-xs font-mono text-action hover:underline cursor-pointer"
                    onClick={() => footerEditor.current.insert(`{{ ${path} }}`)}>
                    {`+ ${path}`}
                  </button>
                ))}
            </div>
          </div>
        </Card>

        <EmailPreview
          subject={preview.subject}
          html={preview.html}
          text={preview.text}
          loading={previewLoading}
        />
      </div>
    </div>
  );
};

export default EmailLayoutEditor;
