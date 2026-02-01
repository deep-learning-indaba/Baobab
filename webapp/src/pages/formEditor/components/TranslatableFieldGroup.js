import React, { useState, useRef, useEffect } from 'react';
import { translationService } from '../../../services/translation';
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
  disabled = false,
  autoTranslateEnabled = true
}) => {
  const [translating, setTranslating] = useState(false);
  const [manuallyEdited, setManuallyEdited] = useState({});
  const typingTimerRef = useRef({});
  const TYPING_DELAY = 1000;

  const handleChange = (langCode, value) => {
    onChange(langCode, value);
    
    // Mark as manually edited
    setManuallyEdited(prev => ({ ...prev, [langCode]: true }));
    
    // Clear existing timer for this language
    if (typingTimerRef.current[langCode]) {
      clearTimeout(typingTimerRef.current[langCode]);
    }
    
    // Auto-translate after user stops typing
    if (autoTranslateEnabled && value && value.trim()) {
      typingTimerRef.current[langCode] = setTimeout(() => {
        handleAutoTranslate(langCode, value);
      }, TYPING_DELAY);
    }
  };

  const handleAutoTranslate = async (sourceLang, sourceText) => {
    if (!sourceText || !sourceText.trim()) return;
    
    const targetLanguages = languages
      .map(lang => lang.code)
      .filter(code => code !== sourceLang && !values[code] && !manuallyEdited[code]);
    
    if (targetLanguages.length === 0) return;
    
    setTranslating(true);
    try {
      const result = await translationService.translateText(
        sourceText,
        sourceLang,
        targetLanguages
      );
      
      if (result.translations && !result.error) {
        Object.entries(result.translations).forEach(([lang, translation]) => {
          if (translation && !manuallyEdited[lang]) {
            onChange(lang, translation);
          }
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
      const result = await translationService.translateText(
        sourceText,
        sourceLang,
        [targetLang]
      );
      
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
    return () => {
      Object.values(typingTimerRef.current).forEach(timer => clearTimeout(timer));
    };
  }, []);

  return (
    <div className="translatable-field-group">
      <label className="translatable-field-label">
        {label}
        {required && <span className="required-indicator">*</span>}
        {translating && <span className="translating-indicator"><i className="fas fa-spinner fa-spin"></i> Translating...</span>}
      </label>
      <div className="translatable-inputs-container">
        {languages.map((language, index) => {
          const value = values[language.code] || '';
          const hasError = required && !value;
          const isFirstLanguage = index === 0;
          const showRetranslateButton = autoTranslateEnabled && !isFirstLanguage && manuallyEdited[language.code] && values[languages[0].code];
          
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
                  disabled={disabled || translating}
                  rows={3}
                />
              ) : (
                <input
                  type="text"
                  className={`translatable-input ${hasError ? 'has-error' : ''}`}
                  value={value}
                  onChange={(e) => handleChange(language.code, e.target.value)}
                  placeholder={placeholder}
                  disabled={disabled || translating}
                />
              )}
              {hasError && (
                <span className="field-error">Required in all languages</span>
              )}
              {showRetranslateButton && (
                <button
                  type="button"
                  className="retranslate-btn"
                  onClick={() => handleRetranslate(language.code)}
                  disabled={translating}
                  title="Re-translate from first language"
                >
                  <i className="fas fa-sync-alt"></i> Re-translate
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
