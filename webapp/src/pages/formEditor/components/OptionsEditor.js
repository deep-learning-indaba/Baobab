import React from 'react';

const OptionsEditor = ({ options, languages, onAdd, onDelete, onUpdateValue, onUpdateLabel, t }) => {
  const [newOptionValue, setNewOptionValue] = React.useState('');
  const [newOptionLabels, setNewOptionLabels] = React.useState(
    languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {})
  );

  const inputCls = "w-full px-2 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-ring";

  const handleAddOption = () => {
    const trimmedValue = newOptionValue.trim();
    if (!trimmedValue) return;
    const allLabelsEmpty = languages.every(lang => !(newOptionLabels[lang.code] ? newOptionLabels[lang.code].trim() : ''));
    if (allLabelsEmpty) return;
    if (options.some(opt => opt.value === trimmedValue)) { alert(t('Value must be unique')); return; }
    onAdd({ value: trimmedValue, labels: { ...newOptionLabels } });
    setNewOptionValue('');
    setNewOptionLabels(languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {}));
  };

  const handleKeyPress = (e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddOption(); } };

  return (
    <div className="mb-6">
      <label className="block font-semibold text-foreground text-sm mb-2">
        {t('Options')}
        <span className="text-error ml-1">*</span>
      </label>

      {options.length > 0 && (
        <div className="border border-border rounded-md overflow-hidden mb-2">
          {/* Table header */}
          <div className="flex bg-surface px-2 py-2 text-xs font-semibold text-muted-foreground border-b border-border gap-2">
            <div className="flex-1 min-w-[120px]">{t('Value')}</div>
            {languages.map(lang => (
              <div key={lang.code} className="[flex:2] min-w-[150px]">{lang.description}</div>
            ))}
            <div className="w-10"></div>
          </div>

          {/* Rows */}
          <div className="max-h-[400px] overflow-y-auto">
            {options.map((option) => (
              <div key={option.id} className="flex gap-2 px-2 py-2 border-b border-border last:border-0 hover:bg-surface transition-colors items-center">
                <div className="flex-1 min-w-[120px]">
                  <input type="text" className={inputCls} value={option.value} onChange={(e) => onUpdateValue(option.id, e.target.value)} placeholder={t('value')} />
                </div>
                {languages.map(lang => (
                  <div key={lang.code} className="[flex:2] min-w-[150px]">
                    <input type="text" className={inputCls} value={(option.labels && option.labels[lang.code]) || ''} onChange={(e) => onUpdateLabel(option.id, lang.code, e.target.value)} placeholder={t('label')} />
                  </div>
                ))}
                <div className="w-10 flex justify-center">
                  <button type="button" onClick={() => onDelete(option.id)} title={t('Delete option')} className="p-1 text-muted-foreground hover:text-error transition-colors border-none bg-transparent cursor-pointer text-base">
                    <i className="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add row */}
      <div className="flex gap-2 px-2 py-2 mt-2 bg-surface border border-dashed border-border rounded-md items-center">
        <div className="flex-1 min-w-[120px]">
          <input type="text" className={inputCls} value={newOptionValue} onChange={(e) => setNewOptionValue(e.target.value)} onKeyPress={handleKeyPress} placeholder={t('New option value')} />
        </div>
        {languages.map(lang => (
          <div key={lang.code} className="[flex:2] min-w-[150px]">
            <input type="text" className={inputCls} value={newOptionLabels[lang.code] || ''} onChange={(e) => setNewOptionLabels({ ...newOptionLabels, [lang.code]: e.target.value })} onKeyPress={handleKeyPress} placeholder={t('Label in {{lang}}', { lang: lang.description })} />
          </div>
        ))}
        <div className="w-10 flex justify-center">
          <button type="button" onClick={handleAddOption} title={t('Add option')} className="p-1 text-muted-foreground hover:text-primary transition-colors border-none bg-transparent cursor-pointer text-lg">
            <i className="fas fa-plus-circle"></i>
          </button>
        </div>
      </div>

      {options.length === 0 && (
        <p className="text-center text-sm text-muted-foreground italic py-6 border border-dashed border-border rounded-md bg-surface mt-1">
          {t('No options yet. Add at least one option.')}
        </p>
      )}
    </div>
  );
};

export default OptionsEditor;
