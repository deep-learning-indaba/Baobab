import React, { useState, useEffect } from 'react';
import VisibilityExpressionEditor from './VisibilityExpressionEditor';
import { formServices } from '../../../services/form/form.service';

const FormSettingsPanel = ({ form, onChange, onClose, t }) => {
  const [availableForms, setAvailableForms] = useState([]);
  const [loadingForms, setLoadingForms] = useState(false);

  useEffect(() => {
    const fetchAvailableForms = async () => {
      setLoadingForms(true);
      try {
        const response = await formServices.getFormList({ is_active: true });
        if (response.forms) {
          setAvailableForms(response.forms.filter(f => f.id !== form.id));
        }
      } catch (error) {
        console.error('Error fetching forms:', error);
      } finally {
        setLoadingForms(false);
      }
    };
    fetchAvailableForms();
  }, [form.id]);

  const handleChange = (field, value) => onChange(field, value);
  const handleSettingsChange = (settingKey, value) =>
    onChange('settings', { ...form.settings, [settingKey]: value });

  const sectionHeadingCls = "text-base font-semibold text-foreground mt-0 mb-4 pb-2 border-b-2 border-border";

  const ToggleRow = ({ checked, onChange: onChangeProp, title, description }) => (
    <label className="flex items-center gap-4 p-4 border border-border rounded-lg cursor-pointer hover:bg-surface-low transition-colors mb-3 last:mb-0">
      <input type="checkbox" className="sr-only" checked={checked} onChange={(e) => onChangeProp(e.target.checked)} />
      <span className="form-toggle" />
      <div className="flex flex-col gap-0.5 flex-1">
        <span className="font-medium text-foreground text-sm">{title}</span>
        <span className="text-sm text-muted-foreground leading-snug">{description}</span>
      </div>
    </label>
  );

  return (
    /* Overlay */
    <div className="fixed inset-0 bg-black/50 flex justify-end z-[1000]" onClick={onClose}>
      {/* Panel */}
      <div
        className="bg-white w-full max-w-[500px] h-screen overflow-y-auto shadow-elevated flex flex-col animate-slide-in-panel"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-5 border-b border-border bg-surface flex-shrink-0">
          <h2 className="text-xl font-semibold text-foreground m-0">{t('Form Settings')}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('Close')}
            className="p-2 text-muted-foreground hover:text-foreground text-xl transition-colors border-none bg-transparent cursor-pointer"
          >
            <i className="fas fa-times"></i>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <section className="mb-8">
            <h3 className={sectionHeadingCls}>{t('Display Settings')}</h3>
            <ToggleRow
              checked={form.settings.page_per_section || false}
              onChange={(v) => handleSettingsChange('page_per_section', v)}
              title={t('Display each section as a separate page')}
              description={t('Users will navigate between sections using Next/Previous buttons')}
            />
          </section>

          <section className="mb-8">
            <h3 className={sectionHeadingCls}>{t('Submission Settings')}</h3>
            <ToggleRow
              checked={form.multiple_responses || false}
              onChange={(v) => handleChange('multiple_responses', v)}
              title={t('Allow multiple responses')}
              description={t('Users can submit the form multiple times')}
            />
            <ToggleRow
              checked={form.allow_edits !== false}
              onChange={(v) => handleChange('allow_edits', v)}
              title={t('Allow editing after submission')}
              description={t('Users can edit their responses after submitting. If disabled, responses cannot be edited once submitted.')}
            />
          </section>

          <section className="mb-8">
            <VisibilityExpressionEditor
              expression={form.visibility_expression}
              onChange={(value) => handleChange('visibility_expression', value)}
            />
          </section>

          <section className="mb-8">
            <h3 className={sectionHeadingCls}>{t('Form Linking')}</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-foreground mb-2">{t('Link to Form')}</label>
              <select
                value={form.linked_form_id || ''}
                onChange={(e) => handleChange('linked_form_id', e.target.value ? parseInt(e.target.value) : null)}
                disabled={loadingForms}
                className="w-full px-3 py-2 border border-border rounded-md text-sm bg-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring disabled:bg-surface disabled:cursor-not-allowed"
              >
                <option value="">{t('No linked form')}</option>
                {availableForms.map(f => (
                  <option key={f.id} value={f.id}>
                    {typeof f.name === 'object' ? (f.name.en || Object.values(f.name)[0]) : f.name}
                  </option>
                ))}
              </select>
              <span className="block text-xs text-muted-foreground italic mt-1">
                {t('Link this form to another form to pre-populate responses')}
              </span>
            </div>
          </section>

          <section className="mb-8">
            <h3 className={sectionHeadingCls}>{t('Form Status')}</h3>
            <ToggleRow
              checked={form.is_open || false}
              onChange={(v) => handleChange('is_open', v)}
              title={t('Form is open')}
              description={t('Users can submit responses to this form')}
            />
            <ToggleRow
              checked={form.is_active || false}
              onChange={(v) => handleChange('is_active', v)}
              title={t('Form is active')}
              description={t('Inactive forms are hidden from users')}
            />
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border bg-surface flex-shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="w-full py-3 bg-primary text-white rounded-md font-medium text-sm hover:bg-primary-container transition-colors"
          >
            {t('Close')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FormSettingsPanel;
