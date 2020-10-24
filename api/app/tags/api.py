from flask import g
import flask_restful as restful
from flask_restful import reqparse, fields, marshal_with
from app.utils.auth import auth_required, event_admin_required
from app.tags.repository import TagRepository as tag_repository
from app.utils import errors

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


class TagAPI(restful.Resource):

    @event_admin_required
    def get(self, event_id):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        args = req_parser.parse_args()
        id = args['id']

        tag = tag_repository.get_by_id(id)
        if tag.event_id != event_id:
            return errors.UNAUTHORIZED

        return _serialize_tag_detail(tag)

    