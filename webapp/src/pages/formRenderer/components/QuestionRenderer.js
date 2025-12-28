import React, { useState, useCallback } from 'react';
import FormTextBox from '../../../components/form/FormTextBox';
import FormTextArea from '../../../components/form/FormTextArea';
import FormSelect from '../../../components/form/FormSelect';
import FormMultiCheckbox from '../../../components/form/FormMultiCheckbox';
import FormRadio from '../../../components/form/FormRadio';
import FormCheckbox from '../../../components/form/FormCheckbox';
import FormDate from '../../../components/form/FormDate';
import FormFileUpload from '../../../components/form/FormFileUpload';
import FormMultiFile from '../../../components/form/FormMultiFile';
import FormCountry from '../../../components/form/FormCountry';
import MarkdownRenderer from '../../../components/MarkdownRenderer';
import { fileService } from '../../../services/file/file.service';
import './QuestionRenderer.css';

const QuestionRenderer = ({
  question,
  value,
  onChange,
  language,
  validationError,
  disabled = false,
  t
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadPercentComplete, setUploadPercentComplete] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [uploaded, setUploaded] = useState(false);

  const id = `question_${question.id}`;

  // Get translated content
  const getTranslatedField = (field) => {
    if (!question[field]) return null;
    if (typeof question[field] === 'object') {
      return question[field][language] || question[field]['en'] || Object.values(question[field])[0];
    }
    return question[field];
  };

  const headline = getTranslatedField('headline');
  const description = getTranslatedField('description');
  const placeholder = getTranslatedField('placeholder');

  // Get options for choice-based questions
  const getOptions = () => {
    const optionsData = question.options;
    if (!optionsData) return [];

    // If options is already an array of {value, label}
    if (Array.isArray(optionsData) && optionsData.length > 0 && optionsData[0].value !== undefined) {
      // This might be the editor format with labels as i18n objects
      if (optionsData[0].labels) {
        return optionsData.map(opt => ({
          value: opt.value,
          label: opt.labels[language] || opt.labels['en'] || Object.values(opt.labels)[0] || opt.value
        }));
      }
      return optionsData;
    }

    // If options is an i18n object with arrays per language
    if (typeof optionsData === 'object' && !Array.isArray(optionsData)) {
      const langOptions = optionsData[language] || optionsData['en'] || Object.values(optionsData)[0];
      if (Array.isArray(langOptions)) {
        return langOptions;
      }
    }

    return [];
  };

  // Handle file upload
  const handleUploadFile = useCallback((file) => {
    setUploading(true);
    setUploadError('');

    return fileService.uploadFile(file, (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      setUploadPercentComplete(percentCompleted);
    }).then(response => {
      if (response.fileId) {
        onChange(question, JSON.stringify({ filename: response.fileId, rename: file.name }));
      }
      setUploaded(response.fileId !== '');
      setUploadError(response.error || '');
      setUploading(false);
      return response.fileId;
    }).catch(err => {
      setUploadError(err.message || 'Upload failed');
      setUploading(false);
    });
  }, [question, onChange]);

  // Handle standard input change
  const handleChange = useCallback((event) => {
    const newValue = event && event.target ? event.target.value : event;
    onChange(question, newValue);
  }, [question, onChange]);

  // Handle checkbox change
  const handleCheckChange = useCallback((event) => {
    const newValue = event.target.checked;
    onChange(question, newValue ? 'true' : 'false');
  }, [question, onChange]);

  // Handle dropdown change
  const handleDropdownChange = useCallback((name, selected) => {
    onChange(question, selected ? selected.value : '');
  }, [question, onChange]);

  // Handle country change
  const handleCountryChange = useCallback((id, value) => {
    onChange(question, value || '');
  }, [question, onChange]);

  // Render the appropriate form control based on question type
  const renderControl = () => {
    const options = getOptions();
    const questionType = question.type;
    const settings = question.settings || {};

    switch (questionType) {
      case 'short-text':
        return (
          <FormTextBox
            id={id}
            name={id}
            type="text"
            label={description}
            placeholder={placeholder}
            onChange={handleChange}
            value={value || ''}
            showError={!!validationError}
            errorText={validationError}
            isDisabled={disabled}
          />
        );

      case 'long-text':
      case 'long_text':
        return (
          <FormTextArea
            id={id}
            name={id}
            label={description}
            placeholder={placeholder}
            onChange={handleChange}
            value={value || ''}
            rows={5}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'markdown':
        return (
          <FormTextArea
            id={id}
            name={id}
            label={description}
            placeholder={placeholder || t('Markdown supported')}
            onChange={handleChange}
            value={value || ''}
            rows={8}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'numeric':
      case 'numeric-text':
        return (
          <FormTextBox
            id={id}
            name={id}
            type="number"
            label={description}
            placeholder={placeholder}
            onChange={handleChange}
            value={value || ''}
            showError={!!validationError}
            errorText={validationError}
            min={settings.min_value}
            isDisabled={disabled}
          />
        );

      case 'combobox':
      case 'multi-choice':
        return (
          <FormSelect
            id={id}
            name={id}
            options={options}
            label={description}
            placeholder={placeholder || t('Select an option...')}
            onChange={handleDropdownChange}
            defaultValue={value || null}
            showError={!!validationError}
            errorText={validationError}
            searchable={options.length > 10}
          />
        );

      case 'checkboxes':
      case 'multi-checkbox':
        return (
          <FormMultiCheckbox
            id={id}
            name={id}
            label={description}
            placeholder={placeholder}
            options={options}
            defaultValue={value || ''}
            onChange={handleChange}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'radio':
      case 'single-choice':
        return (
          <FormRadio
            id={id}
            name={id}
            label={description}
            options={options}
            value={value || ''}
            onChange={handleChange}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'single-checkbox':
        return (
          <FormCheckbox
            id={id}
            name={id}
            label={description}
            placeholder={placeholder}
            onChange={handleCheckChange}
            value={value === 'true' || value === true}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'date':
        return (
          <FormDate
            id={id}
            name={id}
            label={description}
            value={value || ''}
            placeholder={placeholder}
            onChange={handleChange}
            showError={!!validationError}
            errorText={validationError}
            required={question.is_required}
            disabled={disabled}
          />
        );

      case 'file':
        return (
          <FormFileUpload
            id={id}
            name={id}
            label={description}
            value={value}
            showError={!!validationError || !!uploadError}
            errorText={validationError || uploadError}
            uploading={uploading}
            uploadPercentComplete={uploadPercentComplete}
            uploadFile={handleUploadFile}
            uploaded={uploaded}
            options={settings.accepted_extensions ? { accept: settings.accepted_extensions.join(',') } : null}
          />
        );

      case 'multi-file':
        return (
          <FormMultiFile
            id={id}
            name={id}
            label={description}
            value={value}
            onChange={handleChange}
            uploadFile={handleUploadFile}
            errorText={validationError || uploadError}
            placeholder={placeholder}
            options={settings}
          />
        );

      case 'country':
        return (
          <FormCountry
            id={id}
            name={id}
            label={description}
            value={value || ''}
            placeholder={placeholder || t('Select a country...')}
            onChange={handleCountryChange}
            options={settings.countryOptions || {}}
            showError={!!validationError}
            errorText={validationError}
          />
        );

      case 'information':
      case 'sub-heading':
        return description ? (
          <div className="question-information">
            <MarkdownRenderer source={description} />
          </div>
        ) : null;

      default:
        return (
          <p className="text-danger">
            {t('Unknown question type')}: {questionType}
          </p>
        );
    }
  };

  // Don't render headline for information/sub-heading types
  const isDisplayOnly = ['information', 'sub-heading'].includes(question.type);
  const headlineClass = isDisplayOnly ? 'question-headline display-only' : 'question-headline';

  return (
    <div className={`question-renderer ${validationError ? 'has-error' : ''}`}>
      {headline && (
        <div className={headlineClass}>
          {question.is_required && !isDisplayOnly && (
            <span className="required-indicator" aria-label={t('Required')}>*</span>
          )}
          {isDisplayOnly ? (
            <h3 className="display-headline">{headline}</h3>
          ) : (
            <h4 className="question-title">{headline}</h4>
          )}
        </div>
      )}
      <div className="question-control">
        {renderControl()}
      </div>
    </div>
  );
};

export default QuestionRenderer;
