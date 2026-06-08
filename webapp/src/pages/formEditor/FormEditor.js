import React, { useReducer, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { formEditorReducer } from './formEditorReducer';
import { FORM_ACTIONS } from './actionTypes';
import SectionCard from './components/SectionCard';
import FormSettingsPanel from './components/FormSettingsPanel';
import TranslatableFieldGroup from './components/TranslatableFieldGroup';
import { createEmptySection } from './utils/stateUtils';
import { transformToApiPayload, loadFormFromApi } from './utils/apiTransform';
import { validateForm, hasValidationErrors } from './utils/validation';

const FormEditor = ({
  eventId,
  formId,
  eventKey,
  languages,
  onSave,
  onCancel,
  includeReviewTypes = false,
  initialData = null
}) => {
  const { t } = useTranslation();
  const [showSettings, setShowSettings] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  const [autoTranslateEnabled, setAutoTranslateEnabled] = useState(true);

  const initialState = {
    form: {
      id: formId,
      name: languages.reduce((acc, lang) => { acc[lang.code] = ''; return acc; }, {}),
      description: languages.reduce((acc, lang) => { acc[lang.code] = ''; return acc; }, {}),
      is_active: true,
      is_open: true,
      multiple_responses: false,
      allow_edits: true,
      visibility_expression: null,
      linked_form_id: undefined,
      settings: { page_per_section: false }
    },
    sections: initialData ? initialData.sections : [createEmptySection(languages, 1, t('Untitled Section'))],
    event: { id: eventId, languages },
    ui: { isDirty: false, isSaving: false, expandedSections: new Set(), validationErrors: [] }
  };

  const [state, dispatch] = useReducer(formEditorReducer, initialState);

  useEffect(() => {
    if (initialData && initialData.sections) {
      const loadedData = loadFormFromApi(initialData, languages);
      dispatch({ type: FORM_ACTIONS.LOAD_FORM, payload: loadedData });
    }
  }, [initialData, languages]);

  const handleAddSection = () => dispatch({ type: FORM_ACTIONS.ADD_SECTION });

  const handleFormSettingChange = (key, value) =>
    dispatch({ type: FORM_ACTIONS.SET_FORM_SETTING, key, value });

  const handleFormNameChange = (langCode, value) =>
    dispatch({ type: FORM_ACTIONS.SET_FORM_SETTING, key: 'name', value: { ...state.form.name, [langCode]: value } });

  const handleFormDescriptionChange = (langCode, value) =>
    dispatch({ type: FORM_ACTIONS.SET_FORM_SETTING, key: 'description', value: { ...state.form.description, [langCode]: value } });

  const handleSave = async () => {
    setSaveError(null);
    const validationErrors = validateForm(state.sections, languages, state.form.name);
    if (hasValidationErrors(validationErrors)) {
      dispatch({ type: FORM_ACTIONS.SET_VALIDATION_ERRORS, errors: validationErrors });
      return;
    }
    dispatch({ type: FORM_ACTIONS.SAVE_FORM_START });
    try {
      const payload = transformToApiPayload(state.sections, languages);
      const result = await onSave({ ...state.form, ...payload });
      if (result.success) {
        const savedData = loadFormFromApi(result.data, languages);
        dispatch({ type: FORM_ACTIONS.SAVE_FORM_SUCCESS, payload: savedData });
        setShowSuccessNotification(true);
        setTimeout(() => setShowSuccessNotification(false), 3000);
      } else {
        throw new Error(result.error || t('Failed to save form'));
      }
    } catch (error) {
      console.error('Save error:', error);
      setSaveError(error.message);
      dispatch({ type: FORM_ACTIONS.SAVE_FORM_ERROR, error: error.message });
    }
  };

  const handlePreview = () => {
    const payload = transformToApiPayload(state.sections, languages);
    const previewData = { form: { ...state.form, sections: payload.sections }, isDirty: state.ui.isDirty };
    localStorage.setItem(`baobab_form_draft_preview_${formId}`, JSON.stringify(previewData));
    window.open(`/${eventKey}/forms/${formId}/preview`, '_blank');
  };

  const handleCancel = () => {
    if (state.ui.isDirty) {
      if (window.confirm(t('You have unsaved changes. Are you sure you want to leave?'))) {
        onCancel();
      }
    } else {
      onCancel();
    }
  };

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (state.ui.isDirty) { e.preventDefault(); e.returnValue = ''; }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [state.ui.isDirty]);

  const validationErrorsCount = state.ui.validationErrors.filter(e => e.severity === 'error').length;

  const allQuestions = state.sections.flatMap(section =>
    section.questions.map(q => ({
      id: q.id, order: q.order, headline: q.headline,
      sectionId: section.id, sectionOrder: section.order,
      type: q.type, options: q.options || []
    }))
  );

  // Shared button class fragments
  const btnPrimary = "inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const btnSecondary = "inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-border text-foreground rounded-md text-sm font-medium hover:bg-surface-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const btnPreview = "inline-flex items-center gap-2 px-5 py-2.5 bg-action text-white rounded-md text-sm font-medium hover:opacity-90 transition-opacity";

  return (
    <div className="bg-surface">
      {/* Toolbar */}
      <div className="bg-white border-b border-border px-8 py-4 flex justify-between items-center sticky top-[-2rem] z-[100] shadow-sm">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-semibold text-foreground m-0">{t('Form Editor')}</h1>
          {state.ui.isDirty && (
            <span className="flex items-center gap-2 text-warning text-sm font-medium">
              <i className="fas fa-circle text-[8px] animate-pulse"></i>
              {t('Unsaved changes')}
            </span>
          )}
        </div>

        <div className="flex gap-3 items-center">
          {/* Auto-translate toggle */}
          <label className="inline-flex items-center gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              className="sr-only"
              checked={autoTranslateEnabled}
              onChange={(e) => setAutoTranslateEnabled(e.target.checked)}
            />
            <span className="form-toggle" />
            <span className="text-sm text-foreground font-medium">{t('Auto-translate')}</span>
          </label>

          {formId && (
            <button type="button" className={btnPreview} onClick={handlePreview} title={t('Preview this form')}>
              <i className="fas fa-eye"></i>
              {t('Preview')}
            </button>
          )}
          <button type="button" className={btnSecondary} onClick={() => setShowSettings(true)}>
            <i className="fas fa-cog"></i>
            {t('Settings')}
          </button>
          <button type="button" className={btnSecondary} onClick={handleCancel} disabled={state.ui.isSaving}>
            {t('Cancel')}
          </button>
          <button type="button" className={btnPrimary} onClick={handleSave} disabled={state.ui.isSaving}>
            {state.ui.isSaving ? (
              <><i className="fas fa-spinner fa-spin"></i>{t('Saving...')}</>
            ) : (
              <><i className="fas fa-save"></i>{t('Save Form')}</>
            )}
          </button>
        </div>
      </div>

      {/* Banners */}
      {saveError && (
        <div className="flex items-center gap-3 px-8 py-3 font-medium bg-error-container text-on-error-container border-b border-error/20">
          <i className="fas fa-exclamation-triangle"></i>
          {t('Error saving form: {{error}}', { error: saveError })}
        </div>
      )}
      {validationErrorsCount > 0 && (
        <div className="flex items-center gap-3 px-8 py-3 font-medium bg-warning-bg text-warning border-b border-warning/20">
          <i className="fas fa-exclamation-circle"></i>
          {t('{{count}} validation error(s) found. Please fix them before saving.', { count: validationErrorsCount })}
        </div>
      )}

      {/* Form name / description */}
      <div className="bg-white px-8 py-6 mx-auto my-8 max-w-[1200px] rounded-lg shadow-sm">
        <TranslatableFieldGroup
          label={t('Form Name')}
          fieldName="form_name"
          values={state.form.name}
          languages={languages}
          onChange={handleFormNameChange}
          required={true}
          autoTranslateEnabled={autoTranslateEnabled}
          placeholder={t('Enter form name')}
        />
        <TranslatableFieldGroup
          label={t('Form Description')}
          fieldName="form_description"
          values={state.form.description}
          languages={languages}
          onChange={handleFormDescriptionChange}
          multiline={true}
          autoTranslateEnabled={autoTranslateEnabled}
          placeholder={t('Enter form description (optional)')}
        />
      </div>

      {/* Sections */}
      <div className="px-8 pb-8 max-w-[1200px] mx-auto">
        <div className="mb-8">
          {state.sections.map((section, index) => (
            <SectionCard
              key={section.id}
              section={section}
              sectionIndex={index}
              totalSections={state.sections.length}
              languages={languages}
              dispatch={dispatch}
              t={t}
              includeReviewTypes={includeReviewTypes}
              allQuestions={allQuestions}
              linkedFormId={state.form.linked_form_id}
              autoTranslateEnabled={autoTranslateEnabled}
            />
          ))}

          <button
            type="button"
            onClick={handleAddSection}
            className="w-full py-6 bg-white border-[3px] border-dashed border-border rounded-xl cursor-pointer text-primary font-semibold text-lg hover:bg-surface-low hover:border-primary transition-all flex items-center justify-center gap-3"
          >
            <i className="fas fa-plus text-xl"></i>
            {t('Add Section')}
          </button>
        </div>
      </div>

      {showSettings && (
        <FormSettingsPanel
          form={state.form}
          onChange={handleFormSettingChange}
          onClose={() => setShowSettings(false)}
          t={t}
        />
      )}

      {showSuccessNotification && (
        <div className="fixed top-5 right-5 z-[9999] px-6 py-4 flex items-center gap-3 font-medium bg-primary text-white rounded-lg shadow-elevated animate-slide-in-right">
          <i className="fas fa-check-circle text-xl"></i>
          <span>{t('Form saved successfully!')}</span>
        </div>
      )}
    </div>
  );
};

export default FormEditor;
