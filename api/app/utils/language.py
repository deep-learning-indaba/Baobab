"""Language utilities."""

from functools import wraps
from flask_restful import reqparse

def translatable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=False)
        req_args = req_parser.parse_args()

        language = req_args['language'] or 'en'

        return func(*args, language=language, **kwargs)

    return wrapper

_TRANSLATION_COLLECTIONS = ('translations', 'question_translations', 'section_translations', 'event_translations')


def _all_translations(entity):
    for attr in _TRANSLATION_COLLECTIONS:
        collection = getattr(entity, attr, None)
        if collection is not None:
            return sorted(collection, key=lambda t: t.id or 0)
    return []


def translation_for(entity, *languages):
    """The entity's translation in the first of `languages` it has, falling back to
    whichever translation exists. Content is only authored in its event's languages,
    which need not include English, so no single language is guaranteed to exist."""
    for language in languages:
        if language:
            translation = entity.get_translation(language)
            if translation is not None:
                return translation
    translations = _all_translations(entity)
    return translations[0] if translations else None


def user_language_for_event(user, event):
    """The language to address `user` in about `event`: their preference when the
    event supports it, otherwise the event's primary language."""
    preferred = user.user_primaryLanguage if user is not None else None
    if event is None:
        return (preferred or 'en')[:2]
    return event.resolve_language(preferred)
