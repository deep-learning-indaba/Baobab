import React, { useEffect, useMemo, useState } from 'react';
import { Prompt } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { organisationService } from '../../services/organisation/organisation.service';
import { applyBranding } from '../../utils/branding';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import Loading from '../../components/Loading';
import ColourField from './components/ColourField';
import ImageField from './components/ImageField';
import SecretField from './components/SecretField';
import BrandPreview from './components/BrandPreview';

const TEXT_FIELDS = ['name', 'system_name', 'url', 'system_url', 'email_from', 'privacy_policy'];
const IMAGE_FIELDS = ['small_logo', 'large_logo', 'icon_logo', 'favicon', 'pwa_icon_192', 'pwa_icon_512'];
const REQUIRED_IMAGES = ['small_logo', 'large_logo', 'icon_logo'];
const OTHER_FIELDS = ['primary_colour', 'secondary_colour', 'iso_currency_code', 'stripe_api_publishable_key'];
const SECRET_FIELDS = ['stripe_api_secret_key', 'stripe_webhook_secret_key'];
const REQUIRED = ['name', 'system_name', 'url', 'system_url', 'privacy_policy', ...REQUIRED_IMAGES];
const SCALAR_FIELDS = [...TEXT_FIELDS, ...IMAGE_FIELDS, ...OTHER_FIELDS];

// Languages the webapp ships translations for.
const SUPPORTED_LANGUAGES = [
  { code: 'en', description: 'English' },
  { code: 'fr', description: 'Français' },
];

const COLOUR_RE = /^#[0-9a-fA-F]{6}$/;
const CURRENCY_RE = /^[A-Z]{3}$/;
const URL_RE = /^https?:\/\//;
const MAX_LENGTH = {
  name: 50, system_name: 50, url: 100, system_url: 100, email_from: 100, privacy_policy: 100,
  small_logo: 255, large_logo: 255, icon_logo: 255, favicon: 255, pwa_icon_192: 255, pwa_icon_512: 255,
  stripe_api_publishable_key: 200, stripe_api_secret_key: 200, stripe_webhook_secret_key: 200,
};

// Settings the rest of the app reads from the public organisation.
const PUBLIC_FIELDS = [
  'name', 'system_name', 'url', 'system_url', 'privacy_policy', 'languages', 'small_logo',
  'large_logo', 'icon_logo', 'favicon', 'pwa_icon_192', 'pwa_icon_512', 'primary_colour', 'secondary_colour',
];

const toForm = (settings) => {
  const form = {};
  SCALAR_FIELDS.forEach((key) => { form[key] = settings[key] || ''; });
  form.languages = settings.languages.map((l) => l.code);
  return form;
};

// The server stores a blank optional field as null.
const normalise = (value) => (typeof value === 'string' ? value.trim() : value) || null;

const sameList = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);

