import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Redirect } from 'react-router-dom';
import { FormEditor } from '../formEditor';
import { formServices } from '../../services/form';
import Loading from '../../components/Loading';
import './FormEditorPage.css';

const FormEditorPage = (props) => {
  const { t } = useTranslation();
  const formId = props.match && props.match.params ? props.match.params.formId : null;
  const eventId = props.event ? props.event.id : null;
  const languages = props.organisation ? props.organisation.languages || [] : [];
  
  const [loading, setLoading] = useState(!!formId);
  const [error, setError] = useState(null);
  const [initialData, setInitialData] = useState(null);
  const [redirectTo, setRedirectTo] = useState(null);

  const loadForm = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await formServices.getFormStructure(formId, 'en', false);
      
      if (result.error) {
        setError(result.error);
        setLoading(false);
        return;
      }

      setInitialData(result.form);
      setLoading(false);
    } catch (err) {
      console.error('Error loading form:', err);
      setError(err.message || t('Failed to load form'));
      setLoading(false);
    }
  }, [formId, t]);

  useEffect(() => {
    if (formId) {
      loadForm();
    }
  }, [formId, loadForm]);

  const handleSave = async (formData) => {
    try {
      let result;
      
      if (formId) {
        result = await formServices.updateFormStructure(formId, formData, 'en');
      } else {
        const createResult = await formServices.createForm({
          is_open: formData.is_open,
          is_active: formData.is_active,
          multiple_responses: formData.multiple_responses,
          settings: formData.settings
        });
        
        if (createResult.error) {
          return { success: false, error: createResult.error };
        }
        
        const newFormId = createResult.form.id;
        result = await formServices.updateFormStructure(newFormId, formData, 'en');
      }

      if (result.error) {
        return { success: false, error: result.error };
      }

      return { success: true, data: result.form };
    } catch (err) {
      console.error('Error saving form:', err);
      return { success: false, error: err.message || t('Failed to save form') };
    }
  };

  const handleCancel = () => {
    if (props.eventKey) {
      setRedirectTo(`/${props.eventKey}/admin/forms`);
    } else {
      setRedirectTo('/admin/forms');
    }
  };

  if (redirectTo) {
    return <Redirect to={redirectTo} />;
  }

  if (loading) {
    return (
      <div className="form-editor-page">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="form-editor-page">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">{t('Error Loading Form')}</h4>
          <p>{error}</p>
          <hr />
          <button 
            className="btn btn-primary" 
            onClick={handleCancel}
          >
            {t('Go Back')}
          </button>
        </div>
      </div>
    );
  }

  if (!eventId || languages.length === 0) {
    return (
      <div className="form-editor-page">
        <div className="alert alert-warning" role="alert">
          <h4 className="alert-heading">{t('Configuration Required')}</h4>
          <p>{t('Event configuration is required to create or edit forms.')}</p>
          <hr />
          <button 
            className="btn btn-primary" 
            onClick={handleCancel}
          >
            {t('Go Back')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="form-editor-page">
      <FormEditor
        eventId={eventId}
        formId={formId}
        languages={languages}
        onSave={handleSave}
        onCancel={handleCancel}
        includeReviewTypes={false}
        initialData={initialData}
      />
    </div>
  );
};

export default FormEditorPage;
