import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import SectionRenderer from './components/SectionRenderer';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import { evaluateDependency, buildAnswersDict } from './utils/dependencyEvaluator';
import { validateAllAnswers, hasErrors, getErrorCount } from './utils/validation';
import './FormRenderer.css';

/**
 * FormRenderer - A modern, generic form renderer component
 * 
 * Features:
 * - Renders forms with sections and questions
 * - Supports all question types from the generic forms system
 * - Handles question and section dependencies
 * - Validates answers with real-time and submit-time validation
 * - Supports page-per-section mode and all-on-one-page mode
 * - Handles creating new responses and editing existing ones
 * - Auto-saves drafts (optional)
 * 
 * @param {object} form - The form definition from the API
 * @param {object} response - Optional existing response for editing
 * @param {string} language - Current language code
 * @param {function} onSubmit - Callback when form is submitted
 * @param {function} onSave - Callback to save draft (optional)
 * @param {function} onCancel - Callback when user cancels
 * @param {boolean} readOnly - If true, form is read-only
 * @param {object} linkedResponse - Optional linked form response (for review forms)
 */
const FormRenderer = ({
  form,
  response = null,
  language = 'en',
  onSubmit,
  onSave,
  onCancel,
  readOnly = false,
  linkedResponse = null,
  showConfirmation = true,
  autoSaveInterval = 0 // milliseconds, 0 = disabled
}) => {
  const { t } = useTranslation();

  // State
  const [answers, setAnswers] = useState([]);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [validationErrors, setValidationErrors] = useState({});
  const [hasValidated, setHasValidated] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [showConfirmationPage, setShowConfirmationPage] = useState(false);
  const [showEditWarning, setShowEditWarning] = useState(false);

  // Form settings
  const settings = (form && form.settings) || {};
  const pagePerSection = settings.page_per_section || false;

  // Determine if form should be read-only based on editability settings
  // If allow_edits is false and response is submitted, make it read-only
  const isResponseSubmitted = response && response.is_submitted;
  const allowEdits = form && form.allow_edits !== false;
  const isReadOnly = readOnly || (!allowEdits && isResponseSubmitted);

  // Get form name
  const formName = useMemo(() => {
    if (!form || !form.name) return '';
    if (typeof form.name === 'object') {
      return form.name[language] || form.name['en'] || Object.values(form.name)[0] || '';
    }
    return form.name;
  }, [form, language]);

  // Get form description
  const formDescription = useMemo(() => {
    if (!form || !form.description) return '';
    if (typeof form.description === 'object') {
      return form.description[language] || form.description['en'] || Object.values(form.description)[0] || '';
    }
    return form.description;
  }, [form, language]);

  // Get active sections sorted by order
  const sections = useMemo(() => {
    if (!form || !form.sections) return [];
    return form.sections
      .filter(s => s.is_active !== false)
      .sort((a, b) => a.order - b.order);
  }, [form]);

  // Build answers dictionary for dependency evaluation
  const answersDict = useMemo(() => buildAnswersDict(answers), [answers]);

  // Initialize answers from existing response
  useEffect(() => {
    if (response && response.answers) {
      setAnswers(response.answers.filter(a => a.is_active !== false));
    }
  }, [response]);

  // Auto-save functionality
  useEffect(() => {
    if (autoSaveInterval > 0 && isDirty && onSave && !isReadOnly) {
      const doSave = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
          const result = await onSave({ answers, is_submitted: false });
          if (result.success) {
            setIsDirty(false);
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 3000);
          }
        } finally {
          setIsSaving(false);
        }
      };
      const timer = setTimeout(doSave, autoSaveInterval);
      return () => clearTimeout(timer);
    }
  }, [answers, autoSaveInterval, isDirty, onSave, isReadOnly, isSaving]);

  // Check if a section is visible based on dependencies
  const isSectionVisible = useCallback((section) => {
    if (!section.dependency_expression) return true;
    return evaluateDependency(section.dependency_expression, answersDict);
  }, [answersDict]);

  // Check if a question is visible based on dependencies
  const isQuestionVisible = useCallback((question, section) => {
    // First check section visibility
    if (!isSectionVisible(section)) return false;
    
    // Then check question's own dependency
    if (!question.dependency_expression) return true;
    return evaluateDependency(question.dependency_expression, answersDict);
  }, [answersDict, isSectionVisible]);

  // Get visible sections
  const visibleSections = useMemo(() => {
    return sections.filter(isSectionVisible);
  }, [sections, isSectionVisible]);

  // Current section for paginated mode
  const currentSection = pagePerSection ? visibleSections[currentSectionIndex] : null;

  // Handle answer change
  const handleAnswerChange = useCallback((question, value) => {
    setAnswers(prevAnswers => {
      const existingIndex = prevAnswers.findIndex(a => a.question_id === question.id);
      const newAnswer = {
        question_id: question.id,
        value: value
      };

      let newAnswers;
      if (existingIndex >= 0) {
        newAnswers = [...prevAnswers];
        newAnswers[existingIndex] = newAnswer;
      } else {
        newAnswers = [...prevAnswers, newAnswer];
      }

      return newAnswers;
    });

    setIsDirty(true);
    setSaveSuccess(false);

    // Clear validation error for this question if re-validated
    if (hasValidated && validationErrors[question.id]) {
      setValidationErrors(prev => {
        const updated = { ...prev };
        delete updated[question.id];
        return updated;
      });
    }
  }, [hasValidated, validationErrors]);

  // Validate the form
  const validate = useCallback((checkRequired = true) => {
    const isVisibleChecker = (question, section) => isQuestionVisible(question, section);
    
    const sectionsToValidate = pagePerSection && currentSection 
      ? [currentSection] 
      : visibleSections;

    const errors = validateAllAnswers(
      sectionsToValidate,
      answers,
      answersDict,
      language,
      t,
      (q, s) => isVisibleChecker(q, s || sectionsToValidate.find(sec => 
        sec.questions && sec.questions.some(sq => sq.id === q.id)
      ))
    );

    setValidationErrors(errors);
    setHasValidated(true);

    return !hasErrors(errors);
  }, [answers, answersDict, currentSection, isQuestionVisible, language, pagePerSection, t, visibleSections]);

  // Handle save draft
  const handleSave = useCallback(async () => {
    if (!onSave || isSaving || isReadOnly) return;

    setIsSaving(true);
    setSubmitError(null);

    try {
      const result = await onSave({
        answers,
        is_submitted: false
      });

      if (result.success) {
        setIsDirty(false);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        setSubmitError(result.error || t('Failed to save'));
      }
    } catch (error) {
      setSubmitError(error.message || t('Failed to save'));
    } finally {
      setIsSaving(false);
    }
  }, [answers, isSaving, onSave, isReadOnly, t]);

  // Handle section navigation (for paginated mode)
  const handleNextSection = useCallback(() => {
    if (!validate(true)) return;

    if (currentSectionIndex < visibleSections.length - 1) {
      setCurrentSectionIndex(prev => prev + 1);
      window.scrollTo(0, 0);
    } else if (showConfirmation) {
      setShowConfirmationPage(true);
      window.scrollTo(0, 0);
    }
    // Note: If no confirmation and last section, the submit button handles submission
  }, [currentSectionIndex, showConfirmation, validate, visibleSections.length]);

  const handlePreviousSection = useCallback(() => {
    if (showConfirmationPage) {
      setShowConfirmationPage(false);
    } else if (currentSectionIndex > 0) {
      setCurrentSectionIndex(prev => prev - 1);
    }
    window.scrollTo(0, 0);
  }, [currentSectionIndex, showConfirmationPage]);

  // Handle form submission
  const handleSubmit = useCallback(async (event) => {
    if (event) event.preventDefault();
    if (isSubmitting || isReadOnly) return;

    // Show warning if form doesn't allow edits and this is first submission
    if (!allowEdits && !isResponseSubmitted) {
      setShowEditWarning(true);
      return;
    }

    // Validate all visible sections
    const isVisibleChecker = (question, section) => isQuestionVisible(question, section);
    const errors = validateAllAnswers(
      visibleSections,
      answers,
      answersDict,
      language,
      t,
      (q, s) => isVisibleChecker(q, s || visibleSections.find(sec => 
        sec.questions && sec.questions.some(sq => sq.id === q.id)
      ))
    );

    setValidationErrors(errors);
    setHasValidated(true);

    if (hasErrors(errors)) {
      // If paginated, go to the first section with errors
      if (pagePerSection) {
        const sectionWithError = visibleSections.findIndex(section =>
          section.questions && section.questions.some(q => errors[q.id])
        );
        if (sectionWithError >= 0) {
          setCurrentSectionIndex(sectionWithError);
          setShowConfirmationPage(false);
        }
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const result = await onSubmit({
        answers,
        is_submitted: true
      });

      if (!result.success) {
        setSubmitError(result.error || t('Failed to submit'));
        
        // Handle server-side validation errors
        if (result.validationErrors) {
          const serverErrors = {};
          result.validationErrors.forEach(err => {
            serverErrors[err.question_id] = t(err.error);
          });
          setValidationErrors(serverErrors);
        }
      }
    } catch (error) {
      setSubmitError(error.message || t('Failed to submit'));
    } finally {
      setIsSubmitting(false);
    }
  }, [allowEdits, answers, answersDict, isQuestionVisible, isResponseSubmitted, isSubmitting, language, onSubmit, pagePerSection, isReadOnly, t, visibleSections]);

  // Render confirmation page
  const renderConfirmationPage = () => {
    const errorCount = getErrorCount(validationErrors);

    return (
      <div className="form-confirmation">
        <h2>{t('Review Your Answers')}</h2>
        <p className="confirmation-instructions">
          {t('Please review your answers before submitting. You can go back to make changes if needed.')}
        </p>

        {errorCount > 0 && (
          <div className="alert alert-danger">
            <i className="fas fa-exclamation-triangle"></i>
            {t('There are {{count}} validation error(s). Please go back and fix them.', { count: errorCount })}
          </div>
        )}

        <div className="confirmation-sections">
          {visibleSections.map(section => {
            const sectionName = typeof section.name === 'object' 
              ? section.name[language] || section.name['en'] || Object.values(section.name)[0]
              : section.name;

            const visibleQuestions = (section.questions
              ? section.questions.filter(q => q.is_active !== false && isQuestionVisible(q, section))
                .sort((a, b) => a.order - b.order)
              : []);

            if (visibleQuestions.length === 0) return null;

            return (
              <div key={section.id} className="confirmation-section">
                <h3>{sectionName}</h3>
                <div className="confirmation-answers">
                  {visibleQuestions.map(question => {
                    const headline = typeof question.headline === 'object'
                      ? question.headline[language] || question.headline['en'] || Object.values(question.headline)[0]
                      : question.headline;

                    const value = answersDict[question.id];
                    const error = validationErrors[question.id];

                    // Skip display-only question types
                    if (['information', 'sub-heading'].includes(question.type)) {
                      return null;
                    }

                    return (
                      <div key={question.id} className={`confirmation-answer ${error ? 'has-error' : ''}`}>
                        <div className="answer-headline">{headline}</div>
                        <div className="answer-value">
                          {value || <span className="no-answer">{t('No answer provided')}</span>}
                        </div>
                        {error && <div className="answer-error">{error}</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        <div className="confirmation-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handlePreviousSection}
          >
            <i className="fas fa-arrow-left"></i>
            {t('Go Back')}
          </button>
          
          <button
            type="submit"
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={isSubmitting || errorCount > 0}
          >
            {isSubmitting ? (
              <>
                <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                {t('Submitting...')}
              </>
            ) : (
              <>
                <i className="fas fa-check"></i>
                {t('Submit')}
              </>
            )}
          </button>
        </div>
      </div>
    );
  };

  // Render progress indicator for paginated mode
  const renderProgressIndicator = () => {
    if (!pagePerSection || visibleSections.length <= 1) return null;

    const totalSteps = showConfirmation ? visibleSections.length + 1 : visibleSections.length;
    const currentStep = showConfirmationPage ? totalSteps : currentSectionIndex + 1;

    return (
      <div className="form-progress">
        <div className="progress-bar-container">
          <div 
            className="progress-bar-fill"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {t('Step {{current}} of {{total}}', { current: currentStep, total: totalSteps })}
        </div>
      </div>
    );
  };

  // Render form content
  const renderFormContent = () => {
    if (showConfirmationPage && pagePerSection) {
      return renderConfirmationPage();
    }

    if (pagePerSection && currentSection) {
      return (
        <SectionRenderer
          section={currentSection}
          answers={answers}
          answersDict={answersDict}
          onAnswerChange={handleAnswerChange}
          validationErrors={validationErrors}
          language={language}
          isQuestionVisible={(q) => isQuestionVisible(q, currentSection)}
          disabled={isReadOnly}
          t={t}
        />
      );
    }

    // All sections on one page
    return (
      <div className="form-all-sections">
        {visibleSections.map(section => (
          <SectionRenderer
            key={section.id}
            section={section}
            answers={answers}
            answersDict={answersDict}
            onAnswerChange={handleAnswerChange}
            validationErrors={validationErrors}
            language={language}
            isQuestionVisible={(q) => isQuestionVisible(q, section)}
            disabled={isReadOnly}
            t={t}
          />
        ))}
      </div>
    );
  };

  // Render navigation buttons
  const renderNavigation = () => {
    if (showConfirmationPage && pagePerSection) {
      return null; // Confirmation page has its own buttons
    }

    return (
      <div className="form-navigation">
        <div className="nav-left">
          {pagePerSection && currentSectionIndex > 0 && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handlePreviousSection}
            >
              <i className="fas fa-arrow-left"></i>
              {t('Previous')}
            </button>
          )}

          {onCancel && (
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={onCancel}
            >
              {t('Cancel')}
            </button>
          )}
        </div>

        <div className="nav-right">
          {onSave && !isReadOnly && (
            <button
              type="button"
              className="btn btn-outline-primary"
              onClick={handleSave}
              disabled={isSaving || !isDirty}
            >
              {isSaving ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {t('Saving...')}
                </>
              ) : (
                <>
                  <i className="fas fa-save"></i>
                  {t('Save Draft')}
                </>
              )}
            </button>
          )}

          {pagePerSection ? (
            currentSectionIndex < visibleSections.length - 1 || showConfirmation ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleNextSection}
              >
                {t('Next')}
                <i className="fas fa-arrow-right"></i>
              </button>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={isSubmitting || isReadOnly}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    {t('Submitting...')}
                  </>
                ) : (
                  <>
                    <i className="fas fa-check"></i>
                    {t('Submit')}
                  </>
                )}
              </button>
            )
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isSubmitting || isReadOnly}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {t('Submitting...')}
                </>
              ) : (
                <>
                  <i className="fas fa-check"></i>
                  {t('Submit')}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    );
  };

  // Proceed with actual submission after warning confirmation
  const handleConfirmSubmit = useCallback(async () => {
    setShowEditWarning(false);
    
    // Validate all visible sections
    const isVisibleChecker = (question, section) => isQuestionVisible(question, section);
    const errors = validateAllAnswers(
      visibleSections,
      answers,
      answersDict,
      language,
      t,
      (q, s) => isVisibleChecker(q, s || visibleSections.find(sec => 
        sec.questions && sec.questions.some(sq => sq.id === q.id)
      ))
    );

    setValidationErrors(errors);
    setHasValidated(true);

    if (hasErrors(errors)) {
      setSubmitError(t('Please fix the errors before submitting'));
      // If paginated, go to the first section with errors
      if (pagePerSection) {
        const sectionWithError = visibleSections.findIndex(section =>
          section.questions && section.questions.some(q => errors[q.id])
        );
        if (sectionWithError >= 0) {
          setCurrentSectionIndex(sectionWithError);
          setShowConfirmationPage(false);
        }
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const result = await onSubmit({
        answers,
        is_submitted: true
      });

      if (result && result.success) {
        // Success handled by parent
      } else if (result && result.errors) {
        if (Array.isArray(result.errors)) {
          const serverErrors = {};
          result.errors.forEach(err => {
            serverErrors[err.question_id] = t(err.error);
          });
          setValidationErrors(serverErrors);
        }
      }
    } catch (error) {
      setSubmitError(error.message || t('Failed to submit'));
    } finally {
      setIsSubmitting(false);
    }
  }, [answers, answersDict, currentSectionIndex, isQuestionVisible, language, onSubmit, pagePerSection, setCurrentSectionIndex, setHasValidated, setIsSubmitting, setShowConfirmationPage, setShowEditWarning, setSubmitError, setValidationErrors, showConfirmationPage, t, visibleSections]);

  // Early return if no form
  if (!form) {
    return (
      <div className="form-renderer-error">
        <div className="alert alert-danger">
          {t('Form not found')}
        </div>
      </div>
    );
  }

  // Early return if form is not open
  if (!form.is_open && !isReadOnly && !(response && response.is_submitted)) {
    return (
      <div className="form-renderer-closed">
        <div className="alert alert-warning">
          <i className="fas fa-lock"></i>
          {t('This form is currently closed for submissions.')}
        </div>
      </div>
    );
  }

  const errorCount = getErrorCount(validationErrors);

  return (
    <div className="form-renderer">
      {/* Edit Warning Dialog */}
      {showEditWarning && (
        <div className="edit-warning-overlay" onClick={() => setShowEditWarning(false)}>
          <div className="edit-warning-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="edit-warning-header">
              <i className="fas fa-exclamation-triangle"></i>
              <h3>{t('Important: Response Cannot Be Edited After Submission')}</h3>
            </div>
            <div className="edit-warning-body">
              <p>
                {t('Once you submit this form, you will NOT be able to edit your responses. Please review your answers carefully before submitting.')}
              </p>
              <p>
                {t('You can still save your responses as a draft and come back to edit them later before submitting.')}
              </p>
            </div>
            <div className="edit-warning-footer">
              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={() => setShowEditWarning(false)}
              >
                {t('Go Back to Review')}
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConfirmSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? t('Submitting...') : t('I Understand, Submit Now')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Form Header */}
      <div className="form-header">
        {formName && <h1 className="form-name">{formName}</h1>}
        {formDescription && (
          <div className="form-description">
            <MarkdownRenderer source={formDescription} />
          </div>
        )}
        {isDirty && !isReadOnly && (
          <span className="unsaved-indicator">
            <i className="fas fa-circle"></i>
            {t('Unsaved changes')}
          </span>
        )}
        {saveSuccess && (
          <span className="save-success-indicator">
            <i className="fas fa-check-circle"></i>
            {t('Saved')}
          </span>
        )}
      </div>

      {/* Progress Indicator */}
      {renderProgressIndicator()}

      {/* Error Banner */}
      {submitError && (
        <div className="alert alert-danger submit-error">
          <i className="fas fa-exclamation-triangle"></i>
          {submitError}
        </div>
      )}

      {/* Validation Errors Summary */}
      {hasValidated && errorCount > 0 && !showConfirmationPage && (
        <div className="alert alert-warning validation-summary">
          <i className="fas fa-exclamation-circle"></i>
          {t('{{count}} validation error(s) found. Please fix them before continuing.', { count: errorCount })}
        </div>
      )}

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="form-content">
        {renderFormContent()}
        {renderNavigation()}
      </form>
    </div>
  );
};

export default FormRenderer;
