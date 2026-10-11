import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { emailTemplatesService } from '../../services/emailTemplates';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { ConfirmModal } from '../../components/Modal';
import Loading from '../../components/Loading';
import LiquidEditor from './components/LiquidEditor';
import FieldBrowser from './components/FieldBrowser';
import ButtonDialog from './components/ButtonDialog';
import EmailPreview from './components/EmailPreview';
import { scenarioSwitches } from './components/schema';
import { emailScope, emailSettingsPath, sourceLabel } from './util';

const PREVIEW_DELAY_MS = 400;

function ToolbarButton({ icon, label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className="inline-flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium text-foreground hover:bg-surface-low cursor-pointer"
    >
      <i className={`fas ${icon}`} style={{ fontSize: 12 }} />
      <span>{label}</span>
    </button>
  );
}

function overridesFor(switches, values) {
  const overrides = {};
  switches.forEach((s) => {
    const on = values[s.path];
    if (on === undefined) return;
    if (s.kind === 'boolean') overrides[s.path] = on;
    else if (s.kind === 'list' && !on) overrides[s.path] = 0;
    else if (s.kind === 'present' && !on) overrides[s.path] = null;
  });
  return overrides;
}

// The language to offer as a translation source: one already customised at
// this level, else one customised anywhere, else any other language.
function defaultTranslationSource(data) {
  const others = Object.keys(data.language_sources || {}).filter((lang) => lang !== data.language);
  return others.find((lang) => data.language_sources[lang] === data.level)
    || others.find((lang) => data.language_sources[lang] !== 'default')
    || others[0]
    || '';
}

