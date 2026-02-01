from google.cloud import translate_v2 as translate
from app import LOGGER
import os


class TranslationService:
    """Service for translating text using Google Translate API"""
    
    _client = None
    
    @classmethod
    def _get_client(cls):
        """Get or create the translation client"""
        if cls._client is None:
            try:
                # Initialize the client with API key
                # For google-cloud-translate v2, we need to set the API key as an environment variable
                api_key = os.getenv('GCP_API_KEY')
                if not api_key:
                    LOGGER.error("GCP_API_KEY not found in environment variables")
                    return None
                
                # Set the API key in the environment for the client to use
                os.environ['GOOGLE_API_KEY'] = api_key
                cls._client = translate.Client()
            except Exception as e:
                LOGGER.error(f"Failed to initialize Google Translate client: {str(e)}")
                return None
        return cls._client
    
    @classmethod
    def translate_text(cls, text, target_language, source_language='en'):
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'fr', 'es')
            source_language: Source language code (default: 'en')
        
        Returns:
            dict: {'translated_text': str, 'detected_source_language': str} or None on error
        """
        if not text or not text.strip():
            return {'translated_text': '', 'detected_source_language': source_language}
        
        client = cls._get_client()
        if not client:
            return None
        
        try:
            result = client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            
            return {
                'translated_text': result['translatedText'],
                'detected_source_language': result.get('detectedSourceLanguage', source_language)
            }
        except Exception as e:
            LOGGER.error(f"Translation error: {str(e)}")
            return None
    
    @classmethod
    def translate_batch(cls, texts, target_languages, source_language='en'):
        """
        Translate a single text to multiple target languages.
        
        Args:
            texts: Single text string or list of texts to translate
            target_languages: List of target language codes
            source_language: Source language code (default: 'en')
        
        Returns:
            dict: {language_code: translated_text} or None on error
        """
        if not texts or (isinstance(texts, str) and not texts.strip()):
            return {lang: '' for lang in target_languages}
        
        client = cls._get_client()
        if not client:
            return None
        
        # Handle single text
        single_text = texts if isinstance(texts, str) else texts[0] if texts else ''
        
        translations = {}
        for target_lang in target_languages:
            if target_lang == source_language:
                translations[target_lang] = single_text
                continue
            
            try:
                result = client.translate(
                    single_text,
                    target_language=target_lang,
                    source_language=source_language
                )
                translations[target_lang] = result['translatedText']
            except Exception as e:
                LOGGER.error(f"Translation error for {target_lang}: {str(e)}")
                translations[target_lang] = None
        
        return translations
