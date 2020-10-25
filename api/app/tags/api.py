from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from app.utils.auth import auth_required, event_admin_required
from app.tags.repository import TagRepository as tag_repository
from app.utils import errors
from app.tags.models import Tag, TagTranslation
from app import LOGGER

def _serialize_tag_detail(tag):
    """Serializes a tag with all of its translations."""
    result = {
        'id': tag.id,
        'event_id': tag.event_id,
        'name': {
            t.language: t.name for t in tag.translations
        }
    }
    return result


def _serialize_tag(tag, language):
    """Serialize a tag in a specific language."""
    translation = tag.get_translation(language)
    if translation is None:
        LOGGER.warn('Could not find translation for language {} for tag id {}'.format(language, tag.id))
        translation = tag.get_translation('en')
    return {
        'id': tag.id,
        'event_id': tag.event_id,
        'name': translation.name
    }

class TagAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        args = req_parser.parse_args()
        id = args['id']

        tag = tag_repository.get_by_id(id)
        if tag.event_id != event_id:
            return errors.FORBIDDEN

        return _serialize_tag_detail(tag)

    @event_admin_required
    def post(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('name', type=dict, required=True)
        args = req_parser.parse_args()
        name_translations = args['name']

        tag = Tag(event_id)
        for language, name in name_translations.iteritems():
            tag.translations.append(TagTranslation(tag.id, language, name))
        tag_repository.add_tag(tag)

        return _serialize_tag_detail(tag), 201

    @event_admin_required
    def put(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        req_parser.add_argument('name', type=dict, required=True)
        args = req_parser.parse_args()
        id = args['id']
        name_translations = args['name']

        tag = tag_repository.get_by_id(id)
        if not tag or tag.event_id != event_id:
            return errors.TAG_NOT_FOUND

        for language, name in name_translations.iteritems():
            translation = tag.get_translation(language)
            if translation:
                translation.name = name
            else:
                tag.translations.append(TagTranslation(tag.id, language, name))

        for translation in tag.translations:
            if translation.language not in name_translations:
                tag_repository.delete_translation(translation.id)

        tag_repository.commit()

        return _serialize_tag_detail(tag), 200


class TagListAPI(restful.Resource):
    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('language', type=str, required=True)
        args = req_parser.parse_args()
        language = args['language']

        tags = tag_repository.get_all_for_event(event_id)
        return [_serialize_tag(t, language) for t in tags]
