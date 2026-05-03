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
      const draftKey = `baobab_form_draft_preview_${formId}`;
      const draftJson = localStorage.getItem(draftKey);

      if (draftJson) {
        const draft = JSON.parse(draftJson);
        setForm(draft.form);
        setHasUnsavedChanges(draft.isDirty);
        setLoading(false);
        return;
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

  // Handle cancel
  const handleCancel = () => {
    window.close();
  };

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
          <div className="spinner-border" role="status">
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
              className="btn btn-primary"
              onClick={() => window.close()}
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
                className="btn btn-primary"
                onClick={handleRestart}
              >
                <i className="fas fa-redo"></i>
                {t('Preview Again')}
              </button>
              <button
                className="btn btn-outline-secondary"
                onClick={() => window.close()}
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
          className="btn btn-sm btn-outline-light"
          onClick={handleCancel}
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
