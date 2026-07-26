import React, { useState, useRef, useEffect, memo } from 'react';
import { useTranslation } from 'react-i18next';
import { translationService } from '../../../services/translation';

const TranslatableFieldGroup = memo(({
  label,
  fieldName,
  values,
  languages,
  onChange,
  required = false,
  multiline = false,
  placeholder = '',
  disabled = false,
  autoTranslateEnabled = true,
  showErrors = false
}) => {
  const { t } = useTranslation();
  const [touched, setTouched] = useState({});
  const [translating, setTranslating] = useState(false);
  const [translatingTargets, setTranslatingTargets] = useState(() => new Set());
  const [manuallyEdited, setManuallyEdited] = useState({});
  const typingTimerRef = useRef({});
  // Monotonic id per language so a slow in-flight translation can't land on
  // top of text the user typed after it was requested.
  const requestSeqRef = useRef(0);
  const TYPING_DELAY = 1000;

  const primaryLang = languages[0] && languages[0].code;

  // Any language that already holds text when this field mounts is treated as
  // hand-written content: it may be a human-curated translation loaded from
  // the database, and auto-translate must not silently replace it.
  const [preExisting] = useState(() =>
    languages.reduce((acc, lang) => {
      acc[lang.code] = !!(values && values[lang.code] && String(values[lang.code]).trim());
      return acc;
    }, {})
  );

  const isProtected = (langCode) => manuallyEdited[langCode] || preExisting[langCode];

  const handleChange = (langCode, value) => {
    onChange(langCode, value);
    setManuallyEdited(prev => ({ ...prev, [langCode]: true }));
    if (typingTimerRef.current[langCode]) clearTimeout(typingTimerRef.current[langCode]);
    // Only the primary language seeds translations. Translating *from* whatever
    // field happens to have focus meant that editing the French text replaced
    // the English original with a machine translation of the French.
    if (langCode !== primaryLang) return;
    if (autoTranslateEnabled && value && value.trim()) {
      typingTimerRef.current[langCode] = setTimeout(() => handleAutoTranslate(langCode, value), TYPING_DELAY);
    }
  };

  const handleAutoTranslate = async (sourceLang, sourceText) => {
    if (!sourceText || !sourceText.trim()) return;
    // Fill in languages that are still empty and untouched. Anything the user
    // typed, or that arrived with content from the API, is left alone - use
    // the explicit Re-translate button to overwrite those.
    const targetLanguages = languages
      .map(lang => lang.code)
      .filter(code => code !== sourceLang && !isProtected(code));
    if (targetLanguages.length === 0) return;
    const seq = ++requestSeqRef.current;
    setTranslating(true);
    // Only disable the fields being overwritten - never the field the user is
    // typing in (that's `sourceLang`), or a disabled input drops keystrokes
    // that land while the request is in flight.
    setTranslatingTargets(new Set(targetLanguages));
    try {
      const result = await translationService.translateText(sourceText, sourceLang, targetLanguages);
      if (seq !== requestSeqRef.current) return; // superseded by a later edit
      if (result.translations && !result.error) {
        Object.entries(result.translations).forEach(([lang, translation]) => {
          if (translation && !isProtected(lang)) onChange(lang, translation);
        });
      }
    } catch (error) {
      console.error('Auto-translation failed:', error);
    } finally {
      if (seq === requestSeqRef.current) {
        setTranslating(false);
        setTranslatingTargets(new Set());
      }
    }
  };

  const handleRetranslate = async (targetLang) => {
    const sourceText = values[primaryLang];
    if (!sourceText || !sourceText.trim()) return;
    setTranslating(true);
    setTranslatingTargets(new Set([targetLang]));
    try {
      const result = await translationService.translateText(sourceText, primaryLang, [targetLang]);
      if (result.translations && result.translations[targetLang]) {
        onChange(targetLang, result.translations[targetLang]);
        setManuallyEdited(prev => ({ ...prev, [targetLang]: false }));
      }
    } catch (error) {
      console.error('Re-translation failed:', error);
    } finally {
      setTranslating(false);
      setTranslatingTargets(new Set());
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
            {t('Translating...')}
          </span>
        )}
      </label>

      <div className="flex gap-4 flex-wrap">
        {languages.map((language, index) => {
          const value = values[language.code] || '';
          // Only flag an empty required field once the user has interacted with
          // it or tried to save - a brand new question shouldn't render red.
          const hasError = required && !value && (showErrors || touched[language.code]);
          const isFirstLanguage = index === 0;
          const isTranslatingThisField = translatingTargets.has(language.code);
          const showRetranslateButton = autoTranslateEnabled && !isFirstLanguage &&
            !!values[primaryLang];

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
                  onBlur={() => setTouched(prev => ({ ...prev, [language.code]: true }))}
                  placeholder={placeholder}
                  disabled={disabled || isTranslatingThisField}
                  rows={3}
                />
              ) : (
                <input
                  type="text"
                  className={inputCls(hasError)}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  onBlur={() => setTouched(prev => ({ ...prev, [language.code]: true }))}
                  placeholder={placeholder}
                  disabled={disabled || isTranslatingThisField}
                />
              )}
              {hasError && (
                <span className="text-error text-xs">{t('Required in all languages')}</span>
              )}
              {showRetranslateButton && (
                <button
                  type="button"
                  onClick={() => handleRetranslate(language.code)}
                  disabled={translating}
                  title={t('Re-translate from {{language}}', { language: languages[0].description })}
                  className="inline-flex items-center gap-1 mt-0.5 px-2 py-1 text-xs text-action border border-action rounded hover:bg-action hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-fit"
                >
                  <i className="fas fa-sync-alt text-[10px]"></i> {t('Re-translate')}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default TranslatableFieldGroup;
