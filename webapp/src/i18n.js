import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';


function i18nInit(organisation) {
  const orgLanguageDetector = {
    name: 'orgLanguageDetector',
  
    lookup(options) {
      let found = [];
  
      if (typeof navigator !== 'undefined') {
        if (navigator.languages) { // chrome only; not an array, so can't use .push.apply instead of iterating
          for (let i=0; i < navigator.languages.length; i++) {
            found.push(navigator.languages[i]);
          }
        }
        if (navigator.userLanguage) {
          found.push(navigator.userLanguage);
        }
        if (navigator.language) {
          found.push(navigator.language);
        }
      }
  
      if (found.length == 0) {
        return undefined;
      }
  
      found = found.map(lang => lang.slice(0, 2));
      const orgLanguageCodes = organisation.languages.map(l => l.code);
      let selectedLanguage = null;
      found.forEach(f => {
        if (selectedLanguage == null && orgLanguageCodes.includes(f)) {
          selectedLanguage = f; 
        }
      })

      return selectedLanguage || undefined;
    }
  };
  
  const languageDetectorOptions = {
    // order and from where user language should be detected
    order: ['querystring', 'localStorage', 'cookie', 'sessionStorage', 'orgLanguageDetector']
  };
  
  const languageDetector = new LanguageDetector(null, languageDetectorOptions);
  languageDetector.addDetector(orgLanguageDetector);

  i18n
  .use(Backend)
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: true,
    interpolation: {
      escapeValue: false, // not needed for react as it escapes by default
    },
    keySeparator: false
  });

  return i18n;
}

export default i18nInit;