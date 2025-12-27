import React from 'react';
import './QuestionSettingsEditor.css';

const QuestionSettingsEditor = ({ type, settings, onChange, languages, t }) => {
  const handleChange = (field, value) => {
    onChange({
      ...settings,
      [field]: value
    });
  };

  const handleArrayChange = (field, valueString) => {
    const values = valueString
      .split(',')
      .map(v => v.trim())
      .filter(v => v);
    handleChange(field, values);
  };

  if (type === 'file' || type === 'multi-file') {
    return (
      <div className="question-settings-editor">
        <h4 className="settings-title">{t('File Settings')}</h4>
        
        <div className="settings-field">
          <label>{t('Accepted Extensions')}</label>
          <input
            type="text"
            value={(settings.accepted_extensions || []).join(', ')}
            onChange={(e) => handleArrayChange('accepted_extensions', e.target.value)}
            placeholder={t('e.g., .pdf, .doc, .docx')}
            className="settings-input"
          />
          <span className="settings-hint">
            {t('Separate multiple extensions with commas')}
          </span>
        </div>

        <div className="settings-field">
          <label>{t('Maximum File Size (MB)')}</label>
          <input
            type="number"
            min="1"
            max="100"
            value={settings.max_file_size_mb || 10}
            onChange={(e) => handleChange('max_file_size_mb', parseInt(e.target.value) || 10)}
            className="settings-input"
          />
        </div>

        {type === 'multi-file' && (
          <div className="settings-field">
            <label>{t('Maximum Number of Files')}</label>
            <input
              type="number"
              min="1"
              max="20"
              value={settings.max_files || 5}
              onChange={(e) => handleChange('max_files', parseInt(e.target.value) || 5)}
              className="settings-input"
            />
          </div>
        )}
      </div>
    );
  }

  if (type === 'numeric') {
    return (
      <div className="question-settings-editor">
        <h4 className="settings-title">{t('Numeric Settings')}</h4>
        
        <div className="settings-row">
          <div className="settings-field">
            <label>{t('Minimum Value')}</label>
            <input
              type="number"
              value={settings.min_value ? settings.min_value : ''}
              onChange={(e) => handleChange('min_value', e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder={t('No minimum')}
              className="settings-input"
            />
          </div>

          <div className="settings-field">
            <label>{t('Maximum Value')}</label>
            <input
              type="number"
              value={settings.max_value ? settings.max_value : ''}
              onChange={(e) => handleChange('max_value', e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder={t('No maximum')}
              className="settings-input"
            />
          </div>
        </div>

        <div className="settings-field">
          <label>{t('Decimal Places')}</label>
          <input
            type="number"
            min="0"
            max="10"
            value={settings.decimal_places ? settings.decimal_places : 0}
            onChange={(e) => handleChange('decimal_places', parseInt(e.target.value) || 0)}
            className="settings-input"
          />
        </div>

        <div className="settings-field">
          <label>{t('Score Weight (for review questions)')}</label>
          <input
            type="number"
            min="0"
            step="0.1"
            value={settings.weight ? settings.weight : ''}
            onChange={(e) => handleChange('weight', e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder={t('Optional')}
            className="settings-input"
          />
        </div>
      </div>
    );
  }

  if (type === 'long-text' || type === 'markdown') {
    return (
      <div className="question-settings-editor">
        <h4 className="settings-title">{t('Text Length Settings')}</h4>
        
        <div className="settings-row">
          <div className="settings-field">
            <label>{t('Minimum Words')}</label>
            <input
              type="number"
              min="0"
              value={settings.min_words ? settings.min_words : ''}
              onChange={(e) => handleChange('min_words', e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder={t('No minimum')}
              className="settings-input"
            />
          </div>

          <div className="settings-field">
            <label>{t('Maximum Words')}</label>
            <input
              type="number"
              min="0"
              value={settings.max_words ? settings.max_words : ''}
              onChange={(e) => handleChange('max_words', e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder={t('No maximum')}
              className="settings-input"
            />
          </div>
        </div>
      </div>
    );
  }

  if (type === 'reference') {
    return (
      <div className="question-settings-editor">
        <h4 className="settings-title">{t('Reference Settings')}</h4>
        
        <div className="settings-row">
          <div className="settings-field">
            <label>{t('Minimum Referrals')}</label>
            <input
              type="number"
              min="0"
              value={settings.min_referrals ? settings.min_referrals : 1}
              onChange={(e) => handleChange('min_referrals', parseInt(e.target.value) || 1)}
              className="settings-input"
            />
          </div>

          <div className="settings-field">
            <label>{t('Maximum Referrals')}</label>
            <input
              type="number"
              min="1"
              value={settings.max_referrals ? settings.max_referrals : 3}
              onChange={(e) => handleChange('max_referrals', parseInt(e.target.value) || 3)}
              className="settings-input"
            />
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default QuestionSettingsEditor;
