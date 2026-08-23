import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { tagsService } from '../../services/tags';
import Loading from '../../components/Loading';
import DetailsTab from './components/DetailsTab';
import VariantsTab from './components/VariantsTab';
import FormsTab from './components/FormsTab';
import PlaceholdersTab from './components/PlaceholdersTab';
import GenerateTab from './components/GenerateTab';

const TABS = [
  { key: 'details', label: 'Details' },
  { key: 'variants', label: 'Template files' },
  { key: 'forms', label: 'Linked forms' },
  { key: 'placeholders', label: 'Placeholders' },
  { key: 'generate', label: 'Generate' },
];

const DocumentTemplateEditor = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);
  const routeTemplateId = props.match && props.match.params.templateId;
  const isNew = !routeTemplateId || routeTemplateId === 'new';

  const [template, setTemplate] = useState(null);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('details');
  const [tags, setTags] = useState([]);
  const [autoTranslateEnabled, setAutoTranslateEnabled] = useState(true);

  const orgLanguages = (props.organisation && props.organisation.languages) || [];
  // TranslatableFieldGroup treats languages[0] as the source language for
  // auto-translate, so English has to lead even if the organisation's own
  // list happens to order it differently.
  const languages = orgLanguages.length
    ? [...orgLanguages].sort((a, b) => (a.code === 'en' ? -1 : b.code === 'en' ? 1 : 0))
    : [{ code: 'en', description: 'English' }];

  const load = useCallback(() => {
    if (isNew || !template) return;
    documentsService.getTemplate(template.id).then((result) => {
      if (!result.error) setTemplate(result.data);
    });
  }, [isNew, template]);

  useEffect(() => {
    if (!isNew) {
      setLoading(true);
      documentsService.getTemplate(routeTemplateId).then((result) => {
        setLoading(false);
        if (result.error) {
          setError(result.error);
          return;
        }
        setTemplate(result.data);
      });
    }
  }, [isNew, routeTemplateId]);

  useEffect(() => {
    if (event) {
      tagsService.getTagList(event.id, 'en').then((result) => {
        setTags((result.tags || []).filter((tag) => tag.active));
      });
    }
  }, [event]);

  const handleCreated = (created) => {
    setTemplate(created);
    props.history.replace(`/${eventKey}/documentsAdmin/${created.id}`);
    setActiveTab('variants');
  };

  const handleSaved = (saved) => {
    setTemplate(saved);
  };

  if (!event) return <Loading />;
  if (loading) return <Loading />;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <button
            className="text-sm text-action hover:underline mb-2"
            onClick={() => props.history.push(`/${eventKey}/documentsAdmin`)}
          >
            ← {t('Back to Documents')}
          </button>
          <h1 className="font-heading text-2xl font-semibold text-foreground">
            {isNew ? t('New document') : (template ? template.name : '')}
          </h1>
        </div>
        {languages.length > 1 && (
          <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer select-none shrink-0 mt-1">
            <input
              type="checkbox"
              checked={autoTranslateEnabled}
              onChange={(e) => setAutoTranslateEnabled(e.target.checked)}
            />
            {t('Auto-translate')}
          </label>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      )}

      <div className="border-b border-border mb-6 flex gap-1 overflow-x-auto">
        {TABS.map((tab) => {
          const disabled = isNew && tab.key !== 'details' && !template;
          return (
            <button
              key={tab.key}
              disabled={disabled}
              onClick={() => setActiveTab(tab.key)}
              className={
                'px-4 py-2.5 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ' +
                (activeTab === tab.key
                  ? 'border-primary text-primary'
                  : disabled
                  ? 'border-transparent text-muted-foreground/50 cursor-not-allowed'
                  : 'border-transparent text-muted-foreground hover:text-foreground')
              }
            >
              {t(tab.label)}
            </button>
          );
        })}
      </div>

      {activeTab === 'details' && (
        <DetailsTab
          template={template}
          isNew={isNew}
          eventId={event.id}
          languages={languages}
          autoTranslateEnabled={autoTranslateEnabled}
          tags={tags}
          onCreated={handleCreated}
          onSaved={handleSaved}
        />
      )}
      {activeTab === 'variants' && template && (
        <VariantsTab template={template} eventId={event.id} tags={tags} onReload={load} />
      )}
      {activeTab === 'forms' && template && (
        <FormsTab
          template={template}
          eventId={event.id}
          languages={languages}
          autoTranslateEnabled={autoTranslateEnabled}
          onReload={load}
        />
      )}
      {activeTab === 'placeholders' && template && (
        <PlaceholdersTab template={template} eventId={event.id} onReload={load} />
      )}
      {activeTab === 'generate' && template && (
        <GenerateTab template={template} eventId={event.id} />
      )}
    </div>
  );
};

export default DocumentTemplateEditor;
