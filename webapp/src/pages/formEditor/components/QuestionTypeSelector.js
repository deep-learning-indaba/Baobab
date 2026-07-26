import React from 'react';
import { default as ReactSelect } from 'react-select';

const QuestionTypeSelector = ({ value, onChange, t, includeReviewTypes = false, linkedFormId = null, hasError = false }) => {
  const baseOptions = [
    { value: 'short-text',    label: t('Short Text'),             icon: 'fa-align-left' },
    { value: 'long-text',     label: t('Long Text'),              icon: 'fa-align-justify' },
    { value: 'markdown',      label: t('Markdown'),               icon: 'fa-file-alt' },
    { value: 'single-choice', label: t('Single Choice (Radio)'),  icon: 'fa-dot-circle' },
    { value: 'combobox',      label: t('Combobox (Dropdown)'),    icon: 'fa-caret-square-down' },
    { value: 'checkboxes',    label: t('Checkboxes'),             icon: 'fa-check-square' },
    { value: 'single-checkbox', label: t('Single Checkbox'),      icon: 'fa-check' },
    { value: 'file',          label: t('File Upload'),            icon: 'fa-file-upload' },
    { value: 'multi-file',    label: t('Multiple File Upload'),   icon: 'fa-cloud-upload-alt' },
    { value: 'date',          label: t('Date'),                   icon: 'fa-calendar-alt' },
    { value: 'numeric',       label: t('Numeric'),                icon: 'fa-hashtag' },
    { value: 'sub-heading',   label: t('Sub-heading'),            icon: 'fa-heading' },
    { value: 'country',       label: t('Country Selector'),        icon: 'fa-globe-africa' },
  ];

  // 'reference' has no implementation in the form renderer (the reference
  // request flow is still tied to the legacy response model), so it is not
  // offered for new questions. Kept selectable only for a form that already has
  // one, so editing such a form doesn't silently blank its type.
  if (value === 'reference') {
    baseOptions.push({
      value: 'reference',
      label: t('Reference Request (not supported)'),
      icon: 'fa-user-friends'
    });
  }

  if (linkedFormId || value === 'linked-form-question') {
    baseOptions.push({ value: 'linked-form-question', label: t('Linked Form Question'), icon: 'fa-link' });
  }

  const reviewOnlyOptions = [
    { value: 'radio',       label: t('Radio (Score)'),        icon: 'fa-star' },
    { value: 'information', label: t('Information Display'),   icon: 'fa-info-circle' },
  ];

  const options = includeReviewTypes ? [...baseOptions, ...reviewOnlyOptions] : baseOptions;

  const formatOptionLabel = ({ label, icon }) => (
    <div className="flex items-center gap-2">
      <i className={`fas ${icon} w-4 text-center text-muted-foreground`}></i>
      <span>{label}</span>
    </div>
  );

  // Read the design tokens rather than hard-coding hexes, so this control tracks
  // the theme like the rest of the editor.
  const token = (name, fallback) => {
    if (typeof window === 'undefined' || !window.getComputedStyle) return fallback;
    const value = window.getComputedStyle(document.documentElement).getPropertyValue(name);
    return (value && value.trim()) || fallback;
  };
  const actionColor = token('--clr-action', '#0132c5');
  const borderColor = token('--clr-outline-variant', '#bfc9c1');
  const errorColor = token('--clr-error', '#dc3545');

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <ReactSelect
      options={options}
      value={selectedOption || null}
      onChange={(option) => onChange(option ? option.value : null)}
      placeholder={t('Select question type')}
      formatOptionLabel={formatOptionLabel}
      isClearable={false}
      styles={{
        control: (base, state) => ({
          ...base,
          minHeight: '38px',
          borderColor: hasError ? errorColor : (state.isFocused ? actionColor : borderColor),
          boxShadow: state.isFocused ? `0 0 0 3px ${actionColor}1a` : 'none',
          '&:hover': { borderColor: hasError ? errorColor : actionColor }
        }),
        option: (base, state) => ({
          ...base,
          backgroundColor: state.isSelected ? actionColor : state.isFocused ? `${actionColor}14` : 'white',
          color: state.isSelected ? 'white' : 'inherit',
          cursor: 'pointer'
        })
      }}
    />
  );
};

export default QuestionTypeSelector;
