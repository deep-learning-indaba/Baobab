import React from 'react';
import './TranslatableFieldGroup.css';

const TranslatableFieldGroup = ({
  label,
  fieldName,
  values,
  languages,
  onChange,
  required = false,
  multiline = false,
  placeholder = '',
  disabled = false
}) => {
  const handleChange = (langCode, value) => {
    onChange(langCode, value);
  };

  return (
    <div className="translatable-field-group">
      <label className="translatable-field-label">
        {label}
        {required && <span className="required-indicator">*</span>}
      </label>
      <div className="translatable-inputs-container">
        {languages.map((language) => {
          const value = values[language.code] || '';
          const hasError = required && !value;
          
          return (
            <div key={language.code} className="translatable-input-wrapper">
              <div className="language-badge" title={language.description}>
                {language.code.toUpperCase()}
              </div>
              {multiline ? (
                <textarea
                  className={`translatable-textarea ${hasError ? 'has-error' : ''}`}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  placeholder={placeholder}
                  disabled={disabled}
                  rows={3}
                />
              ) : (
                <input
                  type="text"
                  className={`translatable-input ${hasError ? 'has-error' : ''}`}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  placeholder={placeholder}
                  disabled={disabled}
                />
              )}
              {hasError && (
                <span className="field-error">Required in all languages</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TranslatableFieldGroup;
