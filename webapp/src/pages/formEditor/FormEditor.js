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
import './FormEditor.css';

const FormEditor = ({
  eventId,
  formId,
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

  const initialState = {
    form: {
      id: formId,
      name: languages.reduce((acc, lang) => {
        acc[lang.code] = '';
        return acc;
      }, {}),
      description: languages.reduce((acc, lang) => {
        acc[lang.code] = '';
        return acc;
      }, {}),
      is_active: true,
      is_open: true,
      multiple_responses: false,
      allow_edits: true,
      visibility_expression: null,
      linked_form_id: undefined,
      settings: {
        page_per_section: false
      }
    },
    sections: initialData ? initialData.sections : [createEmptySection(languages, 1, t('Untitled Section'))],
    event: {
      id: eventId,
      languages: languages
    },
    ui: {
      isDirty: false,
      isSaving: false,
      expandedSections: new Set(),
      validationErrors: []
    }
  };

  const [state, dispatch] = useReducer(formEditorReducer, initialState);

  useEffect(() => {
    if (initialData && initialData.sections) {
      const loadedData = loadFormFromApi(initialData, languages);
      dispatch({
        type: FORM_ACTIONS.LOAD_FORM,
        payload: loadedData
      });
    }
  }, [initialData, languages]);

  const handleAddSection = () => {
    dispatch({ type: FORM_ACTIONS.ADD_SECTION });
  };

  const handleFormSettingChange = (key, value) => {
    dispatch({
      type: FORM_ACTIONS.SET_FORM_SETTING,
      key,
      value
    });
  };

  const handleFormNameChange = (langCode, value) => {
    dispatch({
      type: FORM_ACTIONS.SET_FORM_SETTING,
      key: 'name',
      value: {
        ...state.form.name,
        [langCode]: value
      }
    });
  };

  const handleFormDescriptionChange = (langCode, value) => {
    dispatch({
      type: FORM_ACTIONS.SET_FORM_SETTING,
      key: 'description',
      value: {
        ...state.form.description,
        [langCode]: value
      }
    });
  };

  const handleSave = async () => {
    setSaveError(null);
    
    const validationErrors = validateForm(state.sections, languages, state.form.name);
    
    if (hasValidationErrors(validationErrors)) {
      dispatch({
        type: FORM_ACTIONS.SET_VALIDATION_ERRORS,
        errors: validationErrors
      });
      return;
    }

    dispatch({ type: FORM_ACTIONS.SAVE_FORM_START });

    try {
      const payload = transformToApiPayload(state.sections, languages);
      
      const result = await onSave({
        ...state.form,
        ...payload
      });

      if (result.success) {
        const savedData = loadFormFromApi(result.data, languages);
        dispatch({
          type: FORM_ACTIONS.SAVE_FORM_SUCCESS,
          payload: savedData
        });
        
        // Show success notification
        setShowSuccessNotification(true);
        setTimeout(() => {
          setShowSuccessNotification(false);
        }, 3000);
      } else {
        throw new Error(result.error || t('Failed to save form'));
      }
    } catch (error) {
      console.error('Save error:', error);
      setSaveError(error.message);
      dispatch({
        type: FORM_ACTIONS.SAVE_FORM_ERROR,
        error: error.message
      });
    }
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
      if (state.ui.isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [state.ui.isDirty]);

  const validationErrorsCount = state.ui.validationErrors.filter(e => e.severity === 'error').length;

  const allQuestions = state.sections.flatMap(section => 
    section.questions.map(q => ({
      id: q.id,
      order: q.order,
      headline: q.headline,
      sectionId: section.id,
      sectionOrder: section.order,
      type: q.type,
      options: q.options || []
    }))
  );

  return (
    <div className="form-editor">
      <div className="form-editor-toolbar">
        <div className="toolbar-left">
          <h1 className="form-editor-title">
            {formId ? t('Edit Form') : t('Create New Form')}
          </h1>
          {state.ui.isDirty && (
            <span className="unsaved-indicator">
              <i className="fas fa-circle"></i>
              {t('Unsaved changes')}
            </span>
          )}
        </div>
        
        <div className="toolbar-right">
          <button
            type="button"
            className="toolbar-btn toolbar-btn-secondary"
            onClick={() => setShowSettings(true)}
          >
            <i className="fas fa-cog"></i>
            {t('Settings')}
          </button>
          <button
            type="button"
            className="toolbar-btn toolbar-btn-secondary"
            onClick={handleCancel}
            disabled={state.ui.isSaving}
          >
            {t('Cancel')}
          </button>
          <button
            type="button"
            className="toolbar-btn toolbar-btn-primary"
            onClick={handleSave}
            disabled={state.ui.isSaving}
          >
            {state.ui.isSaving ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                {t('Saving...')}
              </>
            ) : (
              <>
                <i className="fas fa-save"></i>
                {t('Save Form')}
              </>
            )}
          </button>
        </div>
      </div>

      <div className="form-name-section">
        <TranslatableFieldGroup
          label={t('Form Name')}
          fieldName="form_name"
          values={state.form.name}
          languages={languages}
          onChange={handleFormNameChange}
          required={true}
          placeholder={t('Enter form name')}
        />
        <TranslatableFieldGroup
          label={t('Form Description')}
          fieldName="form_description"
          values={state.form.description}
          languages={languages}
          onChange={handleFormDescriptionChange}
          required={false}
          placeholder={t('Enter form description (optional)')}
          multiline={true}
        />
      </div>

      {saveError && (
        <div className="save-error-banner">
          <i className="fas fa-exclamation-triangle"></i>
          {t('Error saving form: {{error}}', { error: saveError })}
        </div>
      )}

      {validationErrorsCount > 0 && (
        <div className="validation-errors-banner">
          <i className="fas fa-exclamation-circle"></i>
          {t('{{count}} validation error(s) found. Please fix them before saving.', { 
            count: validationErrorsCount 
          })}
        </div>
      )}

      <div className="form-editor-content">
        <div className="sections-container">
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
            />
          ))}
          
          <button
            type="button"
            className="add-section-btn"
            onClick={handleAddSection}
          >
            <i className="fas fa-plus"></i>
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
        <div className="save-success-toast">
          <i className="fas fa-check-circle"></i>
          <span>{t('Form saved successfully!')}</span>
        </div>
      )}
    </div>
  );
};

export default FormEditor;
