import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import FormRenderer from '../formRenderer/FormRenderer';
import { formServices } from '../../services/form';
import './FormPreviewPage.css';

/**
 * FormPreviewPage - Preview a form without saving responses to database
 * Used by admins to test forms and validation
 */
const FormPreviewPage = (props) => {
  const formId = props.match.params.formId;
  const { t, i18n } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [previewComplete, setPreviewComplete] = useState(false);
  const [mockResponse, setMockResponse] = useState(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Load form structure - prefer draft from localStorage set by FormEditor
  const loadForm = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // The editor drops a draft snapshot here when you click Preview. Consume it
      // (remove it immediately) rather than leaving it in localStorage - left in
      // place, it would persist indefinitely, so any later visit to this URL, in
      // any session, long after the form was saved, would show that stale
      // snapshot instead of fetching the live form.
      const draftKey = `baobab_form_draft_preview_${formId}`;
      const draftJson = localStorage.getItem(draftKey);
      if (draftJson) {
        localStorage.removeItem(draftKey);
        try {
          const draft = JSON.parse(draftJson);
          if (draft && draft.form) {
            setForm(draft.form);
            setHasUnsavedChanges(!!draft.isDirty);
            setLoading(false);
            return;
          }
        } catch (parseError) {
          console.warn('Discarding unreadable form preview draft', parseError);
        }
      }

      const formResult = await formServices.getFormStructure(formId, i18n.language);
      
      if (formResult.error) {
        setError(formResult.error);
        setLoading(false);
        return;
      }

      setForm(formResult.form);
      setLoading(false);
    } catch (err) {
      setError(err.message || t('Failed to load form'));
      setLoading(false);
    }
  }, [formId, i18n.language, t]);

  useEffect(() => {
    loadForm();
  }, [loadForm]);

  // Mock submit - doesn't actually save to database
  const handleMockSubmit = async (data) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        setMockResponse({
          id: 'preview-' + Date.now(),
          answers: data.answers,
          is_submitted: true,
          submitted_timestamp: new Date().toISOString()
        });
        setPreviewComplete(true);
        resolve({ success: true, data: { id: 'preview' } });
      }, 500);
    });
  };

  // Mock save - doesn't actually save to database
  const handleMockSave = async (data) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        setMockResponse({
          id: 'preview-' + Date.now(),
          answers: data.answers,
          is_submitted: false
        });
        resolve({ success: true, data: { id: 'preview' } });
      }, 300);
    });
  };

  // window.close() only works for a tab this script opened (the editor's
  // Preview button); it is a no-op when the URL is navigated to directly, so
  // fall back to browser history in that case.
  const handleExit = () => {
    window.close();
    setTimeout(() => {
      if (!window.closed) {
        if (window.history.length > 1) window.history.back();
        else if (props.event && props.event.key) {
          window.location.assign(`/${props.event.key}/formConfig`);
        }
      }
    }, 150);
  };

  const handleCancel = handleExit;

  // Handle restart preview
  const handleRestart = () => {
    setPreviewComplete(false);
    setMockResponse(null);
  };

  // Render loading state
  if (loading) {
    return (
      <div className="form-preview-page">
        <div className="preview-banner">
          <i className="fas fa-eye"></i>
          <span>{t('Preview Mode')}</span>
        </div>
        <div className="form-preview-loading">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" role="status">
            <span className="sr-only">{t('Loading...')}</span>
          </div>
          <p>{t('Loading form preview...')}</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="form-preview-page">
        <div className="preview-banner">
          <i className="fas fa-eye"></i>
          <span>{t('Preview Mode')}</span>
        </div>
        <div className="form-preview-error">
          <div className="alert alert-danger">
            <i className="fas fa-exclamation-triangle"></i>
            <h3>{t('Error')}</h3>
            <p>{error}</p>
            <button
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors"
              onClick={handleExit}
            >
              {t('Go Back')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render success view
  if (previewComplete) {
    return (
      <div className="form-preview-page">
        <div className="preview-banner">
          <i className="fas fa-eye"></i>
          <span>{t('Preview Mode')}</span>
        </div>
        <div className="form-preview-success">
          <div className="success-message">
            <i className="fas fa-check-circle"></i>
            <h2>{t('Preview Submission Complete!')}</h2>
            <p className="preview-notice">
              <i className="fas fa-info-circle"></i>
              {t('This was a preview - no data was saved to the database.')}
            </p>
            
            {mockResponse && mockResponse.answers && (
              <div className="preview-summary">
                <h3>{t('Preview Summary')}</h3>
                <p>{t('You provided {{count}} answer(s)', { count: mockResponse.answers.length })}</p>
              </div>
            )}

            <div className="success-actions">
              <button
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors"
                onClick={handleRestart}
              >
                <i className="fas fa-redo"></i>
                {t('Preview Again')}
              </button>
              <button
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-border text-foreground rounded-md text-sm font-medium hover:bg-surface-low transition-colors"
                onClick={handleExit}
              >
                <i className="fas fa-times"></i>
                {t('Exit Preview')}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render form preview
  return (
    <div className="form-preview-page">
      <div className="preview-banner">
        <div className="banner-content">
          <i className="fas fa-eye"></i>
          <span>{t('Preview Mode')}</span>
          <span className="banner-notice">
            {t('No responses will be saved to the database')}
          </span>
          {hasUnsavedChanges && (
            <span className="banner-notice banner-notice-warning">
              <i className="fas fa-exclamation-triangle"></i>
              {t('Unsaved changes')}
            </span>
          )}
        </div>
        <button
          className="inline-flex items-center gap-2 px-3 py-1.5 border border-white/60 text-white rounded-md text-sm font-medium hover:bg-white/15 transition-colors"
          onClick={handleExit}
        >
          <i className="fas fa-times"></i>
          {t('Exit Preview')}
        </button>
      </div>

      {hasUnsavedChanges && (
        <div className="alert alert-warning form-preview-unsaved-warning">
          <i className="fas fa-exclamation-triangle"></i>
          {t('You are previewing unsaved changes. Save the form to make these changes permanent.')}
        </div>
      )}

      {form && (
        <div className="form-preview-content">
          <FormRenderer
            form={form}
            response={mockResponse}
            language={i18n.language}
            onSubmit={handleMockSubmit}
            onSave={handleMockSave}
            onCancel={handleCancel}
            showConfirmation={true}
            autoSaveInterval={0}
            isPreview={true}
          />
        </div>
      )}
    </div>
  );
};

export default FormPreviewPage;