const EmailTemplateEditor = (props) => {
  const { t, i18n } = useTranslation();
  const { event } = props;
  const key = props.match.params.key;
  const scope = useMemo(() => emailScope(event), [event]);
  const basePath = emailSettingsPath(event);

  const [schema, setSchema] = useState(null);
  const [template, setTemplate] = useState(null);
  const [language, setLanguage] = useState(null);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [errorDetail, setErrorDetail] = useState(null);
  const [preview, setPreview] = useState({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [scenario, setScenario] = useState({});
  const [buttonDialog, setButtonDialog] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [revisions, setRevisions] = useState(null);
  const [sidePanel, setSidePanel] = useState('preview');
  const [translateFrom, setTranslateFrom] = useState('');
  const [translating, setTranslating] = useState(false);
  const bodyEditor = useRef(null);
  const subjectEditor = useRef(null);
  const lastFocused = useRef('body');

  const switches = useMemo(() => (schema ? scenarioSwitches(schema.context) : []), [schema]);

  useEffect(() => {
    emailTemplatesService.getEmailType(scope, key, i18n.language).then((result) => {
      if (result.error) setError(result.error);
      else setSchema(result.data);
    });
  }, [scope, key, i18n.language]);

  const loadTemplate = useCallback((lang) => {
    emailTemplatesService.getTemplate(scope, key, lang).then((result) => {
      if (result.error) {
        setError(result.error);
        return;
      }
      const data = result.data;
      const current = data.override || data.inherited || { subject: '', body: '' };
      setTemplate(data);
      setLanguage(data.language);
      setTranslateFrom(defaultTranslationSource(data));
      setSubject(current.subject);
      setBody(current.body);
      setDirty(false);
      setErrorDetail(null);
      setRevisions(null);
    });
  }, [scope, key]);

  useEffect(() => { loadTemplate(null); }, [loadTemplate]);

  // Re-render the preview a moment after the last edit.
  useEffect(() => {
    if (!template || !schema) return undefined;
    setPreviewLoading(true);
    const timer = setTimeout(() => {
      emailTemplatesService.previewTemplate(scope, key, {
        language, subject, body, sample_overrides: overridesFor(switches, scenario),
      }).then((result) => {
        setPreviewLoading(false);
        // On an error the last good preview stays up; the error shows above
        // the editor, against the line it refers to.
        if (result.error) {
          setErrorDetail(result.errorDetail || { message: result.error });
        } else {
          setPreview(result.data);
          setErrorDetail(null);
        }
      });
    }, PREVIEW_DELAY_MS);
    return () => clearTimeout(timer);
  }, [scope, key, language, subject, body, scenario, switches, template, schema]);

  const changeLanguage = (lang) => {
    if (dirty && !window.confirm(t('You have unsaved changes. Discard them?'))) return;
    loadTemplate(lang);
  };

  const editor = () => (lastFocused.current === 'subject' ? subjectEditor.current : bodyEditor.current);

  const save = () => {
    setSaving(true);
    setMessage(null);
    emailTemplatesService.saveTemplate(scope, key, language, subject, body).then((result) => {
      setSaving(false);
      if (result.error) {
        setError(result.error);
        setErrorDetail(result.errorDetail);
        return;
      }
      setError(null);
      setTemplate(result.data);
      setDirty(false);
      setMessage(t('Saved. New emails of this type will use this text.'));
    });
  };

  const reset = () => {
    setConfirmReset(false);
    emailTemplatesService.resetTemplate(scope, key, language).then((result) => {
      if (result.error) setError(result.error);
      else {
        setMessage(t('Reset. This email now uses the inherited text.'));
        loadTemplate(language);
      }
    });
  };

  const sendTest = () => {
    setMessage(null);
    emailTemplatesService.testSend(scope, key, {
      language, subject, body, sample_overrides: overridesFor(switches, scenario),
    }).then((result) => {
      if (result.error) {
        setError(result.error);
        setErrorDetail(result.errorDetail);
      } else {
        setError(null);
        setMessage(t('A test email was sent to {{email}}.', { email: result.data.sent_to }));
      }
    });
  };

  const translate = () => {
    if (dirty && !window.confirm(t('You have unsaved changes. Replace them with the translation?'))) return;
    setTranslating(true);
    setMessage(null);
    emailTemplatesService.translateTemplate(scope, key, language, translateFrom).then((result) => {
      setTranslating(false);
      if (result.error) {
        setError(result.error);
        return;
      }
      setError(null);
      setSubject(result.data.subject);
      setBody(result.data.body);
      setDirty(true);
      const source = translateFrom.toUpperCase();
      setMessage(result.data.untranslated_lines
        ? t('Translated from {{language}}, except {{count}} line(s) left as they were. Review it, then save.',
          { language: source, count: result.data.untranslated_lines })
        : t('Translated from {{language}}. Review it, then save.', { language: source }));
    });
  };

  const showRevisions = () => {
    setSidePanel('history');
    emailTemplatesService.getRevisions(scope, key, language).then((result) => {
      setRevisions(result.data || []);
    });
  };

  if (!template || !schema) {
    return error ? (
      <div className="max-w-5xl mx-auto py-8 px-4">
        <div className="rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      </div>
    ) : <Loading />;
  }

  const hasOverride = !!template.override;
  const inheritedSource = template.inherited ? template.inherited.source : 'default';
  const bodyErrorLine = errorDetail && errorDetail.field === 'body' ? errorDetail.line : null;
  const subjectErrorLine = errorDetail && errorDetail.field === 'subject' ? 1 : null;

  return (
    <div className="max-w-[1400px] mx-auto py-6 px-4">
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
          <h1 className="font-heading text-2xl font-semibold text-foreground">
            {schema.name}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {hasOverride
              ? (template.level === 'event' ? t('Customised for this event.') : t('Customised for the organisation.'))
              : t('Using the {{source}} text. Saving creates a customised version.', { source: t(sourceLabel(inheritedSource)) })}
            {template.override && template.override.updated_by && (
              <> {t('Last edited by {{name}}.', { name: template.override.updated_by })}</>
            )}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={sendTest}>
            <i className="fas fa-paper-plane" style={{ fontSize: 12 }} />{t('Send test to me')}
          </Button>
          {hasOverride && (
            <Button variant="ghost" size="sm" onClick={() => setConfirmReset(true)}>
              {t('Reset to {{source}}', { source: t(sourceLabel(inheritedSource)) })}
            </Button>
          )}
          <Button size="sm" onClick={save} disabled={saving || !dirty}>
            {saving ? t('Saving…') : t('Save')}
          </Button>
        </div>
      </div>

      {template.languages.length > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex gap-1" role="tablist" aria-label={t('Language')}>
          {template.languages.map((lang) => (
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
        {translateFrom && (
          <div className="flex items-center gap-2 text-sm">
            <label htmlFor="translate-from" className="text-muted-foreground">{t('Translate from')}</label>
            <select
              id="translate-from"
              className="rounded-lg border border-border bg-white px-2 py-1.5 text-sm"
              value={translateFrom}
              onChange={(e) => setTranslateFrom(e.target.value)}
            >
              {Object.keys(template.language_sources || {})
                .filter((lang) => lang !== language)
                .map((lang) => (
                  <option key={lang} value={lang}>
                    {lang.toUpperCase()}{template.language_sources[lang] !== 'default' ? ` (${t('customised')})` : ''}
                  </option>
                ))}
            </select>
            <Button variant="outline" size="sm" onClick={translate} disabled={translating}>
              <i className="fas fa-language" style={{ fontSize: 13 }} />
              {translating ? t('Translating…') : t('Translate')}
            </Button>
          </div>
        )}
        </div>
      )}

      {message && (
        <div className="mb-3 rounded-lg border border-success/30 bg-success/5 px-4 py-2.5 text-sm text-success">{message}</div>
      )}
      {(error || errorDetail) && (
        <div className="mb-3 rounded-lg border border-error/30 bg-error/5 px-4 py-2.5 text-sm text-error">
          {errorDetail
            ? `${errorDetail.field === 'subject' ? t('Subject') : errorDetail.field === 'body' ? t('Body') : t('Template')}${errorDetail.line ? ` (${t('line')} ${errorDetail.line})` : ''}: ${errorDetail.message}`
            : error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="space-y-3 min-w-0">
          <div onFocus={() => { lastFocused.current = 'subject'; }}>
            <label className="block text-sm font-medium text-foreground mb-1">{t('Subject')}</label>
            <LiquidEditor
              ref={subjectEditor}
              value={subject}
              onChange={(v) => { setSubject(v); setDirty(true); }}
              schema={schema.context}
              singleLine
              ariaLabel={t('Subject')}
              errorLine={subjectErrorLine}
            />
          </div>
          <div onFocus={() => { lastFocused.current = 'body'; }}>
            <label className="block text-sm font-medium text-foreground mb-1">{t('Body')}</label>
            <div className="flex flex-wrap items-center gap-0.5 rounded-t-lg border border-b-0 border-border bg-surface-low px-1 py-1">
              <ToolbarButton icon="fa-bold" label={t('Bold')} onClick={() => bodyEditor.current.wrap('**', '**', t('bold text'))} />
              <ToolbarButton icon="fa-italic" label={t('Italic')} onClick={() => bodyEditor.current.wrap('_', '_', t('text'))} />
              <ToolbarButton icon="fa-heading" label={t('Heading')} onClick={() => bodyEditor.current.wrap('\n### ', '\n', t('Heading'))} />
              <ToolbarButton icon="fa-list-ul" label={t('List')} onClick={() => bodyEditor.current.wrap('\n- ', '\n', t('item'))} />
              <ToolbarButton icon="fa-link" label={t('Link')} onClick={() => bodyEditor.current.wrap('[', '](https://)', t('link text'))} />
              <span className="mx-1 h-5 w-px bg-border" />
              <ToolbarButton icon="fa-hand-pointer" label={t('Button')} onClick={() => setButtonDialog(true)} />
              <ToolbarButton icon="fa-code-branch" label={t('Condition')}
                onClick={() => bodyEditor.current.wrap('{% if  %}\n', '\n{% endif %}', '')} />
            </div>
            <div className="[&>div]:rounded-t-none">
              <LiquidEditor
                ref={bodyEditor}
                value={body}
                onChange={(v) => { setBody(v); setDirty(true); }}
                schema={schema.context}
                ariaLabel={t('Body')}
                errorLine={bodyErrorLine}
                minHeight={460}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">
              {t('Write in Markdown: **bold**, _italic_, "- " for a list. Type {{field}} to insert a field or {{tag}} for logic.',
                { field: '{{', tag: '{%', interpolation: { escapeValue: false } })}
            </p>
          </div>
        </div>

        <div className="min-w-0 space-y-3">
          <div className="flex gap-1 text-sm" role="tablist">
            {[['preview', t('Preview')], ['fields', t('Fields')], ['history', t('History')]].map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={sidePanel === value}
                onClick={() => (value === 'history' ? showRevisions() : setSidePanel(value))}
                className={'px-3 py-1.5 rounded-lg font-semibold cursor-pointer ' +
                  (sidePanel === value ? 'bg-primary text-white' : 'text-foreground hover:bg-surface-low')}
              >
                {label}
              </button>
            ))}
          </div>

          {sidePanel === 'preview' && (
            <>
              {switches.length > 0 && (
                <Card className="p-3">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    {t('Preview with sample data where…')}
                  </div>
                  <div className="grid gap-1.5">
                    {switches.map((s) => {
                      const checked = scenario[s.path] !== undefined ? scenario[s.path] : (s.kind === 'boolean' ? s.initial : true);
                      return (
                        <label key={s.path} className="flex items-start gap-2 text-xs text-foreground cursor-pointer min-w-0">
                          <input
                            type="checkbox"
                            className="mt-0.5 shrink-0"
                            checked={checked}
                            onChange={(e) => setScenario({ ...scenario, [s.path]: e.target.checked })}
                          />
                          <span className="min-w-0 break-words">
                            {s.label}
                            {s.kind === 'list' ? ` — ${t('has items')}` : s.kind === 'present' ? ` — ${t('present')}` : ''}
                            <span className="font-mono text-muted-foreground"> ({s.path})</span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </Card>
              )}
              <EmailPreview
                subject={preview.subject}
                html={preview.html}
                text={preview.text}
                loading={previewLoading}
              />
            </>
          )}

          {sidePanel === 'fields' && (
            <Card className="p-3 lg:max-h-[calc(100vh-160px)] lg:overflow-auto">
              <FieldBrowser context={schema.context} onInsert={(text) => editor().insert(text)} />
            </Card>
          )}

          {sidePanel === 'history' && (
            <Card className="p-3">
              {revisions === null ? (
                <Loading />
              ) : revisions.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t('No saved versions at this level yet.')}</p>
              ) : (
                <ul className="space-y-2">
                  {revisions.map((revision) => (
                    <li key={revision.id} className="rounded-lg border border-border p-2.5 text-xs">
                      <div className="font-semibold text-foreground">{new Date(revision.saved_at).toLocaleString()}</div>
                      <div className="text-muted-foreground">{revision.saved_by || t('Imported')}</div>
                      <div className="truncate text-foreground mt-1">{revision.subject}</div>
                      <button
                        type="button"
                        className="mt-1.5 text-action hover:underline cursor-pointer"
                        onClick={() => {
                          setSubject(revision.subject);
                          setBody(revision.body);
                          setDirty(true);
                        }}
                      >
                        {t('Load into editor')}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          )}
        </div>
      </div>

      <ButtonDialog
        visible={buttonDialog}
        context={schema.context}
        onClose={() => setButtonDialog(false)}
        onInsert={(text) => { setButtonDialog(false); bodyEditor.current.insert(text); }}
      />
      <ConfirmModal
        visible={confirmReset}
        okText={t('Reset')}
        danger
        onOK={reset}
        onCancel={() => setConfirmReset(false)}
      >
        <p className="font-semibold text-foreground mb-1">{t('Discard the customised text?')}</p>
        <p>{t('This email will go back to the {{source}} text for this language. Saved versions stay in the history.', { source: t(sourceLabel(inheritedSource)) })}</p>
      </ConfirmModal>
    </div>
  );
};

export default EmailTemplateEditor;
