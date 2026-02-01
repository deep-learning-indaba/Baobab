import axios from 'axios';
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const translationService = {
    translateText
};

/**
 * Translate text to multiple target languages
 * @param {string} text - Text to translate
 * @param {string} sourceLanguage - Source language code (e.g., 'en')
 * @param {string[]} targetLanguages - Array of target language codes (e.g., ['fr', 'es'])
 * @returns {Promise<{translations: Object, error: string}>}
 */
function translateText(text, sourceLanguage, targetLanguages) {
    return axios.post(
        `${baseUrl}/api/v1/translate`,
        {
            text,
            source_language: sourceLanguage,
            target_languages: targetLanguages
        },
        {
            headers: authHeader()
        }
    )
    .then(function(response) {
        return {
            translations: response.data.translations,
            error: ""
        };
    })
    .catch(function(error) {
        console.error('Translation error:', error);
        return {
            translations: null,
            error: error.response && error.response.data && error.response.data.error 
                ? error.response.data.error 
                : 'Translation failed'
        };
    });
}
