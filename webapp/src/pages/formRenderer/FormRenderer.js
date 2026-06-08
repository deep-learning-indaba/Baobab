import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import SectionRenderer from './components/SectionRenderer';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import { evaluateDependency, buildAnswersDict } from './utils/dependencyEvaluator';
import { validateAllAnswers, hasErrors, getErrorCount } from './utils/validation';
import { evaluateVisibilityExpression } from './utils/visibilityEvaluator';

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
  autoSaveInterval = 0,
  userTags = [],
  isPreview = false
}) => {
  const { t } = useTranslation();

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

  const settings = (form && form.settings) || {};
  const pagePerSection = settings.page_per_section || false;
  const isResponseSubmitted = response && response.is_submitted;
  const allowEdits = form && form.allow_edits !== false;
  const isReadOnly = readOnly || (!allowEdits && isResponseSubmitted);

  const formName = useMemo(() => {
    if (!form || !form.name) return '';
    if (typeof form.name === 'object') return form.name[language] || form.name['en'] || Object.values(form.name)[0] || '';
    return form.name;
  }, [form, language]);

  const formDescription = useMemo(() => {
    if (!form || !form.description) return '';
    if (typeof form.description === 'object') return form.description[language] || form.description['en'] || Object.values(form.description)[0] || '';
    return form.description;
  }, [form, language]);

  const sections = useMemo(() => {
    if (!form || !form.sections) return [];
    return form.sections.filter(s => s.is_active !== false).sort((a, b) => a.order - b.order);
  }, [form]);

  const answersDict = useMemo(() => buildAnswersDict(answers, linkedResponse), [answers, linkedResponse]);

  useEffect(() => {
    if (response && response.answers) setAnswers(response.answers.filter(a => a.is_active !== false));
  }, [response]);

  useEffect(() => {
    if (autoSaveInterval > 0 && isDirty && onSave && !isReadOnly) {
      const doSave = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
          const result = await onSave({ answers, is_submitted: false });
          if (result.success) { setIsDirty(false); setSaveSuccess(true); setTimeout(() => setSaveSuccess(false), 3000); }
        } finally { setIsSaving(false); }
      };
      const timer = setTimeout(doSave, autoSaveInterval);
      return () => clearTimeout(timer);
    }
  }, [answers, autoSaveInterval, isDirty, onSave, isReadOnly, isSaving]);

  const isSectionVisible = useCallback((section) => {
    if (section.dependency_expression && !evaluateDependency(section.dependency_expression, answersDict)) return false;
    if (section.tag_expression && !evaluateVisibilityExpression(section.tag_expression, userTags)) return false;
    return true;
  }, [answersDict, userTags]);

  const isQuestionVisible = useCallback((question, section) => {
    if (!isSectionVisible(section)) return false;
    if (question.dependency_expression && !evaluateDependency(question.dependency_expression, answersDict)) return false;
    if (question.tag_expression && !evaluateVisibilityExpression(question.tag_expression, userTags)) return false;
    return true;
  }, [answersDict, isSectionVisible, userTags]);

  const visibleSections = useMemo(() => sections.filter(isSectionVisible), [sections, isSectionVisible]);
  const currentSection = pagePerSection ? visibleSections[currentSectionIndex] : null;

  const handleAnswerChange = useCallback((question, value) => {
    setAnswers(prevAnswers => {
      const existingIndex = prevAnswers.findIndex(a => a.question_id === question.id);
      const newAnswer = { question_id: question.id, value };
      if (existingIndex >= 0) {
        const updated = [...prevAnswers];
        updated[existingIndex] = newAnswer;
        return updated;
      }
      return [...prevAnswers, newAnswer];
    });
    setIsDirty(true);
    setSaveSuccess(false);
    if (hasValidated && validationErrors[question.id]) {
      setValidationErrors(prev => { const u = { ...prev }; delete u[question.id]; return u; });
    }
  }, [hasValidated, validationErrors]);

  const validate = useCallback((checkRequired = true) => {
    const sectionsToValidate = pagePerSection && currentSection ? [currentSection] : visibleSections;
    const errors = validateAllAnswers(sectionsToValidate, answers, answersDict, language, t,
      (q, s) => isQuestionVisible(q, s || sectionsToValidate.find(sec => sec.questions && sec.questions.some(sq => sq.id === q.id)))
    );
    setValidationErrors(errors);
    setHasValidated(true);
    return !hasErrors(errors);
  }, [answers, answersDict, currentSection, isQuestionVisible, language, pagePerSection, t, visibleSections]);

  const handleSave = useCallback(async () => {
    if (!onSave || isSaving || isReadOnly) return;
    setIsSaving(true);
    setSubmitError(null);
    try {
      const result = await onSave({ answers, is_submitted: false });
      if (result.success) { setIsDirty(false); setSaveSuccess(true); setTimeout(() => setSaveSuccess(false), 3000); }
      else setSubmitError(result.error || t('Failed to save'));
    } catch (error) {
      setSubmitError(error.message || t('Failed to save'));
    } finally { setIsSaving(false); }
  }, [answers, isSaving, onSave, isReadOnly, t]);

  const handleNextSection = useCallback(() => {
    if (!validate(true)) return;
    if (currentSectionIndex < visibleSections.length - 1) {
      setCurrentSectionIndex(prev => prev + 1);
      window.scrollTo(0, 0);
    } else if (showConfirmation) {
      setShowConfirmationPage(true);
      window.scrollTo(0, 0);
    }
  }, [currentSectionIndex, showConfirmation, validate, visibleSections.length]);

  const handlePreviousSection = useCallback(() => {
    if (showConfirmationPage) setShowConfirmationPage(false);
    else if (currentSectionIndex > 0) setCurrentSectionIndex(prev => prev - 1);
    window.scrollTo(0, 0);
  }, [currentSectionIndex, showConfirmationPage]);

  const handleSubmit = useCallback(async (event) => {
    if (event) event.preventDefault();
    if (isSubmitting || isReadOnly) return;
    if (!allowEdits && !isResponseSubmitted) { setShowEditWarning(true); return; }

    const errors = validateAllAnswers(visibleSections, answers, answersDict, language, t,
      (q, s) => isQuestionVisible(q, s || visibleSections.find(sec => sec.questions && sec.questions.some(sq => sq.id === q.id)))
    );
    setValidationErrors(errors);
    setHasValidated(true);

    if (hasErrors(errors)) {
      if (pagePerSection) {
        const idx = visibleSections.findIndex(sec => sec.questions && sec.questions.some(q => errors[q.id]));
        if (idx >= 0) { setCurrentSectionIndex(idx); setShowConfirmationPage(false); }
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const result = await onSubmit({ answers, is_submitted: true });
      if (!result.success) {
        setSubmitError(result.error || t('Failed to submit'));
        if (result.validationErrors) {
          const serverErrors = {};
          result.validationErrors.forEach(err => { serverErrors[err.question_id] = t(err.error); });
          setValidationErrors(serverErrors);
        }
      }
    } catch (error) {
      setSubmitError(error.message || t('Failed to submit'));
    } finally { setIsSubmitting(false); }
  }, [allowEdits, answers, answersDict, isQuestionVisible, isResponseSubmitted, isSubmitting, language, onSubmit, pagePerSection, isReadOnly, t, visibleSections]);

  const handleConfirmSubmit = useCallback(async () => {
    setShowEditWarning(false);
    const errors = validateAllAnswers(visibleSections, answers, answersDict, language, t,
      (q, s) => isQuestionVisible(q, s || visibleSections.find(sec => sec.questions && sec.questions.some(sq => sq.id === q.id)))
    );
    setValidationErrors(errors);
    setHasValidated(true);

    if (hasErrors(errors)) {
      setSubmitError(t('Please fix the errors before submitting'));
      if (pagePerSection) {
        const idx = visibleSections.findIndex(sec => sec.questions && sec.questions.some(q => errors[q.id]));
        if (idx >= 0) { setCurrentSectionIndex(idx); setShowConfirmationPage(false); }
      }
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const result = await onSubmit({ answers, is_submitted: true });
      if (result && !result.success && result.errors && Array.isArray(result.errors)) {
        const serverErrors = {};
        result.errors.forEach(err => { serverErrors[err.question_id] = t(err.error); });
        setValidationErrors(serverErrors);
      }
    } catch (error) {
      setSubmitError(error.message || t('Failed to submit'));
    } finally { setIsSubmitting(false); }
  }, [answers, answersDict, isQuestionVisible, language, onSubmit, pagePerSection, t, visibleSections]);

  // Shared button styles
  const btnPrimary = "inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white rounded-md font-medium hover:bg-primary-container transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
  const btnSecondary = "inline-flex items-center justify-center gap-2 px-6 py-3 text-muted-foreground border border-border rounded-md font-medium hover:bg-surface transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
  const btnOutlinePrimary = "inline-flex items-center justify-center gap-2 px-6 py-3 text-action border border-action rounded-md font-medium hover:bg-action/5 transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
  const Spinner = () => <i className="fas fa-spinner fa-spin"></i>;

  const renderConfirmationPage = () => {
    const errorCount = getErrorCount(validationErrors);
    return (
      <div className="p-6 bg-surface rounded-lg">
        <h2 className="text-2xl font-semibold text-foreground mb-3">{t('Review Your Answers')}</h2>
        <p className="text-muted-foreground mb-6">
          {t('Please review your answers before submitting. You can go back to make changes if needed.')}
        </p>

        {errorCount > 0 && (
          <div className="flex items-center gap-3 p-4 mb-6 bg-error-container text-on-error-container rounded-lg border border-error/20">
            <i className="fas fa-exclamation-triangle text-xl"></i>
            {t('There are {{count}} validation error(s). Please go back and fix them.', { count: errorCount })}
          </div>
        )}

        <div className="flex flex-col gap-8 mb-8">
          {visibleSections.map(section => {
            const sectionName = typeof section.name === 'object'
              ? section.name[language] || section.name['en'] || Object.values(section.name)[0]
              : section.name;
            const visibleQuestions = (section.questions || [])
              .filter(q => q.is_active !== false && isQuestionVisible(q, section))
              .sort((a, b) => a.order - b.order);
            if (visibleQuestions.length === 0) return null;

            return (
              <div key={section.id}>
                <h3 className="text-lg font-semibold text-foreground pb-2 border-b-2 border-border mb-4">{sectionName}</h3>
                <div className="flex flex-col gap-4">
                  {visibleQuestions.map(question => {
                    if (['information', 'sub-heading'].includes(question.type)) return null;
                    const headline = typeof question.headline === 'object'
                      ? question.headline[language] || question.headline['en'] || Object.values(question.headline)[0]
                      : question.headline;
                    const val = answersDict[question.id];
                    const error = validationErrors[question.id];
                    return (
                      <div key={question.id} className={`p-4 bg-white border rounded-md${error ? ' border-error bg-error-container/10' : ' border-border'}`}>
                        <div className="font-medium text-foreground mb-2">{headline}</div>
                        <div className="text-foreground break-words">
                          {val || <span className="text-muted-foreground italic">{t('No answer provided')}</span>}
                        </div>
                        {error && <div className="text-error text-sm mt-2">{error}</div>}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex flex-col sm:flex-row justify-between gap-4 pt-6 border-t border-border">
          <button type="button" className={btnSecondary} onClick={handlePreviousSection}>
            <i className="fas fa-arrow-left"></i>
            {t('Go Back')}
          </button>
          <button type="submit" className={btnPrimary} onClick={handleSubmit} disabled={isSubmitting || errorCount > 0}>
            {isSubmitting ? <><Spinner />{t('Submitting...')}</> : <><i className="fas fa-check"></i>{t('Submit')}</>}
          </button>
        </div>
      </div>
    );
  };

  const renderProgressIndicator = () => {
    if (!pagePerSection || visibleSections.length <= 1) return null;
    const totalSteps = showConfirmation ? visibleSections.length + 1 : visibleSections.length;
    const currentStep = showConfirmationPage ? totalSteps : currentSectionIndex + 1;
    return (
      <div className="mb-8">
        <div className="h-2 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-[width] duration-300"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          />
        </div>
        <div className="mt-2 text-sm text-muted-foreground">
          {t('Step {{current}} of {{total}}', { current: currentStep, total: totalSteps })}
        </div>
      </div>
    );
  };

  const renderFormContent = () => {
    if (showConfirmationPage && pagePerSection) return renderConfirmationPage();
    if (pagePerSection && currentSection) {
      return (
        <SectionRenderer section={currentSection} answers={answers} answersDict={answersDict}
          onAnswerChange={handleAnswerChange} validationErrors={validationErrors} language={language}
          isQuestionVisible={(q) => isQuestionVisible(q, currentSection)}
          disabled={isReadOnly} linkedResponse={linkedResponse} t={t} />
      );
    }
    return (
      <div className="flex flex-col gap-12">
        {visibleSections.map(section => (
          <SectionRenderer key={section.id} section={section} answers={answers} answersDict={answersDict}
            onAnswerChange={handleAnswerChange} validationErrors={validationErrors} language={language}
            isQuestionVisible={isQuestionVisible} disabled={isReadOnly} linkedResponse={linkedResponse} t={t} />
        ))}
      </div>
    );
  };

  const renderNavigation = () => {
    if (showConfirmationPage && pagePerSection) return null;
    return (
      <div className="flex flex-col md:flex-row justify-between items-center pt-8 border-t border-border mt-8 gap-4">
        <div className="flex gap-3 w-full md:w-auto justify-center md:justify-start">
          {pagePerSection && currentSectionIndex > 0 && (
            <button type="button" className={btnSecondary} onClick={handlePreviousSection}>
              <i className="fas fa-arrow-left"></i>
              {t('Previous')}
            </button>
          )}
          {onCancel && (
            <button type="button" className={btnSecondary} onClick={onCancel}>
              {t('Cancel')}
            </button>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto items-stretch sm:items-center">
          {onSave && !isReadOnly && (
            <button type="button" className={btnOutlinePrimary} onClick={handleSave} disabled={isSaving || !isDirty}>
              {isSaving ? <><Spinner />{t('Saving...')}</> : <><i className="fas fa-save"></i>{t('Save Draft')}</>}
            </button>
          )}

          {pagePerSection ? (
            currentSectionIndex < visibleSections.length - 1 || showConfirmation ? (
              <button type="button" className={btnPrimary} onClick={handleNextSection}>
                {t('Next')}<i className="fas fa-arrow-right"></i>
              </button>
            ) : (
              <button type="submit" className={btnPrimary} onClick={handleSubmit} disabled={isSubmitting || isReadOnly}>
                {isSubmitting ? <><Spinner />{t('Submitting...')}</> : <><i className="fas fa-check"></i>{t('Submit')}</>}
              </button>
            )
          ) : (
            <button type="submit" className={btnPrimary} onClick={handleSubmit} disabled={isSubmitting || isReadOnly}>
              {isSubmitting ? <><Spinner />{t('Submitting...')}</> : <><i className="fas fa-check"></i>{t('Submit')}</>}
            </button>
          )}
        </div>
      </div>
    );
  };

  if (!form) {
    return (
      <div className="max-w-2xl mx-auto mt-8 p-4">
        <div className="flex items-center gap-3 p-4 bg-error-container text-on-error-container rounded-lg border border-error/20">
          {t('Form not found')}
        </div>
      </div>
    );
  }

  if (!form.is_open && !isReadOnly && !isPreview && !(response && response.is_submitted)) {
    return (
      <div className="max-w-2xl mx-auto mt-8 p-4">
        <div className="flex items-center gap-3 p-4 bg-warning-bg text-warning rounded-lg border border-warning/20">
          <i className="fas fa-lock text-xl"></i>
          {t('This form is currently closed for submissions.')}
        </div>
      </div>
    );
  }

  const errorCount = getErrorCount(validationErrors);

  return (
    <div className="mx-auto p-4 md:px-8 md:pt-4 md:pb-8 text-left">
      {/* Edit Warning Dialog */}
      {showEditWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000]" onClick={() => setShowEditWarning(false)}>
          <div className="bg-white rounded-lg max-w-xl w-[90%] shadow-elevated" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-4 px-6 py-6 border-b border-border text-warning">
              <i className="fas fa-exclamation-triangle text-3xl"></i>
              <h3 className="m-0 text-xl font-semibold text-foreground">
                {t('Important: Response Cannot Be Edited After Submission')}
              </h3>
            </div>
            <div className="px-6 py-6">
              <p className="mb-4 leading-relaxed text-foreground">
                {t('Once you submit this form, you will NOT be able to edit your responses. Please review your answers carefully before submitting.')}
              </p>
              <p className="leading-relaxed text-foreground">
                {t('You can still save your responses as a draft and come back to edit them later before submitting.')}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row justify-end gap-3 px-6 py-6 border-t border-border">
              <button type="button" className={btnSecondary} onClick={() => setShowEditWarning(false)}>
                {t('Go Back to Review')}
              </button>
              <button type="button" className={btnPrimary} onClick={handleConfirmSubmit} disabled={isSubmitting}>
                {isSubmitting ? t('Submitting...') : t('I Understand, Submit Now')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Closed form preview warning */}
      {!form.is_open && isPreview && (
        <div className="flex items-center gap-3 p-4 mb-6 bg-warning-bg text-warning rounded-lg border border-warning/20">
          <i className="fas fa-lock text-xl"></i>
          {t('Warning: This form is currently closed for submissions. In preview mode, you can still view the form, but submissions are disabled.')}
        </div>
      )}

      {/* Form Header */}
      <div className="flex items-center gap-4 mb-8 flex-wrap">
        {formName && <h1 className="text-3xl font-semibold text-foreground m-0 w-full">{formName}</h1>}
        {isDirty && !isReadOnly && (
          <span className="inline-flex items-center gap-2 text-sm text-warning">
            <i className="fas fa-circle text-[0.5rem] animate-pulse"></i>
            {t('Unsaved changes')}
          </span>
        )}
        {saveSuccess && (
          <span className="inline-flex items-center gap-2 text-sm text-primary">
            <i className="fas fa-check-circle"></i>
            {t('Saved')}
          </span>
        )}
        {formDescription && (
          <div className="w-full mt-3 text-muted-foreground">
            <MarkdownRenderer source={formDescription} />
          </div>
        )}
      </div>

      {/* Progress Indicator */}
      {renderProgressIndicator()}

      {/* Error Banner */}
      {submitError && (
        <div className="flex items-center gap-3 p-4 mb-6 bg-error-container text-on-error-container rounded-lg border border-error/20">
          <i className="fas fa-exclamation-triangle text-xl"></i>
          {submitError}
        </div>
      )}

      {/* Validation Summary */}
      {hasValidated && errorCount > 0 && !showConfirmationPage && (
        <div className="flex items-center gap-3 p-4 mb-6 bg-warning-bg text-warning rounded-lg border border-warning/20">
          <i className="fas fa-exclamation-circle text-xl"></i>
          {t('{{count}} validation error(s) found. Please fix them before continuing.', { count: errorCount })}
        </div>
      )}

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-8">
        {renderFormContent()}
        {renderNavigation()}
      </form>
    </div>
  );
};

export default FormRenderer;
