import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import FormRenderer from '../formRenderer/FormRenderer';
import { formServices } from '../../services/form';
import { formResponseService } from '../../services/formResponse';
import history from '../../History';

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
      <div className="w-full max-w-4xl mx-auto space-y-6">
        <div className="text-center mb-8">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-2">
            {form.name && form.name[i18n.language] ? form.name[i18n.language] : t('Form Responses')}
          </h1>
          <p className="text-muted-foreground text-sm">
            {t('You have {{count}} response(s) for this form', { count: responses.length })}
          </p>
        </div>

        <div className="flex justify-center mb-8">
          <button
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
            onClick={handleCreateNewResponse}
          >
            <i className="fas fa-plus"></i>
            {t('Create New Response')}
          </button>
        </div>

        <div className="space-y-4">
          {responses.map(response => {
            const startedDate = new Date(response.started_timestamp);
            const submittedDate = response.submitted_timestamp 
              ? new Date(response.submitted_timestamp)
              : null;
            const isWithdrawn = response.is_withdrawn;

            return (
              <div 
                key={response.id} 
                className={`bg-white rounded-2xl shadow-sm border p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-all hover:shadow-md ${
                  response.is_submitted ? 'border-green-200 bg-green-50/20' : 'border-amber-200 bg-amber-50/20'
                }`}
              >
                <div className="space-y-3 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    {response.is_submitted ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                        <i className="fas fa-check-circle text-xs"></i>
                        {t('Submitted')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                        <i className="fas fa-edit text-xs"></i>
                        {t('Draft')}
                      </span>
                    )}
                    {isWithdrawn && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                        <i className="fas fa-ban text-xs"></i>
                        {t('Withdrawn')}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex gap-4 text-xs text-muted-foreground flex-wrap">
                    <span className="flex items-center gap-1.5">
                      <i className="far fa-clock"></i>
                      {t('Started')}: {startedDate.toLocaleDateString()}
                    </span>
                    {submittedDate && (
                      <span className="flex items-center gap-1.5">
                        <i className="far fa-calendar-check"></i>
                        {t('Submitted')}: {submittedDate.toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-foreground/80">
                    {t('{{count}} answer(s) provided', { count: response.answers ? response.answers.length : 0 })}
                  </p>
                </div>

                <div className="flex gap-2 w-full md:w-auto">
                  {!response.is_submitted && !isWithdrawn && (
                    <button
                      className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full md:w-auto"
                      onClick={() => handleEditResponse(response)}
                    >
                      <i className="fas fa-edit"></i>
                      {t('Continue Editing')}
                    </button>
                  )}
                  {response.is_submitted && !isWithdrawn && (
                    <button
                      className="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-colors bg-surface-high text-foreground hover:bg-surface-high/80 border border-border w-full md:w-auto"
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
      <div className="w-full max-w-lg mx-auto flex items-center justify-center min-h-[400px] py-12">
        <div className="bg-white rounded-2xl shadow-sm border border-green-200 p-8 text-center space-y-6">
          <i className="fas fa-check-circle text-5xl text-green-500"></i>
          <h2 className="font-heading text-xl font-bold text-foreground">{t('Form Submitted Successfully!')}</h2>
          <p className="text-muted-foreground text-sm">{t('Thank you for your submission.')}</p>
          
          <div className="flex flex-wrap gap-3 justify-center">
            {form && form.multiple_responses && (
              <button
                className="inline-flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
                onClick={handleBackToList}
              >
                <i className="fas fa-list"></i>
                {t('View My Responses')}
              </button>
            )}
            <button
              className="inline-flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-surface-high text-foreground hover:bg-surface-high/80 border border-border"
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
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 py-12">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
        <p className="text-muted-foreground text-sm">{t('Loading form...')}</p>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="w-full max-w-lg mx-auto flex items-center justify-center min-h-[400px] py-12">
        <div className="bg-error/10 text-error border border-error/20 p-6 rounded-2xl text-center space-y-4">
          <i className="fas fa-exclamation-triangle text-4xl block"></i>
          <h3 className="text-lg font-bold font-heading">{t('Error')}</h3>
          <p className="text-sm">{error}</p>
          <button
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
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
      <div className="w-full max-w-5xl mx-auto pt-6">
        {renderSuccess()}
      </div>
    );
  }

  // Render main content
  return (
    <div className="w-full max-w-5xl mx-auto pt-6">
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
