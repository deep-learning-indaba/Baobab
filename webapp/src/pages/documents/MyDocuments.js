import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Loading from '../../components/Loading';

const MyDocuments = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requestingId, setRequestingId] = useState(null);

  const load = useCallback(() => {
    if (!event) return;
    setLoading(true);
    documentsService.getAvailableDocuments(event.id).then((result) => {
      setDocuments(result.data || []);
      setError(result.error || null);
      setLoading(false);
    });
  }, [event]);

  useEffect(() => { load(); }, [load]);

  const handleRequest = (template) => {
    setRequestingId(template.id);
    documentsService.requestDocument(template.id).then((result) => {
      setRequestingId(null);
      if (result.error) {
        setError(result.error);
        return;
      }
      documentsService.downloadDocument(result.data.id, result.data.filename);
      load();
    });
  };

  const handleDownloadPrevious = (doc) => {
    documentsService.downloadDocument(doc.id, doc.filename);
  };

  if (!event) return <Loading />;

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <h1 className="font-heading text-2xl font-semibold text-foreground mb-6">{t('My Documents')}</h1>

      {error && (
        <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>
      )}

      {loading ? (
        <Loading />
      ) : documents.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">
          {t('No documents are available to you for this event yet.')}
        </Card>
      ) : (
        <div className="space-y-4">
          {documents.map((template) => {
            const blocked = template.blockers && template.blockers.length > 0;
            return (
              <Card key={template.id} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h2 className="font-heading font-semibold text-foreground">{template.name}</h2>
                    {template.description && (
                      <p className="text-sm text-muted-foreground mt-1">{template.description}</p>
                    )}
                    {template.instructions && (
                      <p className="text-sm text-muted-foreground mt-1 italic">{template.instructions}</p>
                    )}
                  </div>
                  {!blocked && (
                    <Button
                      onClick={() => handleRequest(template)}
                      disabled={requestingId === template.id}
                      className="shrink-0"
                    >
                      {requestingId === template.id ? t('Generating...') : t('Download PDF')}
                    </Button>
                  )}
                </div>

                {blocked && (
                  <div className="mt-3 rounded-lg border border-border bg-surface-low px-4 py-3 text-sm">
                    <p className="text-foreground mb-2">
                      {template.blockers[0].message || t('Complete a form before requesting this document.')}
                    </p>
                    {template.blockers.map((b) => (
                      <a
                        key={b.form_id}
                        href={`/${eventKey}/forms/${b.form_id}`}
                        className="text-action hover:underline text-sm block"
                      >
                        {t('Go to')} {b.form_name} →
                      </a>
                    ))}
                  </div>
                )}

                {!blocked && template.prompts && template.prompts.length > 0 && (
                  <div className="mt-3 rounded-lg border border-border bg-surface-low px-4 py-3 text-sm flex items-center justify-between gap-3 flex-wrap">
                    <p className="text-muted-foreground">💬 {template.prompts[0].message}</p>
                    <a
                      href={`/${eventKey}/forms/${template.prompts[0].form_id}`}
                      className="text-action hover:underline shrink-0"
                    >
                      {t('Complete')} {template.prompts[0].form_name} →
                    </a>
                  </div>
                )}

                {template.previous_documents && template.previous_documents.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <p className="text-xs text-muted-foreground mb-1">{t('Previously generated')}:</p>
                    {template.previous_documents.map((doc) => (
                      <button
                        key={doc.id}
                        onClick={() => handleDownloadPrevious(doc)}
                        className="text-sm text-action hover:underline block"
                      >
                        {doc.filename} — {doc.generated_at ? new Date(doc.generated_at).toLocaleDateString() : ''}
                      </button>
                    ))}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MyDocuments;
