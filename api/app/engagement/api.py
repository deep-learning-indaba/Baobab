from flask import g, request
import flask_restful as restful

from app.utils.auth import auth_required
from app.utils import errors
from app.events.repository import EventRepository as event_repository
from app.engagement.repository import EngagementRepository


class EngagementInstallAPI(restful.Resource):
    """POST /api/v1/engagement/install — record that the current user installed
    the event app (PWA) while browsing a given event."""

    @auth_required
    def post(self):
        body = request.get_json()
        if not body or not body.get('event_id'):
            return errors.MISSING_FIELDS

        event = event_repository.get_by_id(body.get('event_id'))
        if not event:
            return errors.EVENT_NOT_FOUND

        EngagementRepository.record(event, g.current_user['id'], 'app_installed')
        return {}, 201
