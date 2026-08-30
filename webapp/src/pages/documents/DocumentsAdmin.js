import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { ConfirmModal } from '../../components/Modal';
import Loading from '../../components/Loading';

const HEALTH_LABEL = {
  ok: 'Ready',
  no_variants: 'No template file',
  no_catch_all: 'No fallback variant',
  access_issue: "Can't access a template file",
};

function computeHealth(template) {
  const activeVariants = (template.variants || []).filter((v) => v.is_active);
  if (activeVariants.length === 0) return 'no_variants';
  if (activeVariants.some((v) => v.access_status && v.access_status !== 'ok')) return 'access_issue';
  const hasCatchAll = activeVariants.some((v) => !v.selection_expression);
  if (!hasCatchAll) return 'no_catch_all';
  return 'ok';
}

const DocumentsAdmin = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const load = useCallback(() => {
    if (!event) return;
    setLoading(true);
    documentsService.getTemplates(event.id).then((result) => {
      setTemplates(result.data || []);
      setError(result.error || null);
      setLoading(false);
    });
  }, [event]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = () => {
    const id = confirmDeleteId;
    setConfirmDeleteId(null);
    documentsService.deleteTemplate(id).then((result) => {
      if (result.error) {
        setError(result.error);
      } else {
        load();
      }
    });
  };

  if (!event) return <Loading />;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Documents')}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t('Invitation letters, certificates and other documents attendees can generate for this event.')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => props.history.push(`/${eventKey}/documentsAdmin/placeholders`)}>
            {t('Derived placeholders')}
          </Button>
          <Button variant="secondary" onClick={() => props.history.push(`/${eventKey}/documentsAdmin/user-data`)}>
            {t('Attendee data')}
          </Button>
          <Button onClick={() => props.history.push(`/${eventKey}/documentsAdmin/new`)}>
            {t('+ New document')}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">
          {error}
        </div>
      )}

      {loading ? (
        <Loading />
      ) : templates.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          {t('No documents configured yet. Create one to get started.')}
        </Card>
      ) : (
        <div className="space-y-3">
          {templates.map((template) => {
            const health = computeHealth(template);
            return (
              <Card key={template.id} className="p-5 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-heading font-semibold text-foreground truncate">{template.name}</span>
                    {!template.is_active && (
                      <span className="text-xs rounded-full px-2 py-0.5 bg-surface-high text-muted-foreground">
                        {t('Inactive')}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground mt-1 flex items-center gap-3 flex-wrap">
                    <span>{t('Key')}: {template.key}</span>
                    <span>{(template.variants || []).length} {t('variant(s)')}</span>
                    <span>{(template.form_links || []).length} {t('linked form(s)')}</span>
                    <span>{template.self_service ? t('Self-service') : t('Admin-generated only')}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span
                    className={
                      'text-xs font-semibold rounded-full px-2.5 py-1 ' +
                      (health === 'ok'
                        ? 'bg-success/10 text-success'
                        : 'bg-warning/10 text-warning')
                    }
                  >
                    {t(HEALTH_LABEL[health])}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => props.history.push(`/${eventKey}/documentsAdmin/${template.id}`)}
                  >
                    {t('Edit')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setConfirmDeleteId(template.id)}
                  >
                    {t('Delete')}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <ConfirmModal
        visible={!!confirmDeleteId}
        okText={t('Delete')}
        onOK={handleDelete}
        onCancel={() => setConfirmDeleteId(null)}
      >
        <p className="font-semibold text-foreground mb-1">{t('Delete this document?')}</p>
        <p>{t('Attendees will no longer be able to request it. Documents already generated are not affected.')}</p>
      </ConfirmModal>
    </div>
  );
};

export default DocumentsAdmin;
