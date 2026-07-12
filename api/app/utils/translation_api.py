import flask_restful as restful
from flask import request
from app.utils.translation import TranslationService
from app.utils.auth import auth_required
from app import LOGGER


class TranslationAPI(restful.Resource):
    """API endpoint for translating text"""
    
    @auth_required
    def post(self):
        """
        Translate text to one or more target languages.
        
        Request body:
        {
            "text": "Text to translate",
            "source_language": "en",
            "target_languages": ["fr", "es"]
        }
        
        Response:
        {
            "translations": {
                "fr": "Texte traduit",
                "es": "Texto traducido"
            }
        }
        """
        try:
            args = request.get_json()
            
            text = args.get('text', '').strip()
            source_language = args.get('source_language', 'en')
            target_languages = args.get('target_languages', [])
            
            if not text:
                return {'translations': {lang: '' for lang in target_languages}}, 200
            
            if not target_languages:
                return {'error': 'target_languages is required'}, 400
            
            translations = TranslationService.translate_batch(
                text,
                target_languages,
                source_language
            )
            
            if translations is None:
                return {'error': 'Translation service unavailable'}, 503
            
            # Filter out None values (failed translations)
            failed = [lang for lang, trans in translations.items() if trans is None]
            if failed:
                LOGGER.warning(f"Failed to translate to: {failed}")
            
            return {'translations': translations}, 200
            
        except Exception as e:
            LOGGER.error(f"Error in translation API: {str(e)}")
            return {'error': 'Internal server error'}, 500
