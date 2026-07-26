import React, { useRef } from 'react';
import { translationService } from '../../../services/translation';

const TYPING_DELAY = 1000;
// Sentinel key for the not-yet-added "new option" draft row, which has no
// option.id yet - keeps it on the same manuallyEdited/translatingKeys/timer
// tracking as real options.
const NEW_OPTION_KEY = '__new__';

const OptionsEditor = ({ options, languages, onAdd, onDelete, onUpdateValue, onUpdateLabel, t, autoTranslateEnabled = true }) => {
  const [newOptionValue, setNewOptionValue] = React.useState('');
  const [newOptionLabels, setNewOptionLabels] = React.useState(
    languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {})
  );
  // Keyed by `${optionId}:${langCode}` - tracks labels the user typed directly,
  // so auto-translate never overwrites a hand-edited translation.
  const [manuallyEdited, setManuallyEdited] = React.useState({});
  // Keyed by `${optionId}:${langCode}` - only the specific target fields
  // currently being overwritten get disabled, never the field being typed
  // into (a blanket "disable while translating" drops keystrokes there).
  const [translatingKeys, setTranslatingKeys] = React.useState(() => new Set());
  const [addError, setAddError] = React.useState(null);
  const typingTimerRef = useRef({});
  // Bumped whenever a translation request is superseded (a later keystroke, or
  // the draft row being committed) so a late response can't repopulate a field
  // the user has already moved on from.
  const requestSeqRef = useRef({});
  const sourceLang = languages[0].code;

  // Labels that already had content when this editor mounted are treated as
  // authored translations and are never overwritten by auto-translate - only
  // by an explicit edit. Same reasoning as TranslatableFieldGroup.
  const [preExistingLabels] = React.useState(() => {
    const seed = {};
    (options || []).forEach(opt => {
      languages.forEach(lang => {
        const v = opt.labels && opt.labels[lang.code];
        if (v && String(v).trim()) seed[`${opt.id}:${lang.code}`] = true;
      });
    });
    return seed;
  });

  const isLabelProtected = (optionKey, langCode) => {
    const key = `${optionKey}:${langCode}`;
    return !!(manuallyEdited[key] || preExistingLabels[key]);
  };

  // Duplicate values break option lookup on submitted answers, so surface them
  // on the row itself rather than only at save time.
  const duplicateValues = React.useMemo(() => {
    const seen = new Set();
    const dupes = new Set();
    (options || []).forEach(opt => {
      const v = (opt.value || '').trim();
      if (!v) return;
      if (seen.has(v)) dupes.add(v);
      seen.add(v);
    });
    return dupes;
  }, [options]);

  const inputCls = "w-full px-2 py-1.5 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed";

  const handleAutoTranslate = async (optionKey, sourceText, updateFn) => {
    if (!sourceText || !sourceText.trim()) return;
    const targetLanguages = languages
      .map(l => l.code)
      .filter(code => code !== sourceLang && !isLabelProtected(optionKey, code));
    if (targetLanguages.length === 0) return;
    const seq = (requestSeqRef.current[optionKey] || 0) + 1;
    requestSeqRef.current[optionKey] = seq;
    setTranslatingKeys(prev => new Set([...prev, ...targetLanguages.map(code => `${optionKey}:${code}`)]));
    try {
      const result = await translationService.translateText(sourceText, sourceLang, targetLanguages);
      if (requestSeqRef.current[optionKey] !== seq) return;
      if (result.translations && !result.error) {
        Object.entries(result.translations).forEach(([lang, translation]) => {
          if (translation && !isLabelProtected(optionKey, lang)) updateFn(lang, translation);
        });
      }
    } catch (error) {
      console.error('Option auto-translation failed:', error);
    } finally {
      setTranslatingKeys(prev => {
        const next = new Set(prev);
        targetLanguages.forEach(code => next.delete(`${optionKey}:${code}`));
        return next;
      });
    }
  };

  // optionKey is option.id for existing rows, or NEW_OPTION_KEY for the
  // not-yet-added draft row; updateFn writes the value to the right place
  // (dispatch for existing options, local state for the draft).
  const handleLabelChange = (optionKey, langCode, value, updateFn) => {
    updateFn(langCode, value);
    setManuallyEdited(prev => ({ ...prev, [`${optionKey}:${langCode}`]: true }));
    if (langCode !== sourceLang) return;
    if (typingTimerRef.current[optionKey]) clearTimeout(typingTimerRef.current[optionKey]);
    if (autoTranslateEnabled && value && value.trim()) {
      typingTimerRef.current[optionKey] = setTimeout(() => handleAutoTranslate(optionKey, value, updateFn), TYPING_DELAY);
    }
  };

  React.useEffect(() => {
    return () => { Object.values(typingTimerRef.current).forEach(timer => clearTimeout(timer)); };
  }, []);

  const handleAddOption = () => {
    const trimmedValue = newOptionValue.trim();
    // Explain why nothing happened instead of silently ignoring the click.
    if (!trimmedValue) {
      setAddError(t('Enter a value for the option'));
      return;
    }
    const allLabelsEmpty = languages.every(lang => !(newOptionLabels[lang.code] ? newOptionLabels[lang.code].trim() : ''));
    if (allLabelsEmpty) {
      setAddError(t('Enter a label for the option'));
      return;
    }
    if (options.some(opt => opt.value === trimmedValue)) {
      setAddError(t('Option value "{{value}}" is already used', { value: trimmedValue }));
      return;
    }
    setAddError(null);
    onAdd({ value: trimmedValue, labels: { ...newOptionLabels } });
    setNewOptionValue('');
    setNewOptionLabels(languages.reduce((acc, lang) => ({ ...acc, [lang.code]: '' }), {}));
    if (typingTimerRef.current[NEW_OPTION_KEY]) clearTimeout(typingTimerRef.current[NEW_OPTION_KEY]);
    // Invalidate any translation already in flight for the draft row, or it
    // would land in the fields we just cleared.
    requestSeqRef.current[NEW_OPTION_KEY] = (requestSeqRef.current[NEW_OPTION_KEY] || 0) + 1;
    setTranslatingKeys(prev => {
      const next = new Set(prev);
      languages.forEach(lang => next.delete(`${NEW_OPTION_KEY}:${lang.code}`));
      return next;
    });
    setManuallyEdited(prev => {
      const next = { ...prev };
      Object.keys(next).forEach(key => { if (key.startsWith(`${NEW_OPTION_KEY}:`)) delete next[key]; });
      return next;
    });
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
              <div key={option.id} className="flex gap-2 px-2 py-2 border-b border-border last:border-0 hover:bg-surface transition-colors items-start">
                <div className="flex-1 min-w-[120px]">
                  <input
                    type="text"
                    className={`${inputCls} ${
                      !((option.value || '').trim()) || duplicateValues.has((option.value || '').trim())
                        ? 'border-error' : ''
                    }`}
                    value={option.value}
                    onChange={(e) => onUpdateValue(option.id, e.target.value)}
                    placeholder={t('value')}
                  />
                  {duplicateValues.has((option.value || '').trim()) && (
                    <span className="block text-error text-xs mt-1">{t('Duplicate value')}</span>
                  )}
                  {!((option.value || '').trim()) && (
                    <span className="block text-error text-xs mt-1">{t('Value is required')}</span>
                  )}
                </div>
                {languages.map(lang => (
                  <div key={lang.code} className="[flex:2] min-w-[150px]">
                    <input
                      type="text"
                      className={inputCls}
                      value={(option.labels && option.labels[lang.code]) || ''}
                      onChange={(e) => handleLabelChange(option.id, lang.code, e.target.value, (l, v) => onUpdateLabel(option.id, l, v))}
                      placeholder={t('label')}
                      disabled={translatingKeys.has(`${option.id}:${lang.code}`)}
                    />
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

      {options.length === 0 && (
        <p className="text-center text-sm text-muted-foreground italic py-6 border border-dashed border-border rounded-md bg-surface mb-2">
          {t('No options yet. Add at least one option.')}
        </p>
      )}

      {/* Add row */}
      <div className="flex gap-2 px-2 py-2 mt-2 bg-surface border border-dashed border-border rounded-md items-center">
        <div className="flex-1 min-w-[120px]">
          <input type="text" className={inputCls} value={newOptionValue} onChange={(e) => { setNewOptionValue(e.target.value); setAddError(null); }} onKeyDown={handleKeyPress} placeholder={t('New option value')} />
        </div>
        {languages.map(lang => (
          <div key={lang.code} className="[flex:2] min-w-[150px]">
            <input
              type="text"
              className={inputCls}
              value={newOptionLabels[lang.code] || ''}
              onChange={(e) => handleLabelChange(
                NEW_OPTION_KEY, lang.code, e.target.value,
                (l, v) => setNewOptionLabels(prev => ({ ...prev, [l]: v }))
              )}
              onKeyDown={handleKeyPress}
              placeholder={t('Label in {{lang}}', { lang: lang.description })}
              disabled={translatingKeys.has(`${NEW_OPTION_KEY}:${lang.code}`)}
            />
          </div>
        ))}
        <div className="w-10 flex justify-center">
          <button type="button" onClick={handleAddOption} title={t('Add option')} className="p-1 text-muted-foreground hover:text-primary transition-colors border-none bg-transparent cursor-pointer text-lg">
            <i className="fas fa-plus-circle"></i>
          </button>
        </div>
      </div>

      {addError && (
        <p className="flex items-center gap-2 text-error text-xs mt-1">
          <i className="fas fa-exclamation-circle"></i>
          {addError}
        </p>
      )}
    </div>
  );
};

export default OptionsEditor;
