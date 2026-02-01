import React, { useState, useEffect } from 'react';
import VisibilityExpressionEditor from './VisibilityExpressionEditor';
import { formServices } from '../../../services/form/form.service';
import './FormSettingsPanel.css';

const FormSettingsPanel = ({ form, onChange, onClose, t }) => {
  const [availableForms, setAvailableForms] = useState([]);
  const [loadingForms, setLoadingForms] = useState(false);

  useEffect(() => {
    const fetchAvailableForms = async () => {
      setLoadingForms(true);
      try {
        const response = await formServices.getFormList({ is_active: true });
        if (response.forms) {
          const forms = response.forms.filter(f => f.id !== form.id);
          setAvailableForms(forms);
        }
      } catch (error) {
        console.error('Error fetching forms:', error);
      } finally {
        setLoadingForms(false);
      }
    };

    fetchAvailableForms();
  }, [form.id]);

  const handleChange = (field, value) => {
    onChange(field, value);
  };

  const handleSettingsChange = (settingKey, value) => {
    onChange('settings', {
      ...form.settings,
      [settingKey]: value
    });
  };

  return (
    <div className="form-settings-overlay" onClick={onClose}>
      <div className="form-settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-panel-header">
          <h2>{t('Form Settings')}</h2>
          <button
            type="button"
            className="close-settings-btn"
            onClick={onClose}
            aria-label={t('Close')}
          >
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div className="settings-panel-body">
          <section className="settings-section">
            <h3>{t('Display Settings')}</h3>
            <label className="settings-checkbox">
              <input
                type="checkbox"
                checked={form.settings.page_per_section || false}
                onChange={(e) => handleSettingsChange('page_per_section', e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <div className="checkbox-label">
                <span className="checkbox-title">{t('Display each section as a separate page')}</span>
                <span className="checkbox-description">
                  {t('Users will navigate between sections using Next/Previous buttons')}
                </span>
              </div>
            </label>
          </section>

          <section className="settings-section">
            <h3>{t('Submission Settings')}</h3>
            <label className="settings-checkbox">
              <input
                type="checkbox"
                checked={form.multiple_responses || false}
                onChange={(e) => handleChange('multiple_responses', e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <div className="checkbox-label">
                <span className="checkbox-title">{t('Allow multiple responses')}</span>
                <span className="checkbox-description">
                  {t('Users can submit the form multiple times')}
                </span>
              </div>
            </label>

            <label className="settings-checkbox">
              <input
                type="checkbox"
                checked={form.allow_edits !== false}
                onChange={(e) => handleChange('allow_edits', e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <div className="checkbox-label">
                <span className="checkbox-title">{t('Allow editing after submission')}</span>
                <span className="checkbox-description">
                  {t('Users can edit their responses after submitting. If disabled, responses cannot be edited once submitted.')}
                </span>
              </div>
            </label>
          </section>

          <section className="settings-section">
            <VisibilityExpressionEditor
              expression={form.visibility_expression}
              onChange={(value) => handleChange('visibility_expression', value)}
            />
          </section>

          <section className="settings-section">
            <h3>{t('Form Linking')}</h3>
            <div className="settings-field">
              <label>{t('Link to Form')}</label>
              <select
                value={form.linked_form_id || ''}
                onChange={(e) => handleChange('linked_form_id', e.target.value ? parseInt(e.target.value) : null)}
                className="settings-select"
                disabled={loadingForms}
              >
                <option value="">{t('No linked form')}</option>
                {availableForms.map(f => (
                  <option key={f.id} value={f.id}>
                    {typeof f.name === 'object' ? (f.name.en || Object.values(f.name)[0]) : f.name}
                  </option>
                ))}
              </select>
              <span className="settings-hint">
                {t('Link this form to another form to pre-populate responses')}
              </span>
            </div>
          </section>

          <section className="settings-section">
            <h3>{t('Form Status')}</h3>
            <label className="settings-checkbox">
              <input
                type="checkbox"
                checked={form.is_open || false}
                onChange={(e) => handleChange('is_open', e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <div className="checkbox-label">
                <span className="checkbox-title">{t('Form is open')}</span>
                <span className="checkbox-description">
                  {t('Users can submit responses to this form')}
                </span>
              </div>
            </label>

            <label className="settings-checkbox">
              <input
                type="checkbox"
                checked={form.is_active || false}
                onChange={(e) => handleChange('is_active', e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <div className="checkbox-label">
                <span className="checkbox-title">{t('Form is active')}</span>
                <span className="checkbox-description">
                  {t('Inactive forms are hidden from users')}
                </span>
              </div>
            </label>
          </section>
        </div>

        <div className="settings-panel-footer">
          <button
            type="button"
            className="close-settings-footer-btn"
            onClick={onClose}
          >
            {t('Close')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FormSettingsPanel;
