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
import { countWords } from '../utils/validation';

const QuestionRenderer = ({
  question,
  value,
  onChange,
  language,
  validationError,
  disabled = false,
  linkedResponse = null,
  t
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadPercentComplete, setUploadPercentComplete] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [uploaded, setUploaded] = useState(false);

  const id = `question_${question.id}`;

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
  const settings = question.settings || {};

  const getOptions = () => {
    const optionsData = question.options;
    if (!optionsData) return [];
    if (Array.isArray(optionsData) && optionsData.length > 0 && optionsData[0].value !== undefined) {
      if (optionsData[0].labels) {
        return optionsData.map(opt => ({
          value: opt.value,
          label: opt.labels[language] || opt.labels['en'] || Object.values(opt.labels)[0] || opt.value
        }));
      }
      return optionsData;
    }
    if (typeof optionsData === 'object' && !Array.isArray(optionsData)) {
      const langOptions = optionsData[language] || optionsData['en'] || Object.values(optionsData)[0];
      if (Array.isArray(langOptions)) return langOptions;
    }
    return [];
  };

  const handleUploadFile = useCallback((file) => {
    // Enforce the configured size limit before spending an upload on it.
    const maxMb = (question.settings || {}).max_file_size_mb;
    if (maxMb && file && file.size > Number(maxMb) * 1024 * 1024) {
      setUploadError(t('This file is larger than the {{max}} MB limit', { max: maxMb }));
      return Promise.resolve(null);
    }
    setUploading(true);
    setUploadError('');
    return fileService.uploadFile(file, (progressEvent) => {
      setUploadPercentComplete(Math.round((progressEvent.loaded * 100) / progressEvent.total));
    }).then(response => {
      if (response.fileId) onChange(question, JSON.stringify({ filename: response.fileId, rename: file.name }));
      setUploaded(response.fileId !== '');
      setUploadError(response.error || '');
      setUploading(false);
      return response.fileId;
    }).catch(err => {
      setUploadError(err.message || t('Upload failed'));
      setUploading(false);
    });
  }, [question, onChange, t]);

  const handleChange = useCallback((event) => {
    onChange(question, event && event.target ? event.target.value : event);
  }, [question, onChange]);

  const handleCheckChange = useCallback((event) => {
    onChange(question, event.target.checked ? 'true' : 'false');
  }, [question, onChange]);

  const handleDropdownChange = useCallback((name, selected) => {
    onChange(question, selected ? selected.value : '');
  }, [question, onChange]);

  const handleCountryChange = useCallback((countryId, countryValue) => {
    onChange(question, countryValue || '');
  }, [question, onChange]);

  const infoPanel = (message) => (
    <div className="px-4 py-3 bg-surface border border-border rounded-md flex items-center gap-2 text-muted-foreground text-sm">
      <i className="fas fa-info-circle"></i>
      <span>{message}</span>
    </div>
  );

  const renderLinkedQuestion = () => {
    if (!question.linked_question_id || !linkedResponse) {
      return infoPanel(t('No linked response available'));
    }

    const linkedAnswer = linkedResponse.answers.find(ans => ans.question_id === question.linked_question_id);

    if (!linkedAnswer || !linkedAnswer.value) {
      return infoPanel(t('No answer provided in linked form'));
    }

    return (
      <div className="p-4 bg-action/5 border border-action/30 rounded-md">
        <div className="flex items-center gap-2 text-xs font-medium text-action mb-2">
          <i className="fas fa-link"></i>
          <span>{t('Value from linked form:')}</span>
        </div>
        <div className="p-3 bg-white border border-action/20 rounded text-sm text-foreground whitespace-pre-wrap break-words">
          {linkedAnswer.value}
        </div>
      </div>
    );
  };

  const renderControl = () => {
    const options = getOptions();

    switch (question.type) {
      case 'short-text':
        return (
          <FormTextBox id={id} name={id} type="text" placeholder={placeholder} onChange={handleChange}
            value={value || ''} showError={!!validationError} errorText={validationError} isDisabled={disabled} />
        );
      case 'long-text':
      case 'long_text':
        return (
          <FormTextArea id={id} name={id} placeholder={placeholder} onChange={handleChange}
            value={value || ''} rows={5} showError={!!validationError} errorText={validationError}
            isDisabled={disabled} disabled={disabled} />
        );
      case 'markdown':
        return (
          <FormTextArea id={id} name={id} placeholder={placeholder || t('Markdown supported')} onChange={handleChange}
            value={value || ''} rows={8} showError={!!validationError} errorText={validationError}
            isDisabled={disabled} disabled={disabled} />
        );
      case 'numeric':
      case 'numeric-text':
        return (
          <FormTextBox id={id} name={id} type="number" placeholder={placeholder} onChange={handleChange}
            value={value || ''} showError={!!validationError} errorText={validationError}
            min={settings.min_value} max={settings.max_value}
            step={settings.decimal_places ? Math.pow(10, -settings.decimal_places) : undefined}
            isDisabled={disabled} />
        );
      case 'combobox':
      case 'multi-choice':
        return (
          <FormSelect id={id} name={id} options={options} placeholder={placeholder || t('Select an option...')}
            onChange={handleDropdownChange} defaultValue={value || null} value={value || null}
            showError={!!validationError} errorText={validationError} searchable={options.length > 10}
            disabled={disabled} isDisabled={disabled} />
        );
      case 'checkboxes':
      case 'multi-checkbox':
        return (
          <FormMultiCheckbox id={id} name={id} placeholder={placeholder} options={options}
            defaultValue={value || ''} onChange={(v) => onChange(question, v)}
            showError={!!validationError} errorText={validationError} disabled={disabled} />
        );
      case 'radio':
      case 'single-choice':
        return (
          <FormRadio id={id} name={id} options={options} value={value || ''}
            onChange={(e) => onChange(question, e.target.value)}
            showError={!!validationError} errorText={validationError} disabled={disabled} />
        );
      case 'single-checkbox':
        // The label comes from the description, so don't also render the
        // description block above the control (it would appear twice).
        return (
          <FormCheckbox id={id} name={id} label={description || headline} placeholder={placeholder}
            onChange={handleCheckChange} value={value === 'true' || value === true}
            showError={!!validationError} errorText={validationError} disabled={disabled} />
        );
      case 'date':
        return (
          <FormDate id={id} name={id} value={value || ''} placeholder={placeholder} onChange={handleChange}
            showError={!!validationError} errorText={validationError} required={question.is_required} disabled={disabled} />
        );
      case 'file':
        return (
          <FormFileUpload id={id} name={id} value={value} showError={!!validationError || !!uploadError}
            errorText={validationError || uploadError} uploading={uploading}
            uploadPercentComplete={uploadPercentComplete} uploadFile={handleUploadFile} uploaded={uploaded}
            disabled={disabled}
            options={settings.accepted_extensions ? { accept: settings.accepted_extensions.join(',') } : null} />
        );
      case 'multi-file':
        return (
          <FormMultiFile id={id} name={id} value={value} onChange={handleChange}
            uploadFile={handleUploadFile} errorText={validationError || uploadError}
            placeholder={placeholder} options={settings} disabled={disabled} />
        );
      case 'country':
        return (
          <FormCountry id={id} name={id} value={value || ''} placeholder={placeholder || t('Select a country...')}
            onChange={handleCountryChange} options={settings.countryOptions || {}}
            showError={!!validationError} errorText={validationError} disabled={disabled} isDisabled={disabled} />
        );
      case 'information':
      case 'sub-heading':
        return description ? (
          <div className="text-muted-foreground leading-relaxed">
            <MarkdownRenderer source={description} />
          </div>
        ) : null;
      case 'linked-form-question':
        return renderLinkedQuestion();
      default:
        // Never show respondents a raw type name in red. An unrecognised type is
        // a form-configuration problem, not something they can act on.
        console.warn(`FormRenderer: no control for question type "${question.type}"`);
        return infoPanel(t('This question cannot be displayed. Please contact the organisers.'));
    }
  };

  const isDisplayOnly = ['information', 'sub-heading'].includes(question.type);
  // single-checkbox renders the description as its own label, so suppress the
  // separate description block for it.
  const shouldShowDescription = description && !isDisplayOnly && question.type !== 'single-checkbox';

  // Surface configured limits up front rather than only after a failed submit.
  const limitHints = [];
  if (['short-text', 'long-text', 'markdown'].includes(question.type)) {
    const { min_words: minWords, max_words: maxWords } = settings;
    if (minWords && maxWords) limitHints.push(t('Between {{min}} and {{max}} words', { min: minWords, max: maxWords }));
    else if (maxWords) limitHints.push(t('At most {{max}} words', { max: maxWords }));
    else if (minWords) limitHints.push(t('At least {{min}} words', { min: minWords }));
    if (minWords || maxWords) {
      limitHints.push(t('{{count}} words so far', { count: countWords(value) }));
    }
  }
  if (question.type === 'numeric') {
    const { min_value: minValue, max_value: maxValue } = settings;
    if (minValue !== undefined && minValue !== null && maxValue !== undefined && maxValue !== null) {
      limitHints.push(t('Between {{min}} and {{max}}', { min: minValue, max: maxValue }));
    } else if (maxValue !== undefined && maxValue !== null) {
      limitHints.push(t('At most {{max}}', { max: maxValue }));
    } else if (minValue !== undefined && minValue !== null) {
      limitHints.push(t('At least {{min}}', { min: minValue }));
    }
  }
  if (settings.accepted_extensions && settings.accepted_extensions.length > 0) {
    limitHints.push(t('Accepted file types: {{types}}', { types: settings.accepted_extensions.join(', ') }));
  }
  if (settings.max_file_size_mb) {
    limitHints.push(t('Maximum {{max}} MB', { max: settings.max_file_size_mb }));
  }

  return (
    <div
      id={`question-block-${question.id}`}
      className={`p-4 bg-surface rounded-md transition-colors text-left hover:bg-surface-low${validationError ? ' bg-error-container/10 border-l-[3px] border-error' : ''}`}
    >
      {headline && (
        <div className={isDisplayOnly ? 'mb-2' : 'mb-3'}>
          {isDisplayOnly ? (
            <h3 className="text-xl font-semibold text-foreground m-0">{headline}</h3>
          ) : (
            <h4 className="text-[1.0625rem] font-semibold text-foreground m-0 inline">
              {question.is_required && (
                <span className="text-error font-bold mr-1" aria-label={t('Required')}>*</span>
              )}
              {headline}
            </h4>
          )}
        </div>
      )}
      {shouldShowDescription && (
        <div className="text-muted-foreground text-[0.9375rem] leading-relaxed mt-2 mb-3">
          <MarkdownRenderer source={description} />
        </div>
      )}
      <div className="mt-2">
        {renderControl()}
      </div>
      {limitHints.length > 0 && (
        <p className="text-xs text-muted-foreground mt-2">{limitHints.join(' · ')}</p>
      )}
    </div>
  );
};

export default QuestionRenderer;
