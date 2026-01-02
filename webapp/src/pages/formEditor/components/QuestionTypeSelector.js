import React from 'react';
import { default as ReactSelect } from 'react-select';
import './QuestionTypeSelector.css';

const QuestionTypeSelector = ({ value, onChange, t, includeReviewTypes = false }) => {
  const baseOptions = [
    {
      value: 'short-text',
      label: t('Short Text'),
      icon: 'fa-align-left'
    },
    {
      value: 'long-text',
      label: t('Long Text'),
      icon: 'fa-align-justify'
    },
    {
      value: 'markdown',
      label: t('Markdown'),
      icon: 'fa-markdown'
    },
    {
      value: 'single-choice',
      label: t('Single Choice (Radio)'),
      icon: 'fa-dot-circle'
    },
    {
      value: 'combobox',
      label: t('Combobox (Dropdown)'),
      icon: 'fa-caret-square-down'
    },
    {
      value: 'checkboxes',
      label: t('Checkboxes'),
      icon: 'fa-check-square'
    },
    {
      value: 'single-checkbox',
      label: t('Single Checkbox'),
      icon: 'fa-check'
    },
    {
      value: 'file',
      label: t('File Upload'),
      icon: 'fa-file-upload'
    },
    {
      value: 'multi-file',
      label: t('Multiple File Upload'),
      icon: 'fa-cloud-upload-alt'
    },
    {
      value: 'date',
      label: t('Date'),
      icon: 'fa-calendar-alt'
    },
    {
      value: 'numeric',
      label: t('Numeric'),
      icon: 'fa-hashtag'
    },
    {
      value: 'sub-heading',
      label: t('Sub-heading'),
      icon: 'fa-heading'
    },
    {
      value: 'reference',
      label: t('Reference Request'),
      icon: 'fa-user-friends'
    },
    {
      value: 'linked-form-question',
      label: t('Linked Form Question'),
      icon: 'fa-link'
    },
    {
      value: 'country',
      label: t('Country Selector'),
      icon: 'fa-globe-africa'
    }
  ];

  const reviewOnlyOptions = [
    {
      value: 'radio',
      label: t('Radio (Score)'),
      icon: 'fa-star'
    },
    {
      value: 'information',
      label: t('Information Display'),
      icon: 'fa-info-circle'
    }
  ];

  const options = includeReviewTypes 
    ? [...baseOptions, ...reviewOnlyOptions]
    : baseOptions;

  const formatOptionLabel = ({ label, icon }) => (
    <div className="question-type-option">
      <i className={`fas ${icon} question-type-icon`}></i>
      <span>{label}</span>
    </div>
  );

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <ReactSelect
      options={options}
      value={selectedOption || null}
      onChange={(option) => onChange(option ? option.value : null)}
      placeholder={t('Select question type')}
      formatOptionLabel={formatOptionLabel}
      className="question-type-selector"
      classNamePrefix="question-type-select"
      isClearable={false}
      styles={{
        control: (base, state) => ({
          ...base,
          minHeight: '38px',
          borderColor: state.isFocused ? '#3b82f6' : '#d1d5db',
          boxShadow: state.isFocused ? '0 0 0 3px rgba(59, 130, 246, 0.1)' : 'none',
          '&:hover': {
            borderColor: '#3b82f6'
          }
        }),
        option: (base, state) => ({
          ...base,
          backgroundColor: state.isSelected 
            ? '#3b82f6' 
            : state.isFocused 
              ? '#eff6ff' 
              : 'white',
          color: state.isSelected ? 'white' : '#333',
          cursor: 'pointer'
        })
      }}
    />
  );
};

export default QuestionTypeSelector;