const Section = ({ title, description, children }) => (
  <Card className="p-5 space-y-4">
    <div>
      <h2 className="font-heading text-lg font-semibold text-foreground">{title}</h2>
      {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
    </div>
    {children}
  </Card>
);

const readUser = () => {
  try {
    return JSON.parse(localStorage.getItem('user'));
  } catch (e) {
    return null;
  }
};

/** Names, branding, languages and payment keys for the organisation. */
const OrganisationSettings = () => {
  const { t } = useTranslation();
  const user = readUser();
  const isAdmin = !!(user && user.is_admin);

  const [settings, setSettings] = useState(null);
  const [form, setForm] = useState(null);
  const [secrets, setSecrets] = useState({});
  const [loadError, setLoadError] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [serverError, setServerError] = useState(null);
  const [message, setMessage] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    organisationService.getSettings().then((result) => {
      if (result.error) {
        setLoadError(result.error);
        return;
      }
      setSettings(result.settings);
      setForm(toForm(result.settings));
    });
  }, [isAdmin]);

  const changes = useMemo(() => {
    if (!settings || !form) return {};
    const original = toForm(settings);
    const diff = {};
    SCALAR_FIELDS.forEach((key) => {
      if (normalise(form[key]) !== normalise(original[key])) diff[key] = normalise(form[key]);
    });
    if (!sameList(form.languages, original.languages)) {
      diff.languages = form.languages.map((code) => SUPPORTED_LANGUAGES.find((l) => l.code === code));
    }
    SECRET_FIELDS.forEach((key) => {
      if (secrets[key] !== undefined) diff[key] = secrets[key];
    });
    return diff;
  }, [settings, form, secrets]);

  const dirty = Object.keys(changes).length > 0;

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (dirty) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [dirty]);

  if (!isAdmin) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <div role="alert" className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">
          {t("You don't have permission to view this page.")}
        </div>
      </div>
    );
  }

  if (!form) {
    return loadError ? (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <div role="alert" className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{loadError}</div>
      </div>
    ) : <Loading />;
  }

  const validate = () => {
    const errors = {};
    REQUIRED.forEach((key) => {
      if (!normalise(form[key])) errors[key] = t('This field is required.');
    });
    Object.keys(MAX_LENGTH).forEach((key) => {
      const value = SECRET_FIELDS.includes(key) ? secrets[key] : form[key];
      if (!errors[key] && typeof value === 'string' && value.length > MAX_LENGTH[key]) {
        errors[key] = t('Use at most {{max}} characters.', { max: MAX_LENGTH[key] });
      }
    });
    ['url', 'system_url'].forEach((key) => {
      if (!errors[key] && !URL_RE.test(form[key].trim())) errors[key] = t('Enter a link starting with http:// or https://');
    });
    if (!errors.email_from && form.email_from.trim() && !form.email_from.includes('@')) {
      errors.email_from = t('Enter an email address.');
    }
    ['primary_colour', 'secondary_colour'].forEach((key) => {
      if (form[key].trim() && !COLOUR_RE.test(form[key].trim())) errors[key] = t('Use a colour like #0f5238');
    });
    if (form.iso_currency_code.trim() && !CURRENCY_RE.test(form.iso_currency_code.trim())) {
      errors.iso_currency_code = t('Use three capital letters, like USD.');
    }
    if (form.languages.length === 0) errors.languages = t('Choose at least one language.');
    return errors;
  };

  const errors = validate();
  const valid = Object.keys(errors).length === 0;
  const errorFor = (key) => errors[key] || (serverError && serverError.field === key ? serverError.message : null);

  const edit = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setServerError(null);
    setSaveError(null);
    setMessage(null);
  };

  const editSecret = (key, value) => {
    setSecrets((s) => ({ ...s, [key]: value }));
    setServerError(null);
    setSaveError(null);
    setMessage(null);
  };

  const toggleLanguage = (code) => {
    const chosen = form.languages.includes(code)
      ? form.languages.filter((c) => c !== code)
      : SUPPORTED_LANGUAGES.map((l) => l.code).filter((c) => c === code || form.languages.includes(c));
    edit('languages', chosen);
  };

  const save = () => {
    setSaving(true);
    setServerError(null);
    setSaveError(null);
    organisationService.updateSettings(changes).then((result) => {
      setSaving(false);
      if (result.error) {
        if (result.field) setServerError({ field: result.field, message: result.error });
        else setSaveError(result.error);
        return;
      }
      setSettings(result.settings);
      setForm(toForm(result.settings));
      setSecrets({});
      setMessage(t('Saved. The changes apply to everyone.'));
      applyBranding(result.settings);
      const publicOrg = {};
      PUBLIC_FIELDS.forEach((key) => { publicOrg[key] = result.settings[key]; });
      window.dispatchEvent(new CustomEvent('organisation-updated', { detail: publicOrg }));
    });
  };

  const text = (key, label, extra = {}) => (
    <label className="block text-sm" key={key}>
      <span className="block font-medium text-foreground">{label}</span>
      <input
        className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm"
        value={form[key]}
        onChange={(e) => edit(key, e.target.value)}
        aria-invalid={!!errorFor(key)}
        {...extra.input}
      />
      {errorFor(key) && <span className="block text-xs text-error mt-1">{errorFor(key)}</span>}
      {extra.hint && <span className="block text-xs text-muted-foreground mt-1">{extra.hint}</span>}
    </label>
  );

  const image = (key, label, hint) => (
    <ImageField
      key={key}
      id={`org-${key}`}
      label={label}
      hint={hint}
      value={form[key]}
      required={REQUIRED_IMAGES.includes(key)}
      onChange={(v) => edit(key, v)}
      error={errorFor(key)}
    />
  );

  return (
    <div className="max-w-4xl mx-auto py-6 px-4">
      <Prompt when={dirty} message={t('You have unsaved changes. Are you sure you want to leave?')} />
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div className="min-w-0">
          <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Organisation settings')}</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            {t('Names, branding, languages and payment keys used across this system.')}
          </p>
        </div>
        <Button onClick={save} disabled={!dirty || !valid || saving}>{t('Save changes')}</Button>
      </div>

      {message && (
        <div role="status" className="mb-3 rounded-lg border border-success/30 bg-success/5 px-4 py-2.5 text-sm text-success">{message}</div>
      )}
      {(saveError || (serverError && !FIELD_HAS_INPUT.includes(serverError.field))) && (
        <div role="alert" className="mb-3 rounded-lg border border-error/30 bg-error/5 px-4 py-2.5 text-sm text-error">
          {saveError || serverError.message}
        </div>
      )}

      <div className="space-y-4">
        <Section title={t('General')}>
          <div className="grid gap-4 md:grid-cols-2">
            {text('name', t('Organisation name'))}
            {text('system_name', t('System name'), { hint: t('Shown in the header and the browser tab.') })}
            {text('url', t('Website link'), { input: { placeholder: 'https://' } })}
            {text('system_url', t('System link'), { input: { placeholder: 'https://' }, hint: t('The address people use to reach this system.') })}
            {text('email_from', t('Sender email'), { hint: t('The address emails are sent from.') })}
            {text('privacy_policy', t('Privacy policy'), { hint: t('A file name or a link to your privacy policy.') })}
          </div>
          <label className="block text-sm">
            <span className="block font-medium text-foreground">{t('Domain')}</span>
            <input
              className="mt-1 w-full max-w-md rounded-lg border border-border bg-surface-low px-3 py-2 text-sm"
              value={settings.domain || ''}
              readOnly
            />
            <span className="block text-xs text-muted-foreground mt-1">
              {t("The domain can't be changed here. It must match your DNS configuration.")}
            </span>
          </label>
        </Section>

        <Section title={t('Branding')} description={t('Changes apply to everyone as soon as you save.')}>
          <div className="grid gap-4 md:grid-cols-2">
            <ColourField
              id="org-primary_colour"
              label={t('Primary colour (headers and highlights)')}
              value={form.primary_colour}
              onChange={(v) => edit('primary_colour', v)}
              error={errorFor('primary_colour')}
            />
            <ColourField
              id="org-secondary_colour"
              label={t('Accent colour (buttons and links)')}
              value={form.secondary_colour}
              onChange={(v) => edit('secondary_colour', v)}
              error={errorFor('secondary_colour')}
            />
          </div>
          <BrandPreview primary={form.primary_colour} accent={form.secondary_colour} />
          <div className="grid gap-4 md:grid-cols-2">
            {image('small_logo', t('Small logo'))}
            {image('large_logo', t('Large logo'))}
            {image('icon_logo', t('Header icon'), t('Shown next to the system name in the header.'))}
            {image('favicon', t('Favicon'), t('A 32×32 or 48×48 PNG or ICO image.'))}
            {image('pwa_icon_192', t('App icon (192 pixels)'), t('A square PNG image, 192×192 pixels.'))}
            {image('pwa_icon_512', t('App icon (512 pixels)'), t('A square PNG image, 512×512 pixels.'))}
          </div>
        </Section>

        <Section title={t('Languages')} description={t('The languages people can choose for this system.')}>
          <fieldset>
            <legend className="sr-only">{t('Languages')}</legend>
            <div className="flex flex-wrap gap-4">
              {SUPPORTED_LANGUAGES.map((lang) => (
                <label key={lang.code} className="inline-flex items-center gap-2 text-sm text-foreground">
                  <input
                    type="checkbox"
                    checked={form.languages.includes(lang.code)}
                    onChange={() => toggleLanguage(lang.code)}
                  />
                  {lang.description}
                </label>
              ))}
            </div>
            {errorFor('languages') && <span className="block text-xs text-error mt-1">{errorFor('languages')}</span>}
          </fieldset>
        </Section>

        <Section title={t('Payments')} description={t('Stripe keys are never shown again after saving. Type a new value to replace one.')}>
          <div className="grid gap-4 md:grid-cols-2">
            {text('iso_currency_code', t('Currency code'), { input: { placeholder: 'USD' }, hint: t('Three capital letters, like USD.') })}
            {text('stripe_api_publishable_key', t('Stripe publishable key'))}
          </div>
          <SecretField
            id="org-stripe_api_secret_key"
            label={t('Stripe secret key')}
            isSet={settings.stripe_secret_key_set}
            value={secrets.stripe_api_secret_key}
            onChange={(v) => editSecret('stripe_api_secret_key', v)}
            error={errorFor('stripe_api_secret_key')}
          />
          <SecretField
            id="org-stripe_webhook_secret_key"
            label={t('Stripe webhook secret')}
            isSet={settings.stripe_webhook_secret_key_set}
            value={secrets.stripe_webhook_secret_key}
            onChange={(v) => editSecret('stripe_webhook_secret_key', v)}
            error={errorFor('stripe_webhook_secret_key')}
          />
        </Section>
      </div>
    </div>
  );
};

// Fields that show a server error beside their own input.
const FIELD_HAS_INPUT = [...SCALAR_FIELDS, ...SECRET_FIELDS, 'languages'];

export default OrganisationSettings;
