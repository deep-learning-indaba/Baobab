import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Redirect } from 'react-router-dom';
import { FormEditor } from '../formEditor';
import { formServices } from '../../services/form';
import Loading from '../../components/Loading';

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
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <Loading />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface flex items-start justify-center pt-16 px-4">
        <div className="max-w-2xl w-full bg-error-container border border-error/20 rounded-lg p-8">
          <h4 className="text-lg font-semibold text-on-error-container mb-2">
            {t('Error Loading Form')}
          </h4>
          <p className="text-on-error-container">{error}</p>
          <hr className="my-4 border-error/20" />
          <button
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors"
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
      <div className="min-h-screen bg-surface flex items-start justify-center pt-16 px-4">
        <div className="max-w-2xl w-full bg-warning-bg border border-warning/20 rounded-lg p-8">
          <h4 className="text-lg font-semibold text-warning mb-2">
            {t('Configuration Required')}
          </h4>
          <p className="text-warning/80">
            {t('Event configuration is required to create or edit forms.')}
          </p>
          <hr className="my-4 border-warning/20" />
          <button
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary-container transition-colors"
            onClick={handleCancel}
          >
            {t('Go Back')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="-mt-8 -mx-4 md:-mx-8 bg-surface">
      <FormEditor
        eventId={eventId}
        formId={formId}
        eventKey={props.eventKey}
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
