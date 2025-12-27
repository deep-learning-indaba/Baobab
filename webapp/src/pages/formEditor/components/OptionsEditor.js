import React from 'react';
import './OptionsEditor.css';

const OptionsEditor = ({
  options,
  languages,
  onChange,
  onAdd,
  onDelete,
  onUpdateValue,
  onUpdateLabel,
  t
}) => {
  const [newOptionValue, setNewOptionValue] = React.useState('');
  const [newOptionLabels, setNewOptionLabels] = React.useState(
    languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {})
  );

  const handleAddOption = () => {
    const trimmedValue = newOptionValue.trim();
    
    if (!trimmedValue) {
      return;
    }

    const allLabelsEmpty = languages.every(lang => ! (newOptionLabels[lang.code] ? newOptionLabels[lang.code].trim() : ''));
    if (allLabelsEmpty) {
      return;
    }

    const isDuplicate = options.some(opt => opt.value === trimmedValue);
    if (isDuplicate) {
      alert(t('Value must be unique'));
      return;
    }

    onAdd({
      value: trimmedValue,
      labels: { ...newOptionLabels }
    });

    setNewOptionValue('');
    setNewOptionLabels(languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {}));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddOption();
    }
  };

  return (
    <div className="options-editor">
      <label className="options-editor-label">
        {t('Options')}
        <span className="required-indicator">*</span>
      </label>
      
      {options.length > 0 && (
        <div className="options-table">
          <div className="options-header">
            <div className="option-value-col">{t('Value')}</div>
            {languages.map(lang => (
              <div key={lang.code} className="option-label-col">
                {lang.description}
              </div>
            ))}
            <div className="option-actions-col"></div>
          </div>
          
          <div className="options-body">
            {options.map((option) => (
              <div key={option.id} className="option-row">
                <div className="option-value-col">
                  <input
                    type="text"
                    className="option-input"
                    value={option.value}
                    onChange={(e) => onUpdateValue(option.id, e.target.value)}
                    placeholder={t('value')}
                  />
                </div>
                {languages.map(lang => (
                  <div key={lang.code} className="option-label-col">
                    <input
                      type="text"
                      className="option-input"
                      value={(option.labels && option.labels[lang.code]) || ''}
                      onChange={(e) => onUpdateLabel(option.id, lang.code, e.target.value)}
                      placeholder={t('label')}
                    />
                  </div>
                ))}
                <div className="option-actions-col">
                  <button
                    type="button"
                    className="delete-option-btn"
                    onClick={() => onDelete(option.id)}
                    title={t('Delete option')}
                  >
                    <i className="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="add-option-row">
        <div className="option-value-col">
          <input
            type="text"
            className="option-input"
            value={newOptionValue}
            onChange={(e) => setNewOptionValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t('New option value')}
          />
        </div>
        {languages.map(lang => (
          <div key={lang.code} className="option-label-col">
            <input
              type="text"
              className="option-input"
              value={newOptionLabels[lang.code] || ''}
              onChange={(e) => setNewOptionLabels({ ...newOptionLabels, [lang.code]: e.target.value })}
              onKeyPress={handleKeyPress}
              placeholder={t('Label in {{lang}}', { lang: lang.description })}
            />
          </div>
        ))}
        <div className="option-actions-col">
          <button
            type="button"
            className="add-option-btn"
            onClick={handleAddOption}
            title={t('Add option')}
          >
            <i className="fas fa-plus-circle"></i>
          </button>
        </div>
      </div>

      {options.length === 0 && (
        <div className="options-empty-state">
          {t('No options yet. Add at least one option.')}
        </div>
      )}
    </div>
  );
};

export default OptionsEditor;
