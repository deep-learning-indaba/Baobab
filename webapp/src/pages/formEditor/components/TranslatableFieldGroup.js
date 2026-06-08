import React, { useState, useRef, useEffect } from 'react';
import { translationService } from '../../../services/translation';

const TranslatableFieldGroup = ({
  label,
  fieldName,
  values,
  languages,
  onChange,
  required = false,
  multiline = false,
  placeholder = '',
  disabled = false,
  autoTranslateEnabled = true
}) => {
  const [translating, setTranslating] = useState(false);
  const [manuallyEdited, setManuallyEdited] = useState({});
  const typingTimerRef = useRef({});
  const TYPING_DELAY = 1000;

  const handleChange = (langCode, value) => {
    onChange(langCode, value);
    setManuallyEdited(prev => ({ ...prev, [langCode]: true }));
    if (typingTimerRef.current[langCode]) clearTimeout(typingTimerRef.current[langCode]);
    if (autoTranslateEnabled && value && value.trim()) {
      typingTimerRef.current[langCode] = setTimeout(() => handleAutoTranslate(langCode, value), TYPING_DELAY);
    }
  };

  const handleAutoTranslate = async (sourceLang, sourceText) => {
    if (!sourceText || !sourceText.trim()) return;
    const targetLanguages = languages.map(lang => lang.code).filter(code => code !== sourceLang && !values[code] && !manuallyEdited[code]);
    if (targetLanguages.length === 0) return;
    setTranslating(true);
    try {
      const result = await translationService.translateText(sourceText, sourceLang, targetLanguages);
      if (result.translations && !result.error) {
        Object.entries(result.translations).forEach(([lang, translation]) => {
          if (translation && !manuallyEdited[lang]) onChange(lang, translation);
        });
      }
    } catch (error) {
      console.error('Auto-translation failed:', error);
    } finally {
      setTranslating(false);
    }
  };

  const handleRetranslate = async (targetLang) => {
    const sourceLang = languages[0].code;
    const sourceText = values[sourceLang];
    if (!sourceText || !sourceText.trim()) return;
    setTranslating(true);
    try {
      const result = await translationService.translateText(sourceText, sourceLang, [targetLang]);
      if (result.translations && result.translations[targetLang]) {
        onChange(targetLang, result.translations[targetLang]);
        setManuallyEdited(prev => ({ ...prev, [targetLang]: false }));
      }
    } catch (error) {
      console.error('Re-translation failed:', error);
    } finally {
      setTranslating(false);
    }
  };

  useEffect(() => {
    return () => { Object.values(typingTimerRef.current).forEach(timer => clearTimeout(timer)); };
  }, []);

  const inputCls = (hasError) =>
    `w-full px-3 py-2 border rounded-md text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-ring ${
      hasError ? 'border-error focus:ring-error/20' : 'border-border'
    } disabled:opacity-50 disabled:cursor-not-allowed`;

  return (
    <div className="mb-6">
      <label className="block font-semibold text-foreground text-sm mb-2">
        {label}
        {required && <span className="text-error ml-1">*</span>}
        {translating && (
          <span className="text-action text-sm ml-2 font-normal">
            <i className="fas fa-spinner fa-spin mr-1"></i>
            {' Translating...'}
          </span>
        )}
      </label>

      <div className="flex gap-4 flex-wrap">
        {languages.map((language, index) => {
          const value = values[language.code] || '';
          const hasError = required && !value;
          const isFirstLanguage = index === 0;
          const showRetranslateButton = autoTranslateEnabled && !isFirstLanguage && manuallyEdited[language.code] && values[languages[0].code];

          return (
            <div key={language.code} className="flex-1 min-w-[200px] flex flex-col gap-1">
              <span className="text-xs font-semibold text-muted-foreground uppercase px-2 py-0.5 bg-surface-mid rounded w-fit">
                {language.code.toUpperCase()}
              </span>
              {multiline ? (
                <textarea
                  className={`${inputCls(hasError)} resize-y min-h-[80px]`}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  placeholder={placeholder}
                  disabled={disabled || translating}
                  rows={3}
                />
              ) : (
                <input
                  type="text"
                  className={inputCls(hasError)}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  placeholder={placeholder}
                  disabled={disabled || translating}
                />
              )}
              {hasError && (
                <span className="text-error text-xs">Required in all languages</span>
              )}
              {showRetranslateButton && (
                <button
                  type="button"
                  onClick={() => handleRetranslate(language.code)}
                  disabled={translating}
                  title="Re-translate from first language"
                  className="inline-flex items-center gap-1 mt-0.5 px-2 py-1 text-xs text-action border border-action rounded hover:bg-action hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-fit"
                >
                  <i className="fas fa-sync-alt text-[10px]"></i> Re-translate
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TranslatableFieldGroup;
