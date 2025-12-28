import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import FormRenderer from '../formRenderer/FormRenderer';
import { formServices } from '../../services/form';
import { formResponseService } from '../../services/formResponse';
import history from '../../History';
import './FormPage.css';

/**
 * FormPage - Main page for responding to forms
 * Handles both single and multiple response modes
 */
const FormPage = (props) => {
  const formId = props.match.params.formId;
  const { t, i18n } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(null);
  const [responses, setResponses] = useState([]);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [view, setView] = useState('loading'); // loading, list, form
  const [error, setError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Load form and user's responses
  const loadFormAndResponses = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Load form structure
      const formResult = await formServices.getFormStructure(formId, i18n.language);
      
      if (formResult.error) {
        setError(formResult.error);
        setLoading(false);
        return;
      }

      const formData = formResult.form;
      setForm(formData);

      // Load existing responses
      const responseResult = await formResponseService.getResponse(formId);
      
      if (responseResult.error && responseResult.statusCode !== 404) {
        console.warn('Error loading responses:', responseResult.error);
      }

      const userResponses = responseResult.responses || [];
      setResponses(userResponses);

      // Determine initial view
      if (!formData.multiple_responses) {
        // Single response mode: show form immediately
        const existingResponse = userResponses.length > 0 ? userResponses[0] : null;
        setCurrentResponse(existingResponse);
        setView('form');
      } else if (userResponses.length === 0) {
        // Multiple responses allowed, but no responses yet: show form
        setCurrentResponse(null);
        setView('form');
      } else {
        // Multiple responses and responses exist: show list
        setView('list');
      }

      setLoading(false);
    } catch (err) {
      setError(err.message || t('Failed to load form'));
      setLoading(false);
    }
  }, [formId, i18n.language, t]);

  useEffect(() => {
    loadFormAndResponses();
  }, [loadFormAndResponses]);

  // Handle creating new response
  const handleCreateNewResponse = () => {
    setCurrentResponse(null);
    setView('form');
  };

  // Handle editing existing response
  const handleEditResponse = (response) => {
    if (response.is_submitted) {
      setError(t('Cannot edit a submitted response'));
      return;
    }
    setCurrentResponse(response);
    setView('form');
  };

  // Handle form submission (both draft and final submit)
  const handleSubmit = async (data) => {
    try {
      let result;

      if (currentResponse && currentResponse.id) {
        // Update existing response
        result = await formResponseService.updateResponse(
          formId,
          currentResponse.id,
          { answers: data.answers }
        );
      } else {
        // Create new response
        result = await formResponseService.createResponse(formId, {
          language: i18n.language,
          answers: data.answers
        });

        // If response already exists (in case of race condition), update it
        if (result.error && result.responseId) {
          result = await formResponseService.updateResponse(
            formId,
            result.responseId,
            { answers: data.answers }
          );
        }
      }

      if (result.error) {
        return { success: false, error: result.error };
      }

      // Update current response reference
      const savedResponse = result.response;
      setCurrentResponse(savedResponse);

      // Now submit if is_submitted is true
      if (data.is_submitted) {
        const submitResult = await formResponseService.submitResponse(
          formId,
          savedResponse.id
        );

        if (submitResult.error) {
          return {
            success: false,
            error: submitResult.error,
            validationErrors: submitResult.validationErrors
          };
        }

        // Success!
        setSubmitSuccess(true);
        return { success: true, data: submitResult.response };
      }

      return { success: true, data: savedResponse };
    } catch (err) {
      return { success: false, error: err.message || t('Failed to save response') };
    }
  };

  // Handle draft save
  const handleSave = async (data) => {
    try {
      let result;

      if (currentResponse && currentResponse.id) {
        // Update existing
        result = await formResponseService.updateResponse(
          formId,
          currentResponse.id,
          { answers: data.answers }
        );
      } else {
        // Create new
        result = await formResponseService.createResponse(formId, {
          language: i18n.language,
          answers: data.answers
        });

        if (result.error && result.responseId) {
          result = await formResponseService.updateResponse(
            formId,
            result.responseId,
            { answers: data.answers }
          );
        }
      }

      if (result.error) {
        return { success: false, error: result.error };
      }

      setCurrentResponse(result.response);
      return { success: true, data: result.response };
    } catch (err) {
      return { success: false, error: err.message || t('Failed to save draft') };
    }
  };

  // Handle cancel
  const handleCancel = () => {
    if (form && form.multiple_responses && responses.length > 0) {
      setView('list');
    } else {
      history.goBack();
    }
  };

  // Handle back to list
  const handleBackToList = () => {
    loadFormAndResponses();
  };

  // Render response list (for multiple responses mode)
  const renderResponseList = () => {
    return (
      <div className="form-page-responses">
        <div className="responses-header">
          <h1>{form.name && form.name[i18n.language] ? form.name[i18n.language] : t('Form Responses')}</h1>
          <p className="responses-subtitle">
            {t('You have {{count}} response(s) for this form', { count: responses.length })}
          </p>
        </div>

        <div className="responses-actions">
          <button
            className="btn btn-primary"
            onClick={handleCreateNewResponse}
          >
            <i className="fas fa-plus"></i>
            {t('Create New Response')}
          </button>
        </div>

        <div className="responses-list">
          {responses.map(response => {
            const startedDate = new Date(response.started_timestamp);
            const submittedDate = response.submitted_timestamp 
              ? new Date(response.submitted_timestamp)
              : null;
            const isWithdrawn = response.is_withdrawn;

            return (
              <div key={response.id} className={`response-card ${response.is_submitted ? 'submitted' : 'draft'}`}>
                <div className="response-header">
                  <div className="response-status">
                    {response.is_submitted ? (
                      <>
                        <i className="fas fa-check-circle text-success"></i>
                        <span className="status-text">{t('Submitted')}</span>
                      </>
                    ) : (
                      <>
                        <i className="fas fa-edit text-warning"></i>
                        <span className="status-text">{t('Draft')}</span>
                      </>
                    )}
                    {isWithdrawn && (
                      <>
                        <i className="fas fa-ban text-danger"></i>
                        <span className="status-text">{t('Withdrawn')}</span>
                      </>
                    )}
                  </div>
                  <div className="response-meta">
                    <div className="meta-item">
                      <i className="far fa-clock"></i>
                      {t('Started')}: {startedDate.toLocaleDateString()}
                    </div>
                    {submittedDate && (
                      <div className="meta-item">
                        <i className="far fa-calendar-check"></i>
                        {t('Submitted')}: {submittedDate.toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>

                <div className="response-body">
                  <p className="response-info">
                    {t('{{count}} answer(s) provided', { count: response.answers ? response.answers.length : 0 })}
                  </p>
                </div>

                <div className="response-actions">
                  {!response.is_submitted && !isWithdrawn && (
                    <button
                      className="btn btn-outline-primary btn-sm"
                      onClick={() => handleEditResponse(response)}
                    >
                      <i className="fas fa-edit"></i>
                      {t('Continue Editing')}
                    </button>
                  )}
                  {response.is_submitted && !isWithdrawn && (
                    <button
                      className="btn btn-outline-secondary btn-sm"
                      onClick={() => handleEditResponse(response)}
                      disabled
                    >
                      <i className="fas fa-eye"></i>
                      {t('View')}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render success message
  const renderSuccess = () => {
    return (
      <div className="form-page-success">
        <div className="success-message">
          <i className="fas fa-check-circle"></i>
          <h2>{t('Form Submitted Successfully!')}</h2>
          <p>{t('Thank you for your submission.')}</p>
          
          <div className="success-actions">
            {form && form.multiple_responses && (
              <button
                className="btn btn-primary"
                onClick={handleBackToList}
              >
                <i className="fas fa-list"></i>
                {t('View My Responses')}
              </button>
            )}
            <button
              className="btn btn-outline-secondary"
              onClick={() => history.goBack()}
            >
              <i className="fas fa-arrow-left"></i>
              {t('Go Back')}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render loading state
  if (loading) {
    return (
      <div className="form-page-loading">
        <div className="spinner-border" role="status">
          <span className="sr-only">{t('Loading...')}</span>
        </div>
        <p>{t('Loading form...')}</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="form-page-error">
        <div className="alert alert-danger">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>{t('Error')}</h3>
          <p>{error}</p>
          <button
            className="btn btn-primary"
            onClick={() => history.goBack()}
          >
            {t('Go Back')}
          </button>
        </div>
      </div>
    );
  }

  // Render success view
  if (submitSuccess) {
    return (
      <div className="form-page">
        {renderSuccess()}
      </div>
    );
  }

  // Render main content
  return (
    <div className="form-page">
      {view === 'list' && renderResponseList()}
      
      {view === 'form' && form && (
        <FormRenderer
          form={form}
          response={currentResponse}
          language={i18n.language}
          onSubmit={handleSubmit}
          onSave={handleSave}
          onCancel={handleCancel}
          showConfirmation={true}
          autoSaveInterval={30000}
        />
      )}
    </div>
  );
};

export default FormPage;
